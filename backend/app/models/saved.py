from sqlalchemy import (
    JSON,
    Boolean,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uid


class SavedTender(TimestampMixin, Base):
    __tablename__ = "saved_tenders"
    __table_args__ = (UniqueConstraint("user_id", "tender_id", name="uq_saved_tender_user_tender"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    tender_id: Mapped[str] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"), index=True)
    closing_reminders_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reminder_days: Mapped[list] = mapped_column(JSON, default=lambda: [7, 3, 1, 0])


class SavedSearch(TimestampMixin, Base):
    __tablename__ = "saved_searches"
    __table_args__ = (Index("ix_saved_searches_user_created", "user_id", "created_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    query: Mapped[str] = mapped_column(String(200), default="")
    filters: Mapped[dict] = mapped_column(JSON, default=dict)
    sort: Mapped[str] = mapped_column(String(30), default="relevance")
    alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
