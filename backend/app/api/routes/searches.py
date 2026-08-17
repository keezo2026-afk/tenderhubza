from math import ceil

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.errors import ApiError
from app.models import SavedSearch, User
from app.schemas.common import Page
from app.schemas.domain import SavedSearchInput, SavedSearchOut

router = APIRouter(prefix="/searches", tags=["saved searches"])


def owned(db, user, id):
    item = db.scalar(
        select(SavedSearch).where(SavedSearch.id == id, SavedSearch.user_id == user.id)
    )
    if not item:
        raise ApiError(404, "SAVED_SEARCH_NOT_FOUND", "Saved search not found")
    return item


@router.post("", response_model=SavedSearchOut, status_code=201)
def create(
    data: SavedSearchInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    item = SavedSearch(user_id=user.id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("", response_model=Page[SavedSearchOut])
def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    total = (
        db.scalar(
            select(func.count()).select_from(SavedSearch).where(SavedSearch.user_id == user.id)
        )
        or 0
    )
    items = list(
        db.scalars(
            select(SavedSearch)
            .where(SavedSearch.user_id == user.id)
            .order_by(SavedSearch.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return Page(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=ceil(total / page_size) if total else 0,
    )


@router.get("/{search_id}", response_model=SavedSearchOut)
def get(search_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return owned(db, user, search_id)


@router.put("/{search_id}", response_model=SavedSearchOut)
def update(
    search_id: str,
    data: SavedSearchInput,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = owned(db, user, search_id)
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{search_id}", status_code=204)
def delete(search_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.delete(owned(db, user, search_id))
    db.commit()
    return Response(status_code=204)
