from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
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
    PUBLIC_INSTITUTION = "PUBLIC_INSTITUTION"
    OTHER = "OTHER"


class Source(TimestampMixin, Base):
    __tablename__ = "sources"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    slug: Mapped[str | None] = mapped_column(String(200), unique=True)
    source_type: Mapped[str] = mapped_column(String(30))
    organisation: Mapped[str] = mapped_column(String(200))
    website_url: Mapped[str] = mapped_column(String(2048))
    procurement_url: Mapped[str | None] = mapped_column(String(2048))
    tender_url: Mapped[str | None] = mapped_column(String(2048))
    province_id: Mapped[str | None] = mapped_column(ForeignKey("provinces.id"))
    district_id: Mapped[str | None] = mapped_column(ForeignKey("districts.id"))
    municipality_id: Mapped[str | None] = mapped_column(ForeignKey("municipalities.id"))
    api_url: Mapped[str | None] = mapped_column(String(2048))
    province: Mapped[str | None] = mapped_column(String(100))
    municipality: Mapped[str | None] = mapped_column(String(150))
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(
        String(30), default="DISCOVERED", server_default="DISCOVERED"
    )
    priority: Mapped[int] = mapped_column(default=5, server_default="5")
    connector_type: Mapped[str] = mapped_column(String(200))
    polling_frequency: Mapped[str] = mapped_column(String(100), default="daily")
    polling_interval_minutes: Mapped[int] = mapped_column(default=1440, server_default="1440")
    last_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_tender_discovered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consecutive_failures: Mapped[int] = mapped_column(default=0, server_default="0")
    last_error_category: Mapped[str | None] = mapped_column(String(50))
    last_successful_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_failed_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)


class SourceDiscovery(TimestampMixin, Base):
    __tablename__ = "source_discoveries"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    discovered_by: Mapped[str] = mapped_column(String(200))
    discovery_method: Mapped[str] = mapped_column(String(50))
    evidence_url: Mapped[str] = mapped_column(String(2048))
    notes: Mapped[str | None] = mapped_column(Text)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified_by: Mapped[str | None] = mapped_column(String(200))
    verification_status: Mapped[str] = mapped_column(String(30), default="DISCOVERED")


class ConnectorRegistration(TimestampMixin, Base):
    __tablename__ = "connector_registrations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_id: Mapped[str] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(200), unique=True)
    version: Mapped[str] = mapped_column(String(50))
    connector_type: Mapped[str] = mapped_column(String(40))
    capabilities: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="REGISTERED")
    implementation_reference: Mapped[str | None] = mapped_column(String(500))


class MunicipalitySourceCoverage(TimestampMixin, Base):
    __tablename__ = "municipality_source_coverage"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    municipality_id: Mapped[str] = mapped_column(
        ForeignKey("municipalities.id", ondelete="CASCADE"), unique=True, index=True
    )
    source_id: Mapped[str | None] = mapped_column(
        ForeignKey("sources.id", ondelete="SET NULL"), index=True
    )
    official_website_url: Mapped[str | None] = mapped_column(String(2048))
    source_identified: Mapped[bool] = mapped_column(Boolean, default=False)
    procurement_url: Mapped[str | None] = mapped_column(String(2048))
    verification_status: Mapped[str] = mapped_column(String(30), default="NOT_RESEARCHED")
    source_mechanism: Mapped[str | None] = mapped_column(String(40))
    connector_required: Mapped[bool] = mapped_column(Boolean, default=True)
    connector_implemented: Mapped[bool] = mapped_column(Boolean, default=False)
