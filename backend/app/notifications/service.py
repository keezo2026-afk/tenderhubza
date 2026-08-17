from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import structlog
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    Notification,
    NotificationDelivery,
    NotificationPreference,
    SavedTender,
    Tender,
)
from app.notifications.candidates import SavedSearchCandidateRepository
from app.notifications.matching import matches

log = structlog.get_logger()
MEANINGFUL = {
    "closing_date",
    "closing_time",
    "title",
    "description",
    "estimated_value",
    "status",
    "contact_name",
    "contact_email",
    "contact_phone",
    "documents",
}


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def _preference(self, user_id):
        return self.db.scalar(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        )

    def _create(
        self,
        *,
        user_id,
        notification_type,
        title,
        body,
        event_key,
        tender_id=None,
        saved_search_id=None,
        priority="NORMAL",
    ):
        pref = self._preference(user_id)
        in_app = True if pref is None else pref.in_app_enabled
        push = False if pref is None else pref.push_enabled
        email = False if pref is None else pref.email_enabled
        try:
            with self.db.begin_nested():
                notification = Notification(
                    user_id=user_id,
                    type=notification_type,
                    title=title,
                    body=body,
                    event_key=event_key,
                    tender_id=tender_id,
                    saved_search_id=saved_search_id,
                    priority=priority,
                )
                self.db.add(notification)
                self.db.flush()
                if in_app:
                    self.db.add(
                        NotificationDelivery(
                            notification_id=notification.id,
                            channel="IN_APP",
                            status="SUBMITTED",
                            attempted_at=datetime.now(UTC),
                        )
                    )
                available = datetime.now(UTC) if priority == "HIGH" else self._available_at(pref)
                if push:
                    self.db.add(
                        NotificationDelivery(
                            notification_id=notification.id,
                            channel="PUSH",
                            status="PENDING",
                            available_at=available,
                        )
                    )
                if email:
                    self.db.add(
                        NotificationDelivery(
                            notification_id=notification.id,
                            channel="EMAIL",
                            status="PENDING",
                            available_at=available,
                        )
                    )
            log.info(
                "notification_generated",
                notification_id=notification.id,
                notification_type=notification_type,
                tender_id=tender_id,
                priority=priority,
            )
            return notification
        except IntegrityError:
            log.info("notification_deduplicated", notification_type=notification_type)
            return None

    def _available_at(self, pref):
        now = datetime.now(UTC)
        if not pref or not pref.quiet_hours_enabled:
            return now
        zone = ZoneInfo(pref.timezone)
        local = now.astimezone(zone)
        start = pref.quiet_hours_start
        end = pref.quiet_hours_end
        inside = (
            (local.time() >= start or local.time() < end)
            if start > end
            else start <= local.time() < end
        )
        if not inside:
            return now
        next_end = datetime.combine(
            local.date()
            + (timedelta(days=1) if local.time() >= start and start > end else timedelta()),
            end,
            zone,
        )
        return next_end.astimezone(UTC)

    def match_new_tender(self, tender: Tender):
        created = 0
        searches = SavedSearchCandidateRepository(self.db).for_tender(tender)
        for search in searches:
            pref = self._preference(search.user_id)
            if pref and not pref.new_tender_matches_enabled:
                continue
            if matches(tender, search):
                body = (
                    f"{tender.organisation}"
                    + (f" · {tender.province}" if tender.province else "")
                    + (
                        f" · Closes {tender.closing_date.isoformat()}"
                        if tender.closing_date
                        else ""
                    )
                )
                if self._create(
                    user_id=search.user_id,
                    notification_type="NEW_TENDER_MATCH",
                    title=f"New tender: {tender.title}",
                    body=body,
                    event_key=f"match:{search.user_id}:{tender.id}:{search.id}",
                    tender_id=tender.id,
                    saved_search_id=search.id,
                ):
                    created += 1
                    log.info("saved_search_match", saved_search_id=search.id, tender_id=tender.id)
        return created

    def notify_update(self, tender: Tender, version_id: str, changes: dict):
        meaningful = {k: v for k, v in changes.items() if k in MEANINGFUL}
        if not meaningful:
            log.info("notification_skipped", reason="no_meaningful_change", tender_id=tender.id)
            return 0
        labels = {
            "closing_date": "closing date",
            "closing_time": "closing time",
            "estimated_value": "estimated value",
            "contact_name": "contact details",
            "contact_email": "contact details",
            "contact_phone": "contact details",
        }
        description = ", ".join(
            dict.fromkeys(labels.get(k, k.replace("_", " ")) for k in meaningful)
        )
        count = 0
        for saved in self.db.scalars(select(SavedTender).where(SavedTender.tender_id == tender.id)):
            pref = self._preference(saved.user_id)
            if pref and not pref.tender_update_enabled:
                continue
            if self._create(
                user_id=saved.user_id,
                notification_type="TENDER_UPDATED",
                title=f"Tender updated: {tender.title}",
                body=f"Changed: {description}",
                event_key=f"update:{saved.user_id}:{tender.id}:{version_id}",
                tender_id=tender.id,
            ):
                count += 1
        return count

    def create_closing_reminders(self, today: date | None = None):
        today = today or datetime.now(UTC).date()
        created = 0
        rows = self.db.execute(
            select(SavedTender, Tender)
            .join(Tender, Tender.id == SavedTender.tender_id)
            .where(
                SavedTender.closing_reminders_enabled.is_(True),
                Tender.status == "OPEN",
                Tender.closing_date.is_not(None),
                Tender.closing_date >= today,
                Tender.closing_date <= today + timedelta(days=7),
            )
        )
        for saved, tender in rows:
            days = (tender.closing_date - today).days
            if days not in (saved.reminder_days or [7, 3, 1, 0]):
                continue
            pref = self._preference(saved.user_id)
            if pref and not pref.saved_tender_closing_enabled:
                continue
            title = (
                "Tender closes today"
                if days == 0
                else f"Tender closes in {days} day{'s' if days != 1 else ''}"
            ) + f": {tender.title}"
            priority = "HIGH" if days == 0 else "NORMAL"
            if self._create(
                user_id=saved.user_id,
                notification_type="TENDER_CLOSING_SOON",
                title=title,
                body=f"Closing date: {tender.closing_date.isoformat()}",
                event_key=f"closing:{saved.user_id}:{tender.id}:{days}:{tender.closing_date.isoformat()}",
                tender_id=tender.id,
                priority=priority,
            ):
                created += 1
                log.info("closing_reminder", tender_id=tender.id, days=days)
        return created
