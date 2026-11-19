"""Application errors shared by services and integration adapters."""

from typing import Any


class ApplicationError(Exception):
    def __init__(self, status_code: int, detail: str | dict[str, Any]) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail if isinstance(detail, str) else detail.get("message", ""))
