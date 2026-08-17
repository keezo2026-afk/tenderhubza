from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uid


class SourceType(str, Enum):
    NATIONAL = "NATIONAL"
    PROVINCIAL = "PROVINCIAL"
    MUNICIPAL = "MUNICIPAL"
    MUNICIPAL_ENTITY = "MUNICIPAL_ENTITY"
    SOE = "SOE"
    PUBLIC_ENTITY = "PUBLIC_ENTITY"
    UNIVERSITY = "UNIVERSITY"
    OTHER = "OTHER"


class Source(TimestampMixin, Base):
    __tablename__ = "sources"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    source_type: Mapped[str] = mapped_column(String(30))
    organisation: Mapped[str] = mapped_column(String(200))
    website_url: Mapped[str] = mapped_column(String(2048))
    api_url: Mapped[str | None] = mapped_column(String(2048))
    province: Mapped[str | None] = mapped_column(String(100))
    municipality: Mapped[str | None] = mapped_column(String(150))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    connector_type: Mapped[str] = mapped_column(String(200))
    polling_frequency: Mapped[str] = mapped_column(String(100), default="daily")
    last_successful_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_failed_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
