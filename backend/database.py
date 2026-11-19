"""Database engine and request-scoped SQLAlchemy sessions."""

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from backend.config import settings

engine = create_engine(
    settings().database_url,
    **(
        {"connect_args": {"check_same_thread": False, "timeout": 30}}
        if settings().database_url.startswith("sqlite")
        else {}
    ),
)
if settings().database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def sqlite_settings(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")


SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    with SessionLocal() as db:
        yield db
