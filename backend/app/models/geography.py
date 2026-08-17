from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uid


class Province(TimestampMixin, Base):
    __tablename__ = "provinces"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    code: Mapped[str] = mapped_column(String(10), unique=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class District(TimestampMixin, Base):
    __tablename__ = "districts"
    dataset_id: Mapped[str | None] = mapped_column(ForeignKey("geography_datasets.id"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    province_id: Mapped[str] = mapped_column(ForeignKey("provinces.id"))
    code: Mapped[str | None] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(150))


class Municipality(TimestampMixin, Base):
    __tablename__ = "municipalities"
    dataset_id: Mapped[str | None] = mapped_column(ForeignKey("geography_datasets.id"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    district_id: Mapped[str | None] = mapped_column(ForeignKey("districts.id"))
    province_id: Mapped[str] = mapped_column(ForeignKey("provinces.id"))
    code: Mapped[str | None] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    municipality_type: Mapped[str | None] = mapped_column(String(50))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class MunicipalEntity(TimestampMixin, Base):
    __tablename__ = "municipal_entities"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    municipality_id: Mapped[str] = mapped_column(ForeignKey("municipalities.id"))
    name: Mapped[str] = mapped_column(String(200))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class GeographyDataset(Base):
    __tablename__ = "geography_datasets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(200))
    source: Mapped[str] = mapped_column(String(200))
    source_url: Mapped[str] = mapped_column(String(2048))
    version: Mapped[str] = mapped_column(String(100))
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class GeographyResolutionIssue(Base):
    __tablename__ = "geography_resolution_issues"
    __table_args__ = (
        Index("ix_geography_issue_source", "source_id"),
        Index("ix_geography_issue_raw", "raw_ingestion_id"),
        Index("ix_geography_issue_tender", "tender_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    raw_ingestion_id: Mapped[str | None] = mapped_column(
        ForeignKey("raw_ingestions.id", ondelete="SET NULL")
    )
    tender_id: Mapped[str | None] = mapped_column(ForeignKey("tenders.id", ondelete="SET NULL"))
    province_value: Mapped[str | None] = mapped_column(String(200))
    district_value: Mapped[str | None] = mapped_column(String(200))
    municipality_value: Mapped[str | None] = mapped_column(String(200))
    reason: Mapped[str] = mapped_column(String(100))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
