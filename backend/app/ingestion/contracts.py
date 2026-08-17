from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any


class ProcessingStage(str, Enum):
    DISCOVERY = "DISCOVERY"
    RAW = "RAW"
    PARSING = "PARSING"
    NORMALIZATION = "NORMALIZATION"
    VALIDATION = "VALIDATION"
    DEDUPLICATION = "DEDUPLICATION"
    PERSISTENCE = "DATABASE"
    INDEXING = "SEARCH_INDEX"


@dataclass(frozen=True)
class DiscoveredItem:
    source_identifier: str
    url: str
    release_id: str | None = None


@dataclass(frozen=True)
class RawPayload:
    source_identifier: str
    source_url: str
    payload: dict[str, Any]
    ingested_at: datetime
    connector_version: str
    http_status: int = 200
    content_type: str | None = None
    request_url: str | None = None
    checksum: str | None = None
    source_release_id: str | None = None


@dataclass(frozen=True)
class DocumentReference:
    name: str
    url: str
    media_type: str | None = None
    source_id: str | None = None


@dataclass(frozen=True)
class NormalizedTender:
    source_reference: str
    title: str
    organisation: str
    source_url: str
    description: str | None = None
    reference_number: str | None = None
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
    status: str = "OPEN"
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    source_release_id: str | None = None
    ocds_identifier: str | None = None
    payload_hash: str | None = None
    documents: list[DocumentReference] = field(default_factory=list)
    province_code: str | None = None
    district_code: str | None = None
    municipality_code: str | None = None


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PipelineResult:
    source_identifier: str
    success: bool
    stage: ProcessingStage
    tender_id: str | None = None
    action: str | None = None
    errors: list[str] = field(default_factory=list)
