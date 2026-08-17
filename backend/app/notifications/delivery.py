"""Retry-safe notification delivery with per-device push state."""

from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import (
    DeviceToken,
    Notification,
    NotificationDelivery,
    NotificationDeviceDelivery,
    User,
)
from app.notifications.push import (
    DevelopmentPushProvider,
    InvalidPushTokenError,
    push_provider,
)
from app.services.email import DevelopmentEmailProvider, email_provider

log = structlog.get_logger()


class NotificationDeliveryService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    async def deliver_pending(self, limit: int = 100) -> dict[str, int]:
        deliveries = list(
            self.db.scalars(
                select(NotificationDelivery)
                .where(
                    NotificationDelivery.status == "PENDING",
                    NotificationDelivery.available_at <= datetime.now(UTC),
                )
                .order_by(NotificationDelivery.available_at)
                .limit(limit)
            )
        )
        result = {"submitted": 0, "failed": 0, "skipped": 0, "pending": 0}
        for delivery in deliveries:
            notification = self.db.get(Notification, delivery.notification_id)
            delivery.attempt_count += 1
            delivery.attempted_at = datetime.now(UTC)
            try:
                if delivery.channel == "PUSH":
                    await self._push(delivery, notification)
                elif delivery.channel == "EMAIL":
                    await self._email(delivery, notification)
                else:
                    delivery.status = "SKIPPED"
                    delivery.error_code = "UNSUPPORTED_CHANNEL"
            except Exception as exc:
                delivery.status = "PENDING" if delivery.attempt_count < 3 else "FAILED"
                delivery.available_at = datetime.now(UTC) + timedelta(
                    minutes=5 * delivery.attempt_count
                )
                delivery.error_code = type(exc).__name__
                delivery.error_message = str(exc)[:500]
                log.warning(
                    "notification_delivery_failed",
                    notification_id=notification.id if notification else None,
                    channel=delivery.channel,
                    error_type=type(exc).__name__,
                )
            result[delivery.status.lower()] += 1
            self.db.commit()
        return result

    async def _push(self, delivery: NotificationDelivery, notification: Notification) -> None:
        provider = push_provider(self.settings)
        if isinstance(provider, DevelopmentPushProvider):
            delivery.status = "SKIPPED"
            delivery.error_code = "DEVELOPMENT_PROVIDER"
            log.info("push_skipped", notification_id=notification.id, reason="development_provider")
            return
        devices = list(
            self.db.scalars(
                select(DeviceToken).where(
                    DeviceToken.user_id == notification.user_id,
                    DeviceToken.active.is_(True),
                )
            )
        )
        if not devices:
            delivery.status = "SKIPPED"
            delivery.error_code = "NO_ACTIVE_DEVICE"
            return
        states: list[NotificationDeviceDelivery] = []
        for device in devices:
            state = self.db.scalar(
                select(NotificationDeviceDelivery).where(
                    NotificationDeviceDelivery.notification_id == notification.id,
                    NotificationDeviceDelivery.device_token_id == device.id,
                )
            )
            if not state:
                state = NotificationDeviceDelivery(
                    notification_id=notification.id,
                    device_token_id=device.id,
                    available_at=delivery.available_at,
                )
                self.db.add(state)
                self.db.flush()
            states.append(state)
        for state in states:
            if state.status in {"SUBMITTED", "DELIVERED", "SKIPPED"}:
                continue
            if self._aware(state.available_at) > datetime.now(UTC):
                continue
            device = self.db.get(DeviceToken, state.device_token_id)
            if not device or not device.active:
                state.status = "SKIPPED"
                state.error_code = "INACTIVE_DEVICE"
                continue
            state.attempt_count += 1
            state.attempted_at = datetime.now(UTC)
            try:
                state.provider_message_id = await provider.send(
                    device.token,
                    {
                        "notification_id": notification.id,
                        "tender_id": notification.tender_id or "",
                        "type": notification.type,
                        "title": notification.title,
                        "body": notification.body,
                    },
                )
                state.status = "SUBMITTED"
                state.submitted_at = datetime.now(UTC)
                state.error_code = None
                state.error_message = None
                log.info(
                    "push_submitted",
                    notification_id=notification.id,
                    device_delivery_id=state.id,
                )
            except InvalidPushTokenError as exc:
                device.active = False
                state.status = "FAILED"
                state.error_code = "INVALID_TOKEN"
                state.error_message = str(exc)[:500]
                log.warning(
                    "push_token_deactivated",
                    notification_id=notification.id,
                    device_delivery_id=state.id,
                )
            except Exception as exc:
                state.status = "PENDING" if state.attempt_count < 3 else "FAILED"
                state.available_at = datetime.now(UTC) + timedelta(minutes=5 * state.attempt_count)
                state.error_code = type(exc).__name__
                state.error_message = "push provider request failed"
                log.warning(
                    "push_device_failed",
                    notification_id=notification.id,
                    device_delivery_id=state.id,
                    error_type=type(exc).__name__,
                )
        statuses = {state.status for state in states}
        if statuses <= {"SUBMITTED", "DELIVERED"}:
            delivery.status = "SUBMITTED"
            delivery.provider_message_id = None
        elif "PENDING" in statuses:
            delivery.status = "PENDING"
            delivery.available_at = min(
                state.available_at for state in states if state.status == "PENDING"
            )
        elif statuses == {"SKIPPED"}:
            delivery.status = "SKIPPED"
        else:
            delivery.status = "FAILED"

    async def _email(self, delivery: NotificationDelivery, notification: Notification) -> None:
        provider = email_provider(self.settings)
        if isinstance(provider, DevelopmentEmailProvider):
            delivery.status = "SKIPPED"
            delivery.error_code = "DEVELOPMENT_PROVIDER"
            log.info(
                "email_skipped", notification_id=notification.id, reason="development_provider"
            )
            return
        user = self.db.get(User, notification.user_id)
        delivery.provider_message_id = await provider.send_notification(
            user.email, notification.title, notification.body
        )
        delivery.status = "SUBMITTED"
        log.info("email_submitted", notification_id=notification.id)

    @staticmethod
    def _aware(value: datetime) -> datetime:
        return value if value.tzinfo else value.replace(tzinfo=UTC)
