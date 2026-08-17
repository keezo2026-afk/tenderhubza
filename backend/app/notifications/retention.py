"""Explicit, scheduled notification retention policy."""

from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import delete, or_
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Notification

log = structlog.get_logger()


class NotificationRetentionService:
    """Deletes only read notifications that exceed the configured retention policy."""

    def __init__(self, db: Session):
        self.db = db

    def cleanup(self, now: datetime | None = None) -> int:
        settings = get_settings()
        now = now or datetime.now(UTC)
        cutoff = now - timedelta(days=settings.notification_read_retention_days)
        result = self.db.execute(
            delete(Notification).where(
                Notification.read_at.is_not(None),
                or_(Notification.read_at < cutoff, Notification.expires_at < now),
            )
        )
        count = result.rowcount or 0
        self.db.commit()
        log.info(
            "notification_retention_completed",
            deleted_count=count,
            retention_days=settings.notification_read_retention_days,
        )
        return count
