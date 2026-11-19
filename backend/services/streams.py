"""Local draft editing and explicit publication of stream offers."""

from copy import deepcopy

from sqlalchemy.orm import Session

from backend.domain.offers import (
    OfferSnapshot,
    active_bindings,
    normalized_bindings,
    redistribute_weights,
)
from backend.errors import ApplicationError
from backend.integrations.keitaro import KeitaroClient
from backend.integrations.transport import JsonObject
from backend.models import Stream
from backend.schemas import EditOffer
from backend.services.audit import record_event
from backend.services.serialization import stream_response


def get_stream(session: Session, stream_id: int, expected_revision: int) -> Stream:
    stream = session.get(Stream, stream_id)
    if stream is None:
        raise ApplicationError(404, "Поток не найден. Загрузите кампанию из Keitaro.")
    if stream.revision != expected_revision:
        raise ApplicationError(409, "Поток изменён в другой вкладке. Перезагрузите страницу.")
    return stream


def require_available_offer(client: KeitaroClient, offer_id: int) -> JsonObject:
    offer = client.get_offer(offer_id)
    if offer.get("state") != "active":
        raise ApplicationError(422, "Оффер удалён или отключён в Keitaro.")
    return offer


def add_offer(client: KeitaroClient, draft: list[OfferSnapshot], offer_id: int) -> None:
    if any(offer["offer_id"] == offer_id for offer in draft):
        raise ApplicationError(
            409, "Оффер уже есть в потоке. Для архивного оффера нажмите «Вернуть»."
        )
    remote = require_available_offer(client, offer_id)
    draft.append(
        {
            "offer_id": offer_id,
            "name": remote["name"],
            "share": 0,
            "state": "active",
            "pinned": False,
            "removed": False,
            "new": True,
            "removed_reason": None,
        }
    )


def update_offer(client: KeitaroClient, offer: OfferSnapshot, body: EditOffer) -> None:
    match body.action:
        case "remove":
            offer.update(removed=True, pinned=False, removed_reason="local")
        case "restore":
            require_available_offer(client, body.offer_id)
            offer.update(removed=False, state="active", removed_reason=None)
        case "pin":
            if offer["removed"]:
                raise ApplicationError(422, "Нельзя закрепить долю архивного оффера.")
            offer["share"] = body.share if body.share is not None else offer["share"]
            offer["pinned"] = True
        case "unpin":
            offer["pinned"] = False


def edit_offer(
    session: Session, client: KeitaroClient, stream_id: int, body: EditOffer
) -> JsonObject:
    stream = get_stream(session, stream_id, body.revision)
    if stream.is_missing:
        raise ApplicationError(
            409, "Поток удалён в Keitaro. Восстановите его и выполните Fetch streams."
        )
    if not stream.is_editable:
        raise ApplicationError(422, "Этот поток не содержит офферов.")

    draft = deepcopy(stream.draft)
    if body.action == "add":
        add_offer(client, draft, body.offer_id)
    else:
        offer = next((item for item in draft if item["offer_id"] == body.offer_id), None)
        if offer is None:
            raise ApplicationError(404, "Оффер не найден в потоке.")
        update_offer(client, offer, body)

    stream.draft = redistribute_weights(draft)
    record_event(
        session,
        stream.campaign.remote_id,
        body.action,
        stream.remote_id,
        offer_id=body.offer_id,
        share=body.share,
    )
    session.commit()
    return stream_response(stream)


def cancel_draft(session: Session, stream_id: int, revision: int) -> JsonObject:
    stream = get_stream(session, stream_id, revision)
    stream.draft = deepcopy(stream.published)
    record_event(session, stream.campaign.remote_id, "cancel", stream.remote_id)
    session.commit()
    return stream_response(stream)


def publish_draft(
    session: Session, client: KeitaroClient, stream_id: int, revision: int
) -> JsonObject:
    stream = get_stream(session, stream_id, revision)
    if stream.is_missing:
        raise ApplicationError(409, "Поток отсутствует в Keitaro. Выполните Fetch streams.")

    desired_offers = active_bindings(stream.draft)
    if desired_offers and sum(offer["share"] for offer in desired_offers) != 100:
        raise ApplicationError(422, "Сумма долей должна быть равна 100%.")

    remote = client.get_stream(stream.remote_id)
    actual_bindings = normalized_bindings(remote.get("offers", []))
    desired_bindings = normalized_bindings(desired_offers)
    published_bindings = normalized_bindings(active_bindings(stream.published))

    # A previous timed-out PUT may already have applied this exact configuration.
    already_applied = actual_bindings == desired_bindings
    if not already_applied and actual_bindings != published_bindings:
        raise ApplicationError(
            409,
            "Офферы изменены в Keitaro. Выполните Fetch streams для сверки; ваш черновик сохранён.",
        )

    if desired_offers:
        available_offer_ids = {
            offer["id"]
            for offer in client.list_entities("offers")
            if offer.get("state") == "active"
        }
        if any(offer["offer_id"] not in available_offer_ids for offer in desired_offers):
            raise ApplicationError(422, "Один из офферов удалён или отключён в Keitaro.")

    if not already_applied:
        client.update_stream_offers(stream.remote_id, desired_offers)

    confirmed = client.get_stream(stream.remote_id)
    if normalized_bindings(confirmed.get("offers", [])) != desired_bindings:
        raise ApplicationError(502, "Keitaro не подтвердил новые доли. Черновик сохранён.")

    stream.data = confirmed
    stream.draft = [{**offer, "new": False} for offer in stream.draft]
    stream.published = deepcopy(stream.draft)
    record_event(
        session, stream.campaign.remote_id, "push", stream.remote_id, offers=desired_offers
    )
    session.commit()
    return stream_response(stream)
