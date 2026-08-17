from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    first_name: str
    last_name: str
    phone: str | None
    role: str
    status: str
    created_at: datetime


class TenderCreate(BaseModel):
    source_id: str
    source_reference: str = Field(min_length=1, max_length=255)
    reference_number: str | None = None
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    organisation: str = Field(min_length=1, max_length=255)
    province: str | None = None
    municipality: str | None = None
    district: str | None = None
    category: str | None = None
    subcategory: str | None = None
    tender_type: str | None = None
    issue_date: date | None = None
    closing_date: date | None = None
    closing_time: time | None = None
    estimated_value: Decimal | None = None
    currency: str = "ZAR"
    source_url: str
    status: str = "OPEN"
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None


class TenderOut(TenderCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    updated_at: datetime


class SourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    source_type: str
    organisation: str
    website_url: str
    api_url: str | None = None
    province: str | None = None
    municipality: str | None = None
    active: bool = True
    connector_type: str
    polling_frequency: str = "daily"


class SourceOut(SourceCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    last_successful_run: datetime | None
    last_failed_run: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime


class ProvinceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    code: str
    name: str


class DistrictOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    province_id: str
    code: str | None
    name: str


class MunicipalityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    province_id: str
    district_id: str | None
    code: str | None
    name: str
    municipality_type: str | None
    active: bool


class TenderCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    source_reference: str
    reference_number: str | None
    title: str
    organisation: str
    province: str | None
    municipality: str | None
    category: str | None
    tender_type: str | None
    issue_date: date | None
    closing_date: date | None
    closing_time: time | None
    estimated_value: Decimal | None
    currency: str
    status: str
    created_at: datetime
    ingested_at: datetime


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    source_url: str
    mime_type: str | None


class SourceAttribution(BaseModel):
    id: str
    name: str
    organisation: str
    website_url: str


class TenderDetail(TenderOut):
    source_release_id: str | None
    ocds_identifier: str | None
    ingested_at: datetime
    documents: list[DocumentOut]
    source: SourceAttribution


class HomeResponse(BaseModel):
    latest: list[TenderCard]
    closing_soon: list[TenderCard]
    recently_added: list[TenderCard]


class ConnectorRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    source_id: str
    connector_name: str
    connector_version: str
    started_at: datetime
    completed_at: datetime | None
    status: str
    records_discovered: int
    records_inserted: int
    records_updated: int
    records_failed: int
    last_error: str | None
    duration_seconds: Decimal | None


class SavedTenderItem(BaseModel):
    saved_at: datetime
    tender: TenderCard


class TenderIdsRequest(BaseModel):
    tender_ids: list[str] = Field(min_length=1, max_length=100)


class TenderSavedState(BaseModel):
    tender_id: str
    saved: bool
    closing_reminders_enabled: bool | None = None
    reminder_days: list[int] | None = None


class SavedSearchFilters(BaseModel):
    provinceId: str | None = None
    districtId: str | None = None
    municipalityId: str | None = None
    category: str = ""
    tenderType: str = ""
    organisation: str = ""
    closingFrom: str = ""
    closingTo: str = ""
    issueFrom: str = ""
    issueTo: str = ""
    minValue: str = ""
    maxValue: str = ""
    status: str = ""


class SavedSearchInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    query: str = Field(default="", max_length=200)
    filters: SavedSearchFilters = Field(default_factory=SavedSearchFilters)
    sort: str = Field(default="relevance", pattern="^(relevance|newest|closing_soon)$")
    alerts_enabled: bool = True


class SavedSearchOut(SavedSearchInput):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    updated_at: datetime


class ProfileOut(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: str | None
    display_name: str | None
    province: str | None
    city: str | None


class ProfileUpdate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    province: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)


class NotificationPreferenceInput(BaseModel):
    new_tender_matches_enabled: bool = True
    saved_tender_closing_enabled: bool = True
    tender_update_enabled: bool = True
    email_enabled: bool = False
    push_enabled: bool = False
    in_app_enabled: bool = True
    quiet_hours_enabled: bool = True
    quiet_hours_start: time = time(22, 0)
    quiet_hours_end: time = time(7, 0)
    timezone: str = Field(default="Africa/Johannesburg", max_length=64)


class NotificationPreferenceOut(NotificationPreferenceInput):
    model_config = ConfigDict(from_attributes=True)
    id: str
    updated_at: datetime


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    type: str
    title: str
    body: str
    tender_id: str | None
    saved_search_id: str | None
    priority: str
    read_at: datetime | None
    created_at: datetime
    expires_at: datetime | None


class UnreadCount(BaseModel):
    count: int


class PushTokenInput(BaseModel):
    token: str = Field(min_length=20, max_length=4096)
    platform: str = Field(default="ANDROID", pattern="^ANDROID$")
    app_version: str | None = Field(default=None, max_length=50)
    device_identifier: str | None = Field(default=None, max_length=255)


class PushTokenDelete(BaseModel):
    token: str = Field(min_length=20, max_length=4096)


class SavedTenderReminderInput(BaseModel):
    enabled: bool
    reminder_days: list[int] = Field(default=[7, 3, 1, 0], max_length=4)


class SavedTenderReminderOut(SavedTenderReminderInput):
    tender_id: str
