from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.core.database import get_db
from app.core.errors import ApiError
from app.models import (
    ConnectorRun,
    Municipality,
    MunicipalitySourceCoverage,
    Source,
    SourceDiscovery,
    User,
)
from app.schemas.common import Page
from app.schemas.sources import AdminSourceInput, AdminSourceOut, SourceDiscoveryInput
from app.sources.health import health_for
from app.sources.security import validate_source_url

router = APIRouter(prefix="/admin", tags=["admin sources"])
ALLOWED_TYPES = {
    "NATIONAL",
    "PROVINCIAL",
    "MUNICIPAL",
    "MUNICIPAL_ENTITY",
    "SOE",
    "PUBLIC_ENTITY",
    "UNIVERSITY",
    "PUBLIC_INSTITUTION",
    "OTHER",
}
STATUSES = {"DISCOVERED", "REVIEW", "APPROVED", "ACTIVE", "PAUSED", "FAILING", "BLOCKED", "RETIRED"}


def validate(data):
    if data.source_type not in ALLOWED_TYPES or data.status not in STATUSES:
        raise ApiError(422, "INVALID_SOURCE", "Unsupported source type or status")
    for value in [data.website_url, data.procurement_url, data.tender_url, data.api_url]:
        validate_source_url(value)


def owned(db, id):
    item = db.get(Source, id)
    if not item:
        raise ApiError(404, "SOURCE_NOT_FOUND", "Source not found")
    return item


def output(item):
    return AdminSourceOut(
        id=item.id,
        name=item.name,
        slug=item.slug,
        source_type=item.source_type,
        organisation=item.organisation,
        website_url=item.website_url,
        procurement_url=item.procurement_url,
        tender_url=item.tender_url,
        api_url=item.api_url,
        province_id=item.province_id,
        district_id=item.district_id,
        municipality_id=item.municipality_id,
        connector_type=item.connector_type,
        priority=item.priority,
        polling_interval_minutes=item.polling_interval_minutes,
        status=item.status,
        active=item.active,
        consecutive_failures=item.consecutive_failures,
        last_attempted_at=item.last_attempted_at,
        last_successful_run=item.last_successful_run,
        last_failed_run=item.last_failed_run,
        last_tender_discovered_at=item.last_tender_discovered_at,
        last_error_category=item.last_error_category,
        last_error_message=item.last_error,
    )


@router.get("/sources", response_model=Page[AdminSourceOut])
def sources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    total = db.scalar(select(func.count()).select_from(Source)) or 0
    items = list(
        db.scalars(
            select(Source)
            .order_by(Source.priority, Source.name)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return Page(
        items=[output(x) for x in items],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=ceil(total / page_size) if total else 0,
    )


@router.get("/sources/{source_id}", response_model=AdminSourceOut)
def get_source(source_id: str, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return output(owned(db, source_id))


@router.post("/sources", response_model=AdminSourceOut, status_code=201)
def create_source(
    data: AdminSourceInput,
    discovery: SourceDiscoveryInput,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    validate(data)
    if data.status not in {"DISCOVERED", "REVIEW"}:
        raise ApiError(409, "INVALID_TRANSITION", "New sources require review")
    item = Source(
        **data.model_dump(), active=False, polling_frequency=f"{data.polling_interval_minutes}m"
    )
    db.add(item)
    db.flush()
    db.add(
        SourceDiscovery(
            source_id=item.id, **discovery.model_dump(), verification_status=data.status
        )
    )
    db.commit()
    db.refresh(item)
    return output(item)


@router.put("/sources/{source_id}", response_model=AdminSourceOut)
def update_source(
    source_id: str,
    data: AdminSourceInput,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    validate(data)
    item = owned(db, source_id)
    if data.status == "ACTIVE" and item.status not in {"APPROVED", "ACTIVE", "PAUSED", "FAILING"}:
        raise ApiError(409, "INVALID_TRANSITION", "Source must be approved before activation")
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    item.active = data.status == "ACTIVE"
    db.commit()
    db.refresh(item)
    return output(item)


@router.get("/sources/{source_id}/runs")
def source_runs(
    source_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    owned(db, source_id)
    total = (
        db.scalar(
            select(func.count())
            .select_from(ConnectorRun)
            .where(ConnectorRun.source_id == source_id)
        )
        or 0
    )
    items = list(
        db.scalars(
            select(ConnectorRun)
            .where(ConnectorRun.source_id == source_id)
            .order_by(ConnectorRun.started_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": ceil(total / page_size) if total else 0,
    }


@router.get("/sources/{source_id}/health")
def source_health(
    source_id: str, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    item = owned(db, source_id)
    return {
        "source_id": item.id,
        "health": health_for(item),
        "consecutive_failures": item.consecutive_failures,
        "last_success": item.last_successful_run,
        "last_failure": item.last_failed_run,
        "last_error_category": item.last_error_category,
    }


@router.get("/source-coverage")
def coverage(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    total = db.scalar(select(func.count()).select_from(Municipality)) or 0
    identified = (
        db.scalar(
            select(func.count())
            .select_from(MunicipalitySourceCoverage)
            .where(MunicipalitySourceCoverage.source_identified.is_(True))
        )
        or 0
    )
    implemented = (
        db.scalar(
            select(func.count())
            .select_from(MunicipalitySourceCoverage)
            .where(MunicipalitySourceCoverage.connector_implemented.is_(True))
        )
        or 0
    )
    active = (
        db.scalar(
            select(func.count())
            .select_from(MunicipalitySourceCoverage)
            .join(Source, Source.id == MunicipalitySourceCoverage.source_id)
            .where(Source.active.is_(True))
        )
        or 0
    )
    return {
        "total_municipalities": total,
        "source_identified": identified,
        "connector_implemented": implemented,
        "connector_active": active,
        "needs_investigation": total - identified,
    }
