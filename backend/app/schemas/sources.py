from datetime import datetime

from pydantic import BaseModel, Field


class AdminSourceInput(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(pattern=r"^[a-z0-9-]+$", max_length=200)
    source_type: str
    organisation: str
    website_url: str
    procurement_url: str | None = None
    tender_url: str | None = None
    api_url: str | None = None
    province_id: str | None = None
    district_id: str | None = None
    municipality_id: str | None = None
    connector_type: str = "UNASSIGNED"
    priority: int = Field(default=5, ge=1, le=10)
    polling_interval_minutes: int = Field(default=1440, ge=15)
    status: str = "DISCOVERED"


class AdminSourceOut(AdminSourceInput):
    id: str
    active: bool
    consecutive_failures: int
    last_attempted_at: datetime | None
    last_successful_run: datetime | None
    last_failed_run: datetime | None
    last_tender_discovered_at: datetime | None
    last_error_category: str | None
    last_error_message: str | None


class SourceDiscoveryInput(BaseModel):
    discovered_by: str
    discovery_method: str
    evidence_url: str
    notes: str | None = None
