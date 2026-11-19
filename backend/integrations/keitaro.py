"""Keitaro Admin API operations used by the application."""

from backend.domain.offers import OfferBinding
from backend.errors import ApplicationError
from backend.integrations.transport import ApiTransport, JsonObject


class KeitaroClient:
    def __init__(self, transport: ApiTransport) -> None:
        self.transport = transport

    def list_entities(self, entity: str) -> list[JsonObject]:
        params = {"type": "campaigns"} if entity == "groups" else None
        result = self.transport.request("GET", f"/{entity}", params=params)
        if not isinstance(result, list) or any(not isinstance(item, dict) for item in result):
            raise ApplicationError(502, "Keitaro вернул некорректный список объектов.")
        return [item for item in result if item.get("state") != "deleted"]

    def list_campaigns(self) -> list[JsonObject]:
        campaigns = []
        offset = 0
        page_size = 500
        while True:
            page = self.transport.request(
                "GET", "/campaigns", params={"offset": offset, "limit": page_size}
            )
            if not isinstance(page, list):
                raise ApplicationError(502, "Keitaro вернул некорректный список кампаний.")
            campaigns.extend(item for item in page if item.get("state") != "deleted")
            if len(page) < page_size:
                return campaigns
            offset += page_size

    def get_campaign(self, campaign_id: int) -> JsonObject:
        return self._get_object(f"/campaigns/{campaign_id}")

    def get_stream(self, stream_id: int) -> JsonObject:
        return self._get_object(f"/streams/{stream_id}")

    def get_offer(self, offer_id: int) -> JsonObject:
        return self._get_object(f"/offers/{offer_id}")

    def get_streams(self, campaign_id: int) -> list[JsonObject]:
        result = self.transport.request("GET", f"/campaigns/{campaign_id}/streams")
        if not isinstance(result, list):
            raise ApplicationError(502, "Keitaro вернул некорректный список потоков.")
        return result

    def create_campaign(self, payload: JsonObject) -> JsonObject:
        return self._write_object("POST", "/campaigns", payload)

    def create_stream(self, payload: JsonObject) -> JsonObject:
        return self._write_object("POST", "/streams", payload)

    def activate_campaign(self, campaign_id: int) -> None:
        self.transport.request("PUT", f"/campaigns/{campaign_id}", {"state": "active"})

    def archive_campaign(self, campaign_id: int) -> None:
        self.transport.request("DELETE", f"/campaigns/{campaign_id}")

    def update_stream_offers(self, stream_id: int, offers: list[OfferBinding]) -> None:
        # Updating only this field preserves filters, landings, and redirect settings.
        self.transport.request("PUT", f"/streams/{stream_id}", {"offers": offers})

    def _get_object(self, path: str) -> JsonObject:
        result = self.transport.request("GET", path)
        if not isinstance(result, dict):
            raise ApplicationError(502, "Keitaro вернул некорректный объект.")
        return result

    def _write_object(self, method: str, path: str, payload: JsonObject) -> JsonObject:
        result = self.transport.request(method, path, payload)
        if not isinstance(result, dict) or not isinstance(result.get("id"), int):
            raise ApplicationError(502, "Keitaro не подтвердил создание объекта.")
        return result
