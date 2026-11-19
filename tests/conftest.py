from collections.abc import Iterator
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import backend.main as application
from backend.api.dependencies import get_keitaro_client
from backend.config import settings
from backend.database import get_db
from backend.integrations.keitaro import KeitaroClient
from tests.fakes import TrackerStub


@pytest.fixture
def session_factory(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    factory = sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(application, "engine", engine)
    monkeypatch.setattr(settings(), "app_token", "")
    monkeypatch.setattr(settings(), "campaign_name_prefix", "test_bakhshyan_")
    yield factory
    engine.dispose()


@pytest.fixture
def tracker_stub() -> TrackerStub:
    return TrackerStub()


@pytest.fixture
def client(session_factory, tracker_stub) -> Iterator[TestClient]:
    def test_session() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    application.app.dependency_overrides[get_db] = test_session
    application.app.dependency_overrides[get_keitaro_client] = lambda: KeitaroClient(tracker_stub)
    with TestClient(application.app) as test_client:
        yield test_client
    application.app.dependency_overrides.clear()


@pytest.fixture
def campaign(client):
    response = client.get("/api/campaigns/128")
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def stream(campaign):
    return next(stream for stream in campaign["streams"] if stream["editable"])


@pytest.fixture
def change_remote(tracker_stub):
    """Simulate an operator changing Keitaro outside the wrapper."""

    def mutate(operation):
        data = deepcopy(tracker_stub.data)
        operation(data)
        tracker_stub.data = data

    return mutate
