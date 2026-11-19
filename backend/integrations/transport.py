"""HTTP transport. Credentials and upstream response bodies never reach the UI."""

from typing import Any, Protocol
from urllib.parse import urlparse

import httpx

from backend.config import Settings
from backend.errors import ApplicationError

JsonObject = dict[str, Any]
ApiResponse = JsonObject | list[JsonObject]


class ApiTransport(Protocol):
    def request(
        self,
        method: str,
        path: str,
        payload: JsonObject | None = None,
        params: JsonObject | None = None,
    ) -> ApiResponse: ...


class HttpTransport:
    def __init__(self, config: Settings, client: httpx.Client) -> None:
        self.config = config
        self.client = client

    def request(
        self,
        method: str,
        path: str,
        payload: JsonObject | None = None,
        params: JsonObject | None = None,
    ) -> ApiResponse:
        if not self.config.keitaro_api_key:
            raise ApplicationError(503, "В .env не задан KEITARO_API_KEY.")

        address = urlparse(self.config.keitaro_url)
        if address.scheme not in ("http", "https") or not address.netloc:
            raise ApplicationError(503, "Некорректный KEITARO_URL.")

        url = self.config.keitaro_url.rstrip("/") + "/admin_api/v1" + path
        try:
            response = self.client.request(
                method,
                url,
                headers={"Api-Key": self.config.keitaro_api_key},
                json=payload,
                params=params,
            )
        except httpx.TimeoutException as error:
            raise ApplicationError(
                504,
                "Keitaro не ответил вовремя. Черновик сохранён. Проверьте состояние в трекере или повторите Push.",
            ) from error
        except httpx.RequestError as error:
            raise ApplicationError(
                502,
                "Не удалось подключиться к Keitaro. Проверьте адрес и доступность сервера.",
            ) from error

        if not response.is_success:
            messages = {
                401: "Keitaro отклонил API-ключ.",
                402: "В этой редакции Keitaro недоступен Admin API.",
                403: "Доступ к Keitaro запрещён (403). Проверьте ключ и ограничения IP.",
                404: "Объект в Keitaro не найден.",
            }
            detail = messages.get(
                response.status_code, f"Keitaro вернул ошибку {response.status_code}."
            )
            raise ApplicationError(502, detail)

        if response.status_code == 204:
            return {}

        try:
            data = response.json()
        except ValueError as error:
            raise ApplicationError(502, "Keitaro вернул ответ в неожиданном формате.") from error

        if not isinstance(data, (dict, list)):
            raise ApplicationError(502, "Keitaro вернул ответ в неожиданном формате.")
        return data
