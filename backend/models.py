"""SQLAlchemy models. Remote payloads and local drafts are stored separately."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from backend.domain.offers import OfferSnapshot


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    remote_id: Mapped[int] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(String(255))
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    streams: Mapped[list["Stream"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
    )


class Stream(Base):
    __tablename__ = "streams"
    __table_args__ = (UniqueConstraint("campaign_id", "remote_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
    remote_id: Mapped[int] = mapped_column(Integer)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
    published: Mapped[list[OfferSnapshot]] = mapped_column(JSON, default=list)
    draft: Mapped[list[OfferSnapshot]] = mapped_column(JSON, default=list)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    campaign: Mapped[Campaign] = relationship(back_populates="streams")

    __mapper_args__ = {"version_id_col": revision}

    @property
    def is_dirty(self) -> bool:
        return self.draft != self.published

    @property
    def is_missing(self) -> bool:
        return self.data.get("_missing", False)

    @property
    def is_editable(self) -> bool:
        return self.data.get("schema") == "landings" or bool(self.data.get("offers"))


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_remote_id: Mapped[int] = mapped_column(Integer, index=True)
    stream_remote_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(40))
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
