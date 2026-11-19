"""A test-only Keitaro transport. Production always uses HttpTransport."""

from copy import deepcopy

from backend.errors import ApplicationError
from backend.integrations.transport import ApiResponse, JsonObject
from tests.fixtures.keitaro_data import tracker_data


class TrackerStub:
    def __init__(self) -> None:
        self.data = tracker_data()

    def request(
        self,
        method: str,
        path: str,
        payload: JsonObject | None = None,
        params: JsonObject | None = None,
    ) -> ApiResponse:
        data = deepcopy(self.data)
        parts = path.strip("/").split("/")
        collection = parts[0]
        items = data.get(collection, [])
        result = None

        if method == "GET":
            if len(parts) == 1:
                result = items
                if collection == "campaigns" and params:
                    offset = params.get("offset", 0)
                    result = items[offset : offset + params.get("limit", 500)]
            elif len(parts) == 3 and parts[2] == "streams":
                result = [
                    stream for stream in data["streams"] if stream["campaign_id"] == int(parts[1])
                ]
            else:
                result = next((item for item in items if item["id"] == int(parts[1])), None)
        elif method == "POST" and len(parts) == 1:
            result = {**(payload or {}), "id": max((item["id"] for item in items), default=0) + 1}
            items.append(result)
        elif method == "PUT":
            result = next((item for item in items if item["id"] == int(parts[1])), None)
            if result is not None:
                result.update(payload or {})
        elif method == "DELETE":
            result = {}
            data[collection] = [item for item in items if item["id"] != int(parts[1])]
            if collection == "campaigns":
                data["streams"] = [
                    stream for stream in data["streams"] if stream["campaign_id"] != int(parts[1])
                ]

        if result is None:
            raise ApplicationError(404, "Test tracker entity not found")
        if method != "GET":
            self.data = data
        return deepcopy(result)
