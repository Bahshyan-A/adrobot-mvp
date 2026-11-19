"""One-time migration from the earlier local/remote schema to a single Keitaro source."""

import logging
import sqlite3
from pathlib import Path
from uuid import uuid4

from sqlalchemy import Engine, inspect

from backend.models import Base

logger = logging.getLogger(__name__)


def backup_sqlite_database(engine: Engine) -> Path | None:
    database = engine.url.database
    if not database or database == ":memory:":
        return None

    source = Path(database).resolve()
    backup = source.with_name(f"{source.stem}.before-live-only-{uuid4().hex[:8]}.db")
    with sqlite3.connect(source) as source_connection, sqlite3.connect(backup) as destination:
        source_connection.backup(destination)
    logger.info("Local database backed up to %s", backup)
    return backup


def migrate_legacy_database(engine: Engine) -> Path | None:
    """Preserve real campaign IDs, draft revisions, and history before removing the old discriminator."""
    inspector = inspect(engine)
    if not inspector.has_table("campaigns"):
        return None
    if "mode" not in {column["name"] for column in inspector.get_columns("campaigns")}:
        return None
    if engine.dialect.name != "sqlite":
        raise RuntimeError("The legacy database migration supports SQLite only.")

    backup = backup_sqlite_database(engine)
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.commit()
        try:
            # Explicit BEGIN also makes SQLite DDL transactional.
            connection.exec_driver_sql("BEGIN IMMEDIATE")
            connection.exec_driver_sql("ALTER TABLE streams RENAME TO legacy_streams")
            connection.exec_driver_sql("ALTER TABLE campaigns RENAME TO legacy_campaigns")
            connection.exec_driver_sql("ALTER TABLE audit_events RENAME TO legacy_audit_events")
            connection.exec_driver_sql("DROP INDEX IF EXISTS ix_audit_events_campaign_remote_id")
            connection.exec_driver_sql("DROP INDEX IF EXISTS ix_audit_events_mode")
            Base.metadata.create_all(connection)

            connection.exec_driver_sql("""
                INSERT INTO campaigns (id, remote_id, name, data, synced_at)
                SELECT id, remote_id, name, data, synced_at
                FROM legacy_campaigns WHERE mode = 'live'
            """)
            connection.exec_driver_sql("""
                INSERT INTO streams (id, campaign_id, remote_id, data, published, draft, revision)
                SELECT s.id, s.campaign_id, s.remote_id, s.data, s.published, s.draft, s.revision
                FROM legacy_streams AS s
                JOIN campaigns AS c ON c.id = s.campaign_id
            """)
            connection.exec_driver_sql("""
                INSERT INTO audit_events
                    (id, campaign_remote_id, stream_remote_id, action, details, created_at)
                SELECT id, campaign_remote_id, stream_remote_id, action, details, created_at
                FROM legacy_audit_events WHERE mode = 'live'
            """)
            connection.exec_driver_sql("DROP TABLE legacy_streams")
            connection.exec_driver_sql("DROP TABLE legacy_campaigns")
            connection.exec_driver_sql("DROP TABLE legacy_audit_events")
            connection.exec_driver_sql("DROP TABLE IF EXISTS demo_state")

            if connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall():
                raise RuntimeError("Database migration produced invalid foreign keys.")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            connection.commit()

    return backup
