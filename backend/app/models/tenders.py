from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uid


class Tender(TimestampMixin, Base):
    __tablename__ = "tenders"
    __table_args__ = (
        UniqueConstraint("source_id", "source_reference", name="uq_tender_source_reference"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id"), index=True)
    source_reference: Mapped[str] = mapped_column(String(255))
    reference_number: Mapped[str | None] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    organisation: Mapped[str] = mapped_column(String(255), index=True)
    province: Mapped[str | None] = mapped_column(String(100), index=True)
    municipality: Mapped[str | None] = mapped_column(String(150), index=True)
    district: Mapped[str | None] = mapped_column(String(150))
    category: Mapped[str | None] = mapped_column(String(150), index=True)
    subcategory: Mapped[str | None] = mapped_column(String(150))
    tender_type: Mapped[str | None] = mapped_column(String(100), index=True)
    issue_date: Mapped[date | None] = mapped_column(Date)
    closing_date: Mapped[date | None] = mapped_column(Date, index=True)
    closing_time: Mapped[time | None] = mapped_column(Time)
    estimated_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3), default="ZAR")
    source_url: Mapped[str] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(30), default="OPEN", index=True)
    contact_name: Mapped[str | None] = mapped_column(String(200))
    contact_email: Mapped[str | None] = mapped_column(String(320))
    contact_phone: Mapped[str | None] = mapped_column(String(50))
    source_release_id: Mapped[str | None] = mapped_column(String(255), index=True)
    ocds_identifier: Mapped[str | None] = mapped_column(String(255), index=True)
    payload_hash: Mapped[str | None] = mapped_column(String(64))
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    province_id: Mapped[str | None] = mapped_column(ForeignKey("provinces.id"))
    district_id: Mapped[str | None] = mapped_column(ForeignKey("districts.id"))
    municipality_id: Mapped[str | None] = mapped_column(ForeignKey("municipalities.id"))


class TenderDocument(TimestampMixin, Base):
    __tablename__ = "tender_documents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tender_id: Mapped[str] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    source_url: Mapped[str] = mapped_column(String(2048))
    storage_key: Mapped[str | None] = mapped_column(String(1024))
    mime_type: Mapped[str | None] = mapped_column(String(100))


class TenderRequirement(TimestampMixin, Base):
    __tablename__ = "tender_requirements"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tender_id: Mapped[str] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"))
    requirement_type: Mapped[str] = mapped_column(String(100))
    text: Mapped[str] = mapped_column(Text)


class TenderAmendment(TimestampMixin, Base):
    __tablename__ = "tender_amendments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tender_id: Mapped[str] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"))
    source_reference: Mapped[str] = mapped_column(String(255))
    details: Mapped[str] = mapped_column(Text)


class TenderSourceVersion(Base):
    __tablename__ = "tender_source_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tender_id: Mapped[str] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"))
    raw_ingestion_id: Mapped[str] = mapped_column(ForeignKey("raw_ingestions.id"))
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    change_summary: Mapped[dict] = mapped_column(JSON, default=dict)


class TenderAward(TimestampMixin, Base):
    __tablename__ = "tender_awards"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tender_id: Mapped[str] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"))
    supplier_name: Mapped[str] = mapped_column(String(255))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    awarded_at: Mapped[date | None] = mapped_column(Date)


class TenderAnalysis(TimestampMixin, Base):
    __tablename__ = "tender_analyses"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tender_id: Mapped[str] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(100))
    result: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default="PENDING")


class TenderMatch(TimestampMixin, Base):
    __tablename__ = "tender_matches"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tender_id: Mapped[str] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"))
    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    explanation: Mapped[dict] = mapped_column(JSON, default=dict)


class TenderDuplicateCandidate(TimestampMixin, Base):
    __tablename__ = "tender_duplicate_candidates"
    __table_args__ = (
        UniqueConstraint("tender_id", "candidate_tender_id", name="uq_tender_duplicate_pair"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    match_method: Mapped[str] = mapped_column(String(50), default="EXACT_REFERENCE")
    signals: Mapped[list] = mapped_column(JSON, default=list)
    tender_id: Mapped[str] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"), index=True)
    candidate_tender_id: Mapped[str] = mapped_column(
        ForeignKey("tenders.id", ondelete="CASCADE"), index=True
    )
    reason: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
