from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.security import hash_password
from app.models import (
    DeviceToken,
    Notification,
    NotificationDelivery,
    NotificationDeviceDelivery,
    User,
)
from app.notifications.delivery import NotificationDeliveryService
from app.notifications.push import InvalidPushTokenError
from app.notifications.retention import NotificationRetentionService


class DeviceAwareProvider:
    def __init__(self, invalid_token=None, transient_token=None):
        self.invalid_token = invalid_token
        self.transient_token = transient_token
        self.calls: list[str] = []
        self.transient_failed = False

    async def send(self, token, data):
        self.calls.append(token)
        if token == self.invalid_token:
            raise InvalidPushTokenError("unregistered")
        if token == self.transient_token and not self.transient_failed:
            self.transient_failed = True
            raise RuntimeError("temporary provider failure")
        return f"provider-{token}"


def setup_delivery(db):
    user = User(
        email="devices@example.co.za",
        password_hash=hash_password("StrongPass123!"),
        first_name="Device",
        last_name="Owner",
    )
    db.add(user)
    db.flush()
    notification = Notification(
        user_id=user.id,
        type="TENDER_UPDATED",
        title="Tender updated",
        body="Closing date changed",
        event_key="device-delivery-test",
        priority="NORMAL",
    )
    db.add(notification)
    db.flush()
    delivery = NotificationDelivery(
        notification_id=notification.id,
        channel="PUSH",
        status="PENDING",
        available_at=datetime.now(UTC),
    )
    first = DeviceToken(user_id=user.id, token="token-a", active=True)
    second = DeviceToken(user_id=user.id, token="token-b", active=True)
    db.add_all([delivery, first, second])
    db.commit()
    return notification, delivery, first, second


@pytest.mark.asyncio
async def test_device_delivery_is_idempotent_and_invalid_token_is_retired(db, monkeypatch):
    notification, delivery, first, second = setup_delivery(db)
    provider = DeviceAwareProvider(invalid_token="token-b")
    monkeypatch.setattr("app.notifications.delivery.push_provider", lambda settings: provider)
    await NotificationDeliveryService(db).deliver_pending()
    states = list(db.scalars(select(NotificationDeviceDelivery)))
    assert {state.status for state in states} == {"SUBMITTED", "FAILED"}
    db.refresh(second)
    assert second.active is False
    assert delivery.status == "FAILED"
    delivery.status = "PENDING"
    delivery.available_at = datetime.now(UTC)
    db.commit()
    await NotificationDeliveryService(db).deliver_pending()
    assert provider.calls.count("token-a") == 1
    assert provider.calls.count("token-b") == 1
    db.refresh(delivery)
    assert delivery.status == "SUBMITTED"


@pytest.mark.asyncio
async def test_transient_device_retry_does_not_resend_successful_device(db, monkeypatch):
    _, delivery, _, second = setup_delivery(db)
    provider = DeviceAwareProvider(transient_token="token-b")
    monkeypatch.setattr("app.notifications.delivery.push_provider", lambda settings: provider)
    await NotificationDeliveryService(db).deliver_pending()
    states = list(db.scalars(select(NotificationDeviceDelivery)))
    pending = next(state for state in states if state.device_token_id == second.id)
    assert pending.status == "PENDING"
    pending.available_at = datetime.now(UTC)
    delivery.available_at = datetime.now(UTC)
    db.commit()
    await NotificationDeliveryService(db).deliver_pending()
    assert provider.calls.count("token-a") == 1
    assert provider.calls.count("token-b") == 2
    assert all(state.status == "SUBMITTED" for state in states)


def test_retention_deletes_only_old_read_notifications(db, monkeypatch):
    user = User(
        email="retention@example.co.za",
        password_hash=hash_password("StrongPass123!"),
        first_name="Retention",
        last_name="Owner",
    )
    db.add(user)
    db.flush()
    old = datetime.now(UTC) - timedelta(days=120)
    notifications = [
        Notification(
            user_id=user.id,
            type="TENDER_UPDATED",
            title="old read",
            body="x",
            event_key="old-read",
            priority="LOW",
            read_at=old,
        ),
        Notification(
            user_id=user.id,
            type="TENDER_UPDATED",
            title="old unread",
            body="x",
            event_key="old-unread",
            priority="LOW",
            created_at=old,
        ),
        Notification(
            user_id=user.id,
            type="TENDER_UPDATED",
            title="recent read",
            body="x",
            event_key="recent-read",
            priority="LOW",
            read_at=datetime.now(UTC),
        ),
    ]
    db.add_all(notifications)
    db.commit()
    assert NotificationRetentionService(db).cleanup() == 1
    remaining = {item.event_key for item in db.scalars(select(Notification))}
    assert remaining == {"old-unread", "recent-read"}
    assert NotificationRetentionService(db).cleanup() == 0
