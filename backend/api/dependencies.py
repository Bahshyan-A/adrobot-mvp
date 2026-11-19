import secrets
from collections.abc import Iterator
from typing import Annotated

import httpx
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.errors import ApplicationError
from backend.integrations.keitaro import KeitaroClient
from backend.integrations.transport import HttpTransport

DatabaseSession = Annotated[Session, Depends(get_db)]


def authorize(authorization: Annotated[str, Header()] = "") -> None:
    token = settings().app_token
    if token and not secrets.compare_digest(authorization, f"Bearer {token}"):
        raise ApplicationError(401, "Введите токен доступа к приложению.")


def get_keitaro_client() -> Iterator[KeitaroClient]:
    config = settings()
    with httpx.Client(timeout=config.keitaro_timeout, follow_redirects=False) as http_client:
        yield KeitaroClient(HttpTransport(config, http_client))


TrackerClient = Annotated[KeitaroClient, Depends(get_keitaro_client)]
