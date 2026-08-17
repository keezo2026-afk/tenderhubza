from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from uuid import uuid4
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, JSON, Numeric, String, Text, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

def uid() -> str: return str(uuid4())

class Role(str, Enum): USER="USER"; ADMIN="ADMIN"
class UserStatus(str, Enum): ACTIVE="ACTIVE"; DISABLED="DISABLED"; PENDING="PENDING"
class SourceType(str, Enum):
    NATIONAL="NATIONAL"; PROVINCIAL="PROVINCIAL"; MUNICIPAL="MUNICIPAL"; MUNICIPAL_ENTITY="MUNICIPAL_ENTITY"; SOE="SOE"; PUBLIC_ENTITY="PUBLIC_ENTITY"; UNIVERSITY="UNIVERSITY"; OTHER="OTHER"

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class User(TimestampMixin, Base):
    __tablename__="users"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str]=mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str]=mapped_column(String(255))
    first_name: Mapped[str]=mapped_column(String(100)); last_name: Mapped[str]=mapped_column(String(100))
    phone: Mapped[str|None]=mapped_column(String(30)); role: Mapped[str]=mapped_column(String(20), default=Role.USER.value)
    status: Mapped[str]=mapped_column(String(20), default=UserStatus.ACTIVE.value)
    profile: Mapped["Profile|None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")

class Profile(TimestampMixin, Base):
    __tablename__="profiles"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); user_id: Mapped[str]=mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    display_name: Mapped[str|None]=mapped_column(String(200)); province: Mapped[str|None]=mapped_column(String(100)); city: Mapped[str|None]=mapped_column(String(100)); notification_preferences: Mapped[dict]=mapped_column(JSON, default=dict)
    user: Mapped[User]=relationship(back_populates="profile")

class Business(TimestampMixin, Base):
    __tablename__="businesses"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); owner_user_id: Mapped[str]=mapped_column(ForeignKey("users.id"))
    business_name: Mapped[str]=mapped_column(String(255)); registration_number: Mapped[str|None]=mapped_column(String(100), unique=True); industry: Mapped[str|None]=mapped_column(String(150)); province: Mapped[str|None]=mapped_column(String(100)); municipality: Mapped[str|None]=mapped_column(String(150)); business_size: Mapped[str|None]=mapped_column(String(50)); bbbee_level: Mapped[str|None]=mapped_column(String(30)); cidb_grade: Mapped[str|None]=mapped_column(String(30)); services: Mapped[list]=mapped_column(JSON, default=list); products: Mapped[list]=mapped_column(JSON, default=list); preferred_tender_categories: Mapped[list]=mapped_column(JSON, default=list); preferred_geographic_areas: Mapped[list]=mapped_column(JSON, default=list); preferred_value_min: Mapped[Decimal|None]=mapped_column(Numeric(18,2)); preferred_value_max: Mapped[Decimal|None]=mapped_column(Numeric(18,2))

class Province(TimestampMixin, Base):
    __tablename__="provinces"; id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); code: Mapped[str]=mapped_column(String(10), unique=True); name: Mapped[str]=mapped_column(String(100), unique=True)
class District(TimestampMixin, Base):
    __tablename__="districts"; id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); province_id: Mapped[str]=mapped_column(ForeignKey("provinces.id")); code: Mapped[str|None]=mapped_column(String(20), unique=True); name: Mapped[str]=mapped_column(String(150))
class Municipality(TimestampMixin, Base):
    __tablename__="municipalities"; id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); district_id: Mapped[str|None]=mapped_column(ForeignKey("districts.id")); province_id: Mapped[str]=mapped_column(ForeignKey("provinces.id")); code: Mapped[str|None]=mapped_column(String(20), unique=True); name: Mapped[str]=mapped_column(String(150)); municipality_type: Mapped[str|None]=mapped_column(String(50)); active: Mapped[bool]=mapped_column(Boolean, default=True)
class MunicipalEntity(TimestampMixin, Base):
    __tablename__="municipal_entities"; id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); municipality_id: Mapped[str]=mapped_column(ForeignKey("municipalities.id")); name: Mapped[str]=mapped_column(String(200)); active: Mapped[bool]=mapped_column(Boolean, default=True)

class Source(TimestampMixin, Base):
    __tablename__="sources"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); name: Mapped[str]=mapped_column(String(200), unique=True); source_type: Mapped[str]=mapped_column(String(30)); organisation: Mapped[str]=mapped_column(String(200)); website_url: Mapped[str]=mapped_column(String(2048)); api_url: Mapped[str|None]=mapped_column(String(2048)); province: Mapped[str|None]=mapped_column(String(100)); municipality: Mapped[str|None]=mapped_column(String(150)); active: Mapped[bool]=mapped_column(Boolean, default=True); connector_type: Mapped[str]=mapped_column(String(200)); polling_frequency: Mapped[str]=mapped_column(String(100), default="daily"); last_successful_run: Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); last_failed_run: Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); last_error: Mapped[str|None]=mapped_column(Text)

class Tender(TimestampMixin, Base):
    __tablename__="tenders"; __table_args__=(UniqueConstraint("source_id","source_reference", name="uq_tender_source_reference"),)
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); source_id: Mapped[str]=mapped_column(ForeignKey("sources.id"), index=True); source_reference: Mapped[str]=mapped_column(String(255)); reference_number: Mapped[str|None]=mapped_column(String(255), index=True); title: Mapped[str]=mapped_column(String(500), index=True); description: Mapped[str|None]=mapped_column(Text); organisation: Mapped[str]=mapped_column(String(255), index=True); province: Mapped[str|None]=mapped_column(String(100), index=True); municipality: Mapped[str|None]=mapped_column(String(150), index=True); district: Mapped[str|None]=mapped_column(String(150)); category: Mapped[str|None]=mapped_column(String(150), index=True); subcategory: Mapped[str|None]=mapped_column(String(150)); tender_type: Mapped[str|None]=mapped_column(String(100), index=True); issue_date: Mapped[date|None]=mapped_column(Date); closing_date: Mapped[date|None]=mapped_column(Date, index=True); closing_time: Mapped[time|None]=mapped_column(Time); estimated_value: Mapped[Decimal|None]=mapped_column(Numeric(18,2)); currency: Mapped[str]=mapped_column(String(3), default="ZAR"); source_url: Mapped[str]=mapped_column(String(2048)); status: Mapped[str]=mapped_column(String(30), default="OPEN", index=True); contact_name: Mapped[str|None]=mapped_column(String(200)); contact_email: Mapped[str|None]=mapped_column(String(320)); contact_phone: Mapped[str|None]=mapped_column(String(50))

class RawIngestion(Base):
    __tablename__="raw_ingestions"; id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); source_id: Mapped[str]=mapped_column(ForeignKey("sources.id")); source_identifier: Mapped[str]=mapped_column(String(255)); original_source_url: Mapped[str]=mapped_column(String(2048)); raw_payload: Mapped[dict]=mapped_column(JSON); ingested_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now()); connector_version: Mapped[str]=mapped_column(String(50)); document_references: Mapped[list]=mapped_column(JSON, default=list); normalization_status: Mapped[str]=mapped_column(String(30), default="PENDING"); processing_status: Mapped[str]=mapped_column(String(30), default="DISCOVERED"); error: Mapped[str|None]=mapped_column(Text)
class TenderDocument(TimestampMixin, Base):
    __tablename__="tender_documents"; id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); tender_id: Mapped[str]=mapped_column(ForeignKey("tenders.id", ondelete="CASCADE")); name: Mapped[str]=mapped_column(String(255)); source_url: Mapped[str]=mapped_column(String(2048)); storage_key: Mapped[str|None]=mapped_column(String(1024)); mime_type: Mapped[str|None]=mapped_column(String(100))
class TenderRequirement(TimestampMixin, Base):
    __tablename__="tender_requirements"; id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); tender_id: Mapped[str]=mapped_column(ForeignKey("tenders.id", ondelete="CASCADE")); requirement_type: Mapped[str]=mapped_column(String(100)); text: Mapped[str]=mapped_column(Text)
class TenderAmendment(TimestampMixin, Base):
    __tablename__="tender_amendments"; id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); tender_id: Mapped[str]=mapped_column(ForeignKey("tenders.id", ondelete="CASCADE")); source_reference: Mapped[str]=mapped_column(String(255)); details: Mapped[str]=mapped_column(Text)
class TenderSourceVersion(Base):
    __tablename__="tender_source_versions"; id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); tender_id: Mapped[str]=mapped_column(ForeignKey("tenders.id", ondelete="CASCADE")); raw_ingestion_id: Mapped[str]=mapped_column(ForeignKey("raw_ingestions.id")); captured_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now())
class TenderAward(TimestampMixin, Base):
    __tablename__="tender_awards"; id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); tender_id: Mapped[str]=mapped_column(ForeignKey("tenders.id", ondelete="CASCADE")); supplier_name: Mapped[str]=mapped_column(String(255)); amount: Mapped[Decimal|None]=mapped_column(Numeric(18,2)); awarded_at: Mapped[date|None]=mapped_column(Date)
class TenderAnalysis(TimestampMixin, Base):
    __tablename__="tender_analyses"; id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); tender_id: Mapped[str]=mapped_column(ForeignKey("tenders.id", ondelete="CASCADE")); provider: Mapped[str]=mapped_column(String(100)); model: Mapped[str]=mapped_column(String(100)); result: Mapped[dict]=mapped_column(JSON); status: Mapped[str]=mapped_column(String(30), default="PENDING")
class TenderMatch(TimestampMixin, Base):
    __tablename__="tender_matches"; id: Mapped[str]=mapped_column(String(36), primary_key=True, default=uid); tender_id: Mapped[str]=mapped_column(ForeignKey("tenders.id", ondelete="CASCADE")); business_id: Mapped[str]=mapped_column(ForeignKey("businesses.id", ondelete="CASCADE")); score: Mapped[Decimal|None]=mapped_column(Numeric(5,4)); explanation: Mapped[dict]=mapped_column(JSON, default=dict)
class RevokedToken(Base):
    __tablename__="revoked_tokens"; digest: Mapped[str]=mapped_column(String(64), primary_key=True); expires_at: Mapped[datetime]=mapped_column(DateTime(timezone=True)); revoked_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now())
class PasswordResetToken(Base):
    __tablename__="password_reset_tokens"; digest: Mapped[str]=mapped_column(String(64), primary_key=True); user_id: Mapped[str]=mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True); expires_at: Mapped[datetime]=mapped_column(DateTime(timezone=True)); used_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now())
