from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, uid


class RawIngestion(Base):
    __tablename__ = "raw_ingestions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id"))
    source_identifier: Mapped[str] = mapped_column(String(255))
    original_source_url: Mapped[str] = mapped_column(String(2048))
    raw_payload: Mapped[dict] = mapped_column(JSON)
    request_url: Mapped[str | None] = mapped_column(String(2048))
    http_status: Mapped[int | None] = mapped_column()
    content_type: Mapped[str | None] = mapped_column(String(255))
    response_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payload_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    source_release_id: Mapped[str | None] = mapped_column(String(255))
    ocds_identifier: Mapped[str | None] = mapped_column(String(255))
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    connector_version: Mapped[str] = mapped_column(String(50))
    document_references: Mapped[list] = mapped_column(JSON, default=list)
    normalization_status: Mapped[str] = mapped_column(String(30), default="PENDING")
    processing_status: Mapped[str] = mapped_column(String(30), default="DISCOVERED")
    error: Mapped[str | None] = mapped_column(Text)


class ConnectorRun(Base):
    __tablename__ = "connector_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id"), index=True)
    connector_name: Mapped[str] = mapped_column(String(200))
    connector_version: Mapped[str] = mapped_column(String(50))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="RUNNING")
    records_discovered: Mapped[int] = mapped_column(default=0)
    records_fetched: Mapped[int] = mapped_column(default=0)
    records_parsed: Mapped[int] = mapped_column(default=0)
    records_normalized: Mapped[int] = mapped_column(default=0)
    records_inserted: Mapped[int] = mapped_column(default=0)
    records_updated: Mapped[int] = mapped_column(default=0)
    records_skipped: Mapped[int] = mapped_column(default=0)
    records_failed: Mapped[int] = mapped_column(default=0)
    documents_discovered: Mapped[int] = mapped_column(default=0)
    error_category: Mapped[str | None] = mapped_column(String(50))
    zero_result_anomaly: Mapped[bool] = mapped_column(default=False)
    error_count: Mapped[int] = mapped_column(default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    duration_seconds: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))


class ConnectorState(Base):
    __tablename__ = "connector_states"
    source_id: Mapped[str] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True
    )
    high_water_date: Mapped[date | None] = mapped_column(Date)
    high_water_release_id: Mapped[str | None] = mapped_column(String(255))
    last_run_id: Mapped[str | None] = mapped_column(ForeignKey("connector_runs.id"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
