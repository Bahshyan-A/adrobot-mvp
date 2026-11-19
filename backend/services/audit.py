from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import AuditEvent


def record_event(
    session: Session,
    campaign_id: int,
    action: str,
    stream_id: int | None = None,
    **details: Any,
) -> None:
    session.add(
        AuditEvent(
            campaign_remote_id=campaign_id,
            stream_remote_id=stream_id,
            action=action,
            details=details,
        )
    )


def get_history(session: Session, campaign_id: int) -> list[dict[str, Any]]:
    statement = (
        select(AuditEvent)
        .where(
            AuditEvent.campaign_remote_id == campaign_id,
        )
        .order_by(AuditEvent.id.desc())
        .limit(100)
    )
    return [
        {
            "id": event.id,
            "action": event.action,
            "stream_id": event.stream_remote_id,
            "details": event.details,
            "created_at": event.created_at.isoformat(),
        }
        for event in session.scalars(statement)
    ]
