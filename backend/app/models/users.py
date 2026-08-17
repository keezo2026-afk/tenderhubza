from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    JSON,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uid


class Role(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    PENDING = "PENDING"


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(30))
    role: Mapped[str] = mapped_column(String(20), default=Role.USER.value)
    status: Mapped[str] = mapped_column(String(20), default=UserStatus.ACTIVE.value)
    profile: Mapped["Profile|None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class Profile(TimestampMixin, Base):
    __tablename__ = "profiles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    display_name: Mapped[str | None] = mapped_column(String(200))
    province: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    notification_preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    user: Mapped[User] = relationship(back_populates="profile")


class Business(TimestampMixin, Base):
    __tablename__ = "businesses"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    business_name: Mapped[str] = mapped_column(String(255))
    registration_number: Mapped[str | None] = mapped_column(String(100), unique=True)
    industry: Mapped[str | None] = mapped_column(String(150))
    province: Mapped[str | None] = mapped_column(String(100))
    municipality: Mapped[str | None] = mapped_column(String(150))
    business_size: Mapped[str | None] = mapped_column(String(50))
    bbbee_level: Mapped[str | None] = mapped_column(String(30))
    cidb_grade: Mapped[str | None] = mapped_column(String(30))
    services: Mapped[list] = mapped_column(JSON, default=list)
    products: Mapped[list] = mapped_column(JSON, default=list)
    preferred_tender_categories: Mapped[list] = mapped_column(JSON, default=list)
    preferred_geographic_areas: Mapped[list] = mapped_column(JSON, default=list)
    preferred_value_min: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    preferred_value_max: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
