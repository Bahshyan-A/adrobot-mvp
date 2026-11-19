import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.errors import ApplicationError
from backend.integrations.keitaro import KeitaroClient
from backend.integrations.transport import JsonObject
from backend.models import Campaign
from backend.schemas import CreateCampaign
from backend.services.audit import record_event
from backend.services.synchronization import fetch_campaign


def list_campaigns(session: Session, client: KeitaroClient, query: str = "") -> list[JsonObject]:
    statement = select(Campaign)
    local_campaigns = {campaign.remote_id: campaign for campaign in session.scalars(statement)}
    result = []

    for remote in client.list_campaigns():
        if query.casefold() not in remote["name"].casefold() and query not in str(remote["id"]):
            continue
        local = local_campaigns.get(remote["id"])
        result.append(
            {
                **remote,
                "local_id": local.id if local else None,
                "dirty_count": sum(stream.is_dirty for stream in local.streams) if local else 0,
            }
        )

    session.commit()
    return result


def validate_references(client: KeitaroClient, body: CreateCampaign) -> None:
    references = {
        "domains": body.domain_id,
        "groups": body.group_id,
        "traffic_sources": body.traffic_source_id,
        "offers": body.offer_id,
    }
    for entity, selected_id in references.items():
        available = any(
            item["id"] == selected_id and item.get("state", "active") == "active"
            for item in client.list_entities(entity)
        )
        if not available:
            raise ApplicationError(
                422,
                f"Выбранный объект ({entity}, #{selected_id}) недоступен. Обновите список.",
            )


def create_campaign(session: Session, client: KeitaroClient, body: CreateCampaign) -> JsonObject:
    validate_references(client, body)
    campaign = client.create_campaign(
        {
            "name": body.name,
            "alias": secrets.token_urlsafe(6),
            "type": "position",
            "state": "disabled",
            "domain_id": body.domain_id,
            "group_id": str(body.group_id),
            "traffic_source_id": body.traffic_source_id,
            "cost_type": "CPC",
            "cost_value": 0,
            "cost_currency": "USD",
            "cost_auto": True,
        }
    )
    campaign_id = campaign["id"]

    try:
        create_campaign_streams(client, campaign_id, body)
        client.activate_campaign(campaign_id)
    except ApplicationError:
        # A partially configured campaign must never route live traffic.
        try:
            client.archive_campaign(campaign_id)
        except ApplicationError as cleanup_error:
            raise ApplicationError(
                502,
                f"Создание не завершено. В Keitaro могла остаться кампания #{campaign_id}; проверьте её вручную.",
            ) from cleanup_error
        raise

    record_event(session, campaign_id, "create", geo=body.geo, offer_id=body.offer_id)
    try:
        return fetch_campaign(session, client, campaign_id)
    except ApplicationError as error:
        raise ApplicationError(
            error.status_code,
            f"Кампания #{campaign_id} создана, но не удалось загрузить её конфигурацию. Обновите список кампаний перед повторным созданием.",
        ) from error


def create_campaign_streams(client: KeitaroClient, campaign_id: int, body: CreateCampaign) -> None:
    client.create_stream(
        {
            "campaign_id": campaign_id,
            "name": "Геофильтр · Google",
            "type": "regular",
            "schema": "redirect",
            "action_type": "http",
            "action_payload": "https://google.com",
            "position": 1,
            "state": "active",
            "collect_clicks": True,
            "filters": [{"name": "country", "mode": "accept", "payload": body.geo}],
        }
    )
    client.create_stream(
        {
            "campaign_id": campaign_id,
            "name": "Основной поток",
            "type": "default",
            "schema": "landings",
            "action_type": "http",
            "position": 2,
            "state": "active",
            "collect_clicks": True,
            "filters": [],
            "landings": [],
            "offers": [{"offer_id": body.offer_id, "share": 100, "state": "active"}],
        }
    )
