from math import ceil

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.errors import ApiError
from app.models import SavedTender, Tender, User
from app.schemas.common import Page
from app.schemas.domain import (
    SavedTenderItem,
    SavedTenderReminderInput,
    SavedTenderReminderOut,
    TenderCard,
    TenderIdsRequest,
    TenderSavedState,
)

router = APIRouter(tags=["saved tenders"])


@router.post("/tenders/{tender_id}/save", response_model=TenderSavedState, status_code=201)
def save_tender(
    tender_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    if not db.get(Tender, tender_id):
        raise ApiError(404, "TENDER_NOT_FOUND", "Tender not found")
    existing = db.scalar(
        select(SavedTender).where(
            SavedTender.user_id == user.id, SavedTender.tender_id == tender_id
        )
    )
    if not existing:
        db.add(SavedTender(user_id=user.id, tender_id=tender_id))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
    return TenderSavedState(tender_id=tender_id, saved=True)


@router.delete("/tenders/{tender_id}/save", status_code=204)
def unsave_tender(
    tender_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    item = db.scalar(
        select(SavedTender).where(
            SavedTender.user_id == user.id, SavedTender.tender_id == tender_id
        )
    )
    if item:
        db.delete(item)
        db.commit()
    return Response(status_code=204)


@router.get("/tenders/{tender_id}/saved", response_model=TenderSavedState)
def saved_state(
    tender_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    if not db.get(Tender, tender_id):
        raise ApiError(404, "TENDER_NOT_FOUND", "Tender not found")
    item = db.scalar(
        select(SavedTender).where(
            SavedTender.user_id == user.id, SavedTender.tender_id == tender_id
        )
    )
    return TenderSavedState(
        tender_id=tender_id,
        saved=item is not None,
        closing_reminders_enabled=item.closing_reminders_enabled if item else None,
        reminder_days=item.reminder_days if item else None,
    )


@router.post("/users/me/saved-tender-status", response_model=list[TenderSavedState])
def saved_states(
    data: TenderIdsRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    items = {
        item.tender_id: item
        for item in db.scalars(
            select(SavedTender).where(
                SavedTender.user_id == user.id, SavedTender.tender_id.in_(data.tender_ids)
            )
        )
    }
    return [
        TenderSavedState(
            tender_id=x,
            saved=x in items,
            closing_reminders_enabled=items[x].closing_reminders_enabled if x in items else None,
            reminder_days=items[x].reminder_days if x in items else None,
        )
        for x in data.tender_ids
    ]


@router.put("/tenders/{tender_id}/reminders", response_model=SavedTenderReminderOut)
def set_reminders(
    tender_id: str,
    data: SavedTenderReminderInput,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = db.scalar(
        select(SavedTender).where(
            SavedTender.user_id == user.id, SavedTender.tender_id == tender_id
        )
    )
    if not item:
        raise ApiError(
            404, "SAVED_TENDER_NOT_FOUND", "Save the tender before configuring reminders"
        )
    days = sorted(set(data.reminder_days), reverse=True)
    if any(day not in {0, 1, 3, 7} for day in days):
        raise ApiError(422, "INVALID_REMINDER_DAYS", "Supported reminder days are 7, 3, 1 and 0")
    item.closing_reminders_enabled = data.enabled
    item.reminder_days = days
    db.commit()
    return SavedTenderReminderOut(
        tender_id=tender_id,
        enabled=item.closing_reminders_enabled,
        reminder_days=item.reminder_days,
    )


@router.get("/users/me/saved-tenders", response_model=Page[SavedTenderItem])
def list_saved(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    base = (
        select(SavedTender, Tender)
        .join(Tender, Tender.id == SavedTender.tender_id)
        .where(SavedTender.user_id == user.id)
    )
    total = (
        db.scalar(
            select(func.count()).select_from(SavedTender).where(SavedTender.user_id == user.id)
        )
        or 0
    )
    rows = db.execute(
        base.order_by(SavedTender.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    items = [
        SavedTenderItem(saved_at=s.created_at, tender=TenderCard.model_validate(t)) for s, t in rows
    ]
    return Page(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=ceil(total / page_size) if total else 0,
    )
