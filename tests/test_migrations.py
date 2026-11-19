import json
import sqlite3

import pytest
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import Session

from backend.migrations import migrate_legacy_database
from backend.models import AuditEvent, Base, Campaign, Stream


@pytest.fixture
def legacy_engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    published = [
        {
            "offer_id": 3749,
            "name": "Original offer",
            "share": 100,
            "state": "active",
            "pinned": False,
            "removed": False,
            "new": False,
            "removed_reason": None,
        }
    ]
    draft = [{**published[0], "pinned": True}]

    with engine.begin() as connection:
        connection.exec_driver_sql("""
            CREATE TABLE campaigns (
                id INTEGER PRIMARY KEY, mode TEXT NOT NULL, remote_id INTEGER NOT NULL,
                name TEXT NOT NULL, data JSON NOT NULL, synced_at DATETIME NOT NULL,
                UNIQUE (mode, remote_id)
            )
        """)
        connection.exec_driver_sql("""
            CREATE TABLE streams (
                id INTEGER PRIMARY KEY, campaign_id INTEGER REFERENCES campaigns(id),
                remote_id INTEGER, data JSON, published JSON, draft JSON, revision INTEGER
            )
        """)
        connection.exec_driver_sql("""
            CREATE TABLE audit_events (
                id INTEGER PRIMARY KEY, mode TEXT NOT NULL, campaign_remote_id INTEGER,
                stream_remote_id INTEGER, action TEXT, details JSON, created_at DATETIME
            )
        """)
        connection.exec_driver_sql(
            "CREATE INDEX ix_audit_events_campaign_remote_id ON audit_events (campaign_remote_id)"
        )
        connection.exec_driver_sql("CREATE INDEX ix_audit_events_mode ON audit_events (mode)")
        connection.exec_driver_sql("CREATE TABLE demo_state (key TEXT PRIMARY KEY, data JSON)")

        for campaign_id, source in [(1, "demo"), (2, "live")]:
            connection.execute(
                text("""
                    INSERT INTO campaigns VALUES (:id, :mode, 128, :name, :data, :time)
                """),
                {
                    "id": campaign_id,
                    "mode": source,
                    "name": f"{source} campaign",
                    "data": json.dumps({"id": 128, "name": f"{source} campaign"}),
                    "time": "2026-11-19 09:00:00",
                },
            )
            connection.execute(
                text("""
                    INSERT INTO streams VALUES (:id, :campaign_id, 402, :data, :published, :draft, 9)
                """),
                {
                    "id": campaign_id + 10,
                    "campaign_id": campaign_id,
                    "data": json.dumps({"name": "Offer stream", "schema": "landings"}),
                    "published": json.dumps(published),
                    "draft": json.dumps(draft),
                },
            )
            connection.execute(
                text("""
                    INSERT INTO audit_events VALUES (:id, :mode, 128, 402, 'pin', '{}', :time)
                """),
                {"id": campaign_id + 20, "mode": source, "time": "2026-11-19 09:01:00"},
            )

    yield engine
    engine.dispose()


def test_migration_preserves_real_drafts_ids_and_history_with_backup(legacy_engine):
    backup = migrate_legacy_database(legacy_engine)
    assert backup is not None and backup.is_file()

    inspector = inspect(legacy_engine)
    assert "mode" not in {column["name"] for column in inspector.get_columns("campaigns")}
    assert "demo_state" not in inspector.get_table_names()

    with Session(legacy_engine) as session:
        campaigns = session.scalars(select(Campaign)).all()
        assert [(campaign.id, campaign.remote_id) for campaign in campaigns] == [(2, 128)]
        stream = session.scalar(select(Stream))
        assert stream.id == 12 and stream.campaign_id == 2
        assert stream.revision == 9
        assert stream.is_dirty and stream.draft[0]["pinned"]
        assert not stream.published[0]["pinned"]
        assert session.scalar(select(AuditEvent)).id == 22

    with sqlite3.connect(backup) as connection:
        assert connection.execute("SELECT count(*) FROM campaigns").fetchone()[0] == 2
        assert connection.execute("SELECT mode FROM campaigns WHERE id = 1").fetchone()[0] == "demo"

    assert migrate_legacy_database(legacy_engine) is None


def test_failed_migration_rolls_back_schema_changes(legacy_engine, monkeypatch):
    def fail_create(*_args, **_kwargs):
        raise RuntimeError("Failed migration")

    monkeypatch.setattr(Base.metadata, "create_all", fail_create)
    with pytest.raises(RuntimeError, match="Failed migration"):
        migrate_legacy_database(legacy_engine)

    inspector = inspect(legacy_engine)
    assert "mode" in {column["name"] for column in inspector.get_columns("campaigns")}
    assert "legacy_campaigns" not in inspector.get_table_names()
    with legacy_engine.connect() as connection:
        assert connection.exec_driver_sql("SELECT count(*) FROM campaigns").scalar() == 2
