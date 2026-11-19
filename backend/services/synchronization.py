"""Fetch remote configuration without silently overwriting local drafts."""

from copy import deepcopy
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.domain.offers import OfferSnapshot, active_bindings, normalized_bindings
from backend.errors import ApplicationError
from backend.integrations.keitaro import KeitaroClient
from backend.integrations.transport import JsonObject
from backend.models import Campaign, Stream
from backend.services.audit import record_event
from backend.services.serialization import campaign_response


def find_campaign(session: Session, remote_id: int) -> Campaign | None:
    return session.scalar(
        select(Campaign).where(
            Campaign.remote_id == remote_id,
        )
    )


def validate_remote_configuration(campaign: JsonObject, streams: list[JsonObject]) -> None:
    if not isinstance(campaign.get("name"), str):
        raise ApplicationError(
            502, "Keitaro вернул кампанию без названия. Локальные данные сохранены."
        )

    for stream in streams:
        valid_stream = (
            isinstance(stream, dict)
            and isinstance(stream.get("id"), int)
            and isinstance(stream.get("name"), str)
            and isinstance(stream.get("offers", []), list)
        )
        if not valid_stream:
            raise ApplicationError(
                502, "Keitaro вернул некорректный поток. Локальные данные сохранены."
            )

        seen_offer_ids = set()
        for offer in stream.get("offers", []):
            valid_offer = (
                isinstance(offer, dict)
                and isinstance(offer.get("offer_id"), int)
                and isinstance(offer.get("share"), int)
                and 0 <= offer["share"] <= 100
                and offer["offer_id"] not in seen_offer_ids
            )
            if not valid_offer:
                raise ApplicationError(
                    502,
                    "Keitaro вернул некорректный состав офферов. Локальные данные сохранены.",
                )
            seen_offer_ids.add(offer["offer_id"])


def describe_changes(campaign: Campaign, remote_streams: dict[int, JsonObject]) -> list[str]:
    changes = []
    for stream in campaign.streams:
        actual = remote_streams.get(stream.remote_id)
        prefix = f"Поток #{stream.remote_id}"
        if actual is None:
            if not stream.is_missing:
                changes.append(f"{prefix} отсутствует в Keitaro.")
            continue

        before = {offer["offer_id"]: offer for offer in active_bindings(stream.published)}
        after = {offer["offer_id"]: offer for offer in actual.get("offers", [])}

        for offer_id in sorted(before.keys() - after.keys()):
            changes.append(f"{prefix}: оффер #{offer_id} удалён в Keitaro.")
        for offer_id in sorted(after.keys() - before.keys()):
            changes.append(f"{prefix}: добавлен оффер #{offer_id}.")
        for offer_id in sorted(before.keys() & after.keys()):
            if normalized_bindings([before[offer_id]]) != normalized_bindings([after[offer_id]]):
                changes.append(f"{prefix}: доля или статус оффера #{offer_id} изменены в Keitaro.")

    return changes


def protect_drafts(
    session: Session,
    campaign: Campaign,
    changes: list[str],
    discard_drafts: bool,
    revisions: dict[int, int],
) -> None:
    dirty_streams = [stream for stream in campaign.streams if stream.is_dirty]
    if not dirty_streams:
        return

    if not discard_drafts:
        raise ApplicationError(
            409,
            {
                "message": "Есть неопубликованные изменения. Выберите дальнейшее действие.",
                "sync_conflict": True,
                "changes": changes,
                "revisions": {stream.id: stream.revision for stream in dirty_streams},
            },
        )

    if any(revisions.get(stream.id) != stream.revision for stream in dirty_streams):
        raise ApplicationError(409, "Черновик изменился в другой вкладке. Повторите Fetch streams.")

    for stream in dirty_streams:
        record_event(
            session, campaign.remote_id, "cancel", stream.remote_id, reason="fetch_discard"
        )


def merge_offer_snapshots(
    published: list[OfferSnapshot],
    remote_stream: JsonObject,
    offer_catalog: dict[int, JsonObject],
) -> list[OfferSnapshot]:
    previous_offers = {offer["offer_id"]: offer for offer in published}
    merged: list[OfferSnapshot] = []

    for binding in remote_stream.get("offers", []):
        if binding.get("state") == "deleted":
            continue

        offer_id = binding["offer_id"]
        previous = previous_offers.pop(offer_id, None)
        fallback_name = previous["name"] if previous else f"Оффер #{offer_id}"
        merged.append(
            {
                "offer_id": offer_id,
                "name": offer_catalog.get(offer_id, {}).get("name", fallback_name),
                "share": binding["share"],
                "state": binding.get("state", "active"),
                "pinned": previous["pinned"] if previous else False,
                "removed": False,
                "new": False,
                "removed_reason": None,
            }
        )

    for previous in previous_offers.values():
        archived = deepcopy(previous)
        archived.update(share=0, removed=True, pinned=False, new=False)
        if not previous["removed"]:
            archived["removed_reason"] = "source"
        merged.append(archived)

    return merged


def fetch_campaign(
    session: Session,
    client: KeitaroClient,
    remote_id: int,
    discard_drafts: bool = False,
    revisions: dict[int, int] | None = None,
) -> JsonObject:
    campaign = find_campaign(session, remote_id)
    remote_campaign = client.get_campaign(remote_id)
    streams = client.get_streams(remote_id)
    validate_remote_configuration(remote_campaign, streams)
    remote_streams = {
        stream["id"]: stream for stream in streams if stream.get("state") != "deleted"
    }

    changes = describe_changes(campaign, remote_streams) if campaign else []
    if campaign:
        protect_drafts(session, campaign, changes, discard_drafts, revisions or {})

    offer_catalog = {offer["id"]: offer for offer in client.list_entities("offers")}
    if campaign is None:
        campaign = Campaign(
            remote_id=remote_id,
            name=remote_campaign["name"],
            data=remote_campaign,
        )
        session.add(campaign)
        session.flush()

    campaign.name = remote_campaign["name"]
    campaign.data = remote_campaign
    campaign.synced_at = datetime.now(UTC)
    existing_streams = {stream.remote_id: stream for stream in campaign.streams}

    for remote_stream in remote_streams.values():
        stream = existing_streams.get(remote_stream["id"])
        if stream is None:
            stream = Stream(
                campaign=campaign,
                remote_id=remote_stream["id"],
                data=remote_stream,
                published=[],
                draft=[],
            )
            session.add(stream)

        merged = merge_offer_snapshots(stream.published, remote_stream, offer_catalog)
        stream.data = remote_stream
        stream.published = deepcopy(merged)
        stream.draft = deepcopy(merged)

    for remote_stream_id, stream in existing_streams.items():
        if remote_stream_id not in remote_streams:
            stream.data = {**stream.data, "_missing": True}
            stream.published = merge_offer_snapshots(
                stream.published, {"offers": []}, offer_catalog
            )
            stream.draft = deepcopy(stream.published)

    record_event(session, remote_id, "fetch", changes=changes)
    session.commit()
    session.refresh(campaign)
    return {**campaign_response(campaign), "sync_changes": changes}
