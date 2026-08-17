from datetime import UTC, datetime
from math import ceil
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.errors import ApiError
from app.models import DeviceToken, Notification, NotificationPreference, User
from app.schemas.common import Page
from app.schemas.domain import (
    NotificationOut,
    NotificationPreferenceInput,
    NotificationPreferenceOut,
    PushTokenDelete,
    PushTokenInput,
    UnreadCount,
)

router = APIRouter(tags=["notifications"])


def preferences(db, user):
    item = db.scalar(
        select(NotificationPreference).where(NotificationPreference.user_id == user.id)
    )
    if not item:
        item = NotificationPreference(user_id=user.id)
        db.add(item)
        db.commit()
        db.refresh(item)
    return item


@router.get("/users/me/notification-preferences", response_model=NotificationPreferenceOut)
def get_preferences(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return preferences(db, user)


@router.put("/users/me/notification-preferences", response_model=NotificationPreferenceOut)
def put_preferences(
    data: NotificationPreferenceInput,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        ZoneInfo(data.timezone)
    except ZoneInfoNotFoundError:
        raise ApiError(422, "INVALID_TIMEZONE", "Timezone is not recognized")
    item = preferences(db, user)
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.get("/notifications", response_model=Page[NotificationOut])
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    where = (Notification.user_id == user.id,)
    total = db.scalar(select(func.count()).select_from(Notification).where(*where)) or 0
    items = list(
        db.scalars(
            select(Notification)
            .where(*where)
            .order_by(Notification.created_at.desc())
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


@router.get("/notifications/unread-count", response_model=UnreadCount)
def unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return UnreadCount(
        count=db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user.id, Notification.read_at.is_(None))
        )
        or 0
    )


def owned(db, user, id):
    item = db.scalar(
        select(Notification).where(Notification.id == id, Notification.user_id == user.id)
    )
    if not item:
        raise ApiError(404, "NOTIFICATION_NOT_FOUND", "Notification not found")
    return item


@router.post("/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    item = owned(db, user, notification_id)
    if not item.read_at:
        item.read_at = datetime.now(UTC)
        db.commit()
        db.refresh(item)
    return item


@router.post("/notifications/read-all", status_code=204)
def read_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.read_at.is_(None))
        .values(read_at=datetime.now(UTC))
    )
    db.commit()
    return Response(status_code=204)


@router.post("/devices/push-token", status_code=204)
def register_device(
    data: PushTokenInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    item = db.scalar(select(DeviceToken).where(DeviceToken.token == data.token))
    if item:
        item.user_id = user.id
        item.active = True
        item.last_seen_at = datetime.now(UTC)
        item.app_version = data.app_version
        item.device_identifier = data.device_identifier
    else:
        db.add(DeviceToken(user_id=user.id, **data.model_dump()))
    db.commit()
    return Response(status_code=204)


@router.delete("/devices/push-token", status_code=204)
def unregister_device(
    data: PushTokenDelete, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    item = db.scalar(
        select(DeviceToken).where(DeviceToken.token == data.token, DeviceToken.user_id == user.id)
    )
    if item:
        item.active = False
        db.commit()
    return Response(status_code=204)
