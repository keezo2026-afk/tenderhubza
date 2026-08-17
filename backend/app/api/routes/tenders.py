from datetime import date
from decimal import Decimal
from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.core.database import get_db
from app.core.errors import ApiError
from app.models import Source, Tender, TenderDocument, User
from app.schemas.common import Page
from app.schemas.domain import (
    HomeResponse,
    SourceAttribution,
    TenderCard,
    TenderCreate,
    TenderDetail,
    TenderOut,
)
from app.search.postgres import TenderSearch

router = APIRouter(prefix="/tenders", tags=["tenders"])
search = TenderSearch()


def _filters(
    query,
    province_id,
    district_id,
    municipality_id,
    category,
    tender_type,
    status,
    closing_from,
    closing_to,
    issue_from,
    issue_to,
    min_value,
    max_value,
    organisation,
):
    for value, column in [
        (province_id, Tender.province_id),
        (district_id, Tender.district_id),
        (municipality_id, Tender.municipality_id),
        (category, Tender.category),
        (tender_type, Tender.tender_type),
        (status, Tender.status),
        (organisation, Tender.organisation),
    ]:
        if value:
            query = query.where(column == value)
    for value, column, op in [
        (closing_from, Tender.closing_date, ">="),
        (closing_to, Tender.closing_date, "<="),
        (issue_from, Tender.issue_date, ">="),
        (issue_to, Tender.issue_date, "<="),
        (min_value, Tender.estimated_value, ">="),
        (max_value, Tender.estimated_value, "<="),
    ]:
        if value is not None:
            query = query.where(column >= value if op == ">=" else column <= value)
    if not status:
        query = query.where(
            Tender.status == "OPEN",
            or_(Tender.closing_date.is_(None), Tender.closing_date >= date.today()),
        )
    return query


@router.get("", response_model=Page[TenderCard])
def list_tenders(
    q: str | None = Query(None, max_length=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    province_id: str | None = None,
    district_id: str | None = None,
    municipality_id: str | None = None,
    category: str | None = None,
    tender_type: str | None = None,
    status: str | None = None,
    closing_from: date | None = None,
    closing_to: date | None = None,
    issue_from: date | None = None,
    issue_to: date | None = None,
    min_value: Decimal | None = None,
    max_value: Decimal | None = None,
    organisation: str | None = None,
    sort: str = Query("relevance", pattern="^(relevance|newest|closing_soon)$"),
    db: Session = Depends(get_db),
):
    base = _filters(
        select(Tender),
        province_id,
        district_id,
        municipality_id,
        category,
        tender_type,
        status,
        closing_from,
        closing_to,
        issue_from,
        issue_to,
        min_value,
        max_value,
        organisation,
    )
    base, rank = search.apply(base, q, db.bind.dialect.name)
    count = select(func.count()).select_from(base.order_by(None).subquery())
    if sort == "newest":
        base = base.order_by(
            Tender.issue_date.desc().nullslast(), Tender.created_at.desc(), Tender.id
        )
    elif sort == "closing_soon":
        base = base.order_by(
            Tender.closing_date.asc().nullslast(),
            Tender.issue_date.desc().nullslast(),
            Tender.id,
        )
    elif rank is not None:
        base = base.order_by(rank.desc(), Tender.closing_date.asc().nullslast(), Tender.id)
    else:
        base = base.order_by(
            Tender.closing_date.asc().nullslast(),
            Tender.issue_date.desc().nullslast(),
            Tender.id,
        )
    total = db.scalar(count) or 0
    items = list(db.scalars(base.offset((page - 1) * page_size).limit(page_size)).all())
    return Page(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=ceil(total / page_size) if total else 0,
    )


@router.get("/home", response_model=HomeResponse)
def home(db: Session = Depends(get_db)):
    current = (
        Tender.status == "OPEN",
        or_(Tender.closing_date.is_(None), Tender.closing_date >= date.today()),
    )
    latest = list(
        db.scalars(
            select(Tender).where(*current).order_by(Tender.issue_date.desc().nullslast()).limit(10)
        )
    )
    closing = list(
        db.scalars(
            select(Tender)
            .where(*current, Tender.closing_date.is_not(None))
            .order_by(Tender.closing_date)
            .limit(10)
        )
    )
    recent = list(
        db.scalars(select(Tender).where(*current).order_by(Tender.ingested_at.desc()).limit(10))
    )
    return HomeResponse(latest=latest, closing_soon=closing, recently_added=recent)


@router.get("/{tender_id}", response_model=TenderDetail)
def get_tender(tender_id: str, db: Session = Depends(get_db)):
    item = db.get(Tender, tender_id)
    if not item:
        raise ApiError(404, "TENDER_NOT_FOUND", "Tender not found")
    source = db.get(Source, item.source_id)
    docs = list(db.scalars(select(TenderDocument).where(TenderDocument.tender_id == item.id)))
    data = TenderOut.model_validate(item).model_dump()
    return TenderDetail(
        **data,
        source_release_id=item.source_release_id,
        ocds_identifier=item.ocds_identifier,
        ingested_at=item.ingested_at,
        documents=docs,
        source=SourceAttribution(
            id=source.id,
            name=source.name,
            organisation=source.organisation,
            website_url=source.website_url,
        ),
    )


@router.post("", response_model=TenderOut, status_code=201, include_in_schema=False)
def create_tender(
    data: TenderCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    item = Tender(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
