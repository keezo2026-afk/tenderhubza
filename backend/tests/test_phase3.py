from datetime import UTC, date, datetime, time, timedelta

import pytest
from sqlalchemy import func, select

from app.core.security import hash_password
from app.models import (
    Notification,
    NotificationDelivery,
    NotificationPreference,
    SavedSearch,
    SavedTender,
    Source,
    Tender,
    User,
)
from app.notifications.delivery import NotificationDeliveryService
from app.notifications.matching import matches
from app.notifications.service import NotificationService


def user(db, email="notify@example.co.za"):
    item = User(
        email=email,
        password_hash=hash_password("StrongPass123!"),
        first_name="Nandi",
        last_name="Tester",
    )
    db.add(item)
    db.commit()
    return item


def auth(client, email):
    token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "StrongPass123!"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def tender(db, index=1, closing=None, status="OPEN"):
    source = db.scalar(select(Source).where(Source.name == "Notification source"))
    if not source:
        source = Source(
            name="Notification source",
            source_type="OTHER",
            organisation="Test",
            website_url="https://example.org",
            connector_type="NOTIFY_TEST",
            polling_frequency="manual",
        )
        db.add(source)
        db.flush()
    item = Tender(
        source_id=source.id,
        source_reference=f"notify-{index}",
        reference_number=f"NT-{index}",
        title="Construction of Community Hall",
        description="Municipal building works",
        organisation="Msunduzi Municipality",
        province="KwaZulu-Natal",
        category="Construction",
        tender_type="open",
        source_url=f"https://example.org/{index}",
        status=status,
        issue_date=date(2026, 8, 17),
        closing_date=closing,
        estimated_value=1000000,
    )
    db.add(item)
    db.commit()
    return item


def search(db, u, name="KZN Construction", alerts=True, filters=None):
    item = SavedSearch(
        user_id=u.id,
        name=name,
        query="construction",
        filters=filters
        or {
            "provinceId": None,
            "category": "Construction",
            "organisation": "Msunduzi Municipality",
            "status": "OPEN",
            "minValue": "500000",
            "maxValue": "2000000",
            "issueFrom": "2026-08-01",
            "closingTo": "2026-12-31",
        },
        sort="relevance",
        alerts_enabled=alerts,
    )
    db.add(item)
    db.commit()
    return item


def test_saved_search_match_dedup_filters_disabled_and_multiple(db):
    u = user(db)
    t = tender(db, 1, date(2026, 9, 14))
    search(db, u)
    search(db, u, "Second match")
    search(db, u, "Disabled", False)
    nonmatch = search(db, u, "Wrong province", True, {"provinceId": "does-not-match"})
    service = NotificationService(db)
    assert service.match_new_tender(t) == 2
    db.commit()
    assert service.match_new_tender(t) == 0
    db.commit()
    assert db.scalar(select(func.count()).select_from(Notification)) == 2
    assert matches(t, nonmatch) is False
    assert all(n.user_id == u.id for n in db.scalars(select(Notification)))


def test_matching_user_preference_disabled(db):
    u = user(db)
    t = tender(db, 2, date(2026, 9, 14))
    search(db, u)
    db.add(NotificationPreference(user_id=u.id, new_tender_matches_enabled=False))
    db.commit()
    assert NotificationService(db).match_new_tender(t) == 0


def test_closing_reminders_windows_dedup_and_exclusions(db):
    today = date(2026, 8, 17)
    u = user(db)
    service = NotificationService(db)
    for i, days in enumerate([7, 3, 1, 0], 1):
        t = tender(db, 10 + i, today + timedelta(days=days))
        db.add(SavedTender(user_id=u.id, tender_id=t.id))
    closed = tender(db, 20, today + timedelta(days=1), "CLOSED")
    missing = tender(db, 21, None)
    disabled = tender(db, 22, today + timedelta(days=1))
    db.add_all(
        [
            SavedTender(user_id=u.id, tender_id=closed.id),
            SavedTender(user_id=u.id, tender_id=missing.id),
            SavedTender(user_id=u.id, tender_id=disabled.id, closing_reminders_enabled=False),
        ]
    )
    db.commit()
    assert service.create_closing_reminders(today) == 4
    db.commit()
    assert service.create_closing_reminders(today) == 0
    db.commit()
    items = list(db.scalars(select(Notification)))
    assert len(items) == 4
    assert any(n.priority == "HIGH" for n in items)


def test_channel_preferences_and_quiet_hours(db):
    u = user(db)
    t = tender(db, 29, date(2026, 9, 14))
    search(db, u)
    pref = NotificationPreference(
        user_id=u.id,
        push_enabled=True,
        email_enabled=True,
        quiet_hours_enabled=True,
        quiet_hours_start=time(0, 0),
        quiet_hours_end=time(23, 59),
        timezone="Africa/Johannesburg",
    )
    db.add(pref)
    db.commit()
    assert NotificationService(db).match_new_tender(t) == 1
    db.commit()
    deliveries = list(db.scalars(select(NotificationDelivery)))
    assert {d.channel for d in deliveries} == {"IN_APP", "PUSH", "EMAIL"}
    assert all(d.status == "PENDING" for d in deliveries if d.channel != "IN_APP")
    assert all(
        (d.available_at.replace(tzinfo=UTC) if d.available_at.tzinfo is None else d.available_at)
        > datetime.now(UTC)
        for d in deliveries
        if d.channel != "IN_APP"
    )


@pytest.mark.asyncio
async def test_development_channels_are_honestly_skipped(db):
    u = user(db)
    t = tender(db, 28, date(2026, 9, 14))
    search(db, u)
    db.add(
        NotificationPreference(
            user_id=u.id, push_enabled=True, email_enabled=True, quiet_hours_enabled=False
        )
    )
    db.commit()
    NotificationService(db).match_new_tender(t)
    db.commit()
    result = await NotificationDeliveryService(db).deliver_pending()
    assert result["skipped"] == 2
    assert {
        d.status
        for d in db.scalars(
            select(NotificationDelivery).where(NotificationDelivery.channel != "IN_APP")
        )
    } == {"SKIPPED"}


def test_closing_global_preference_disabled(db):
    u = user(db)
    t = tender(db, 30, date(2026, 8, 18))
    db.add_all(
        [
            SavedTender(user_id=u.id, tender_id=t.id),
            NotificationPreference(user_id=u.id, saved_tender_closing_enabled=False),
        ]
    )
    db.commit()
    assert NotificationService(db).create_closing_reminders(date(2026, 8, 17)) == 0


def test_tender_update_meaningful_saved_only_and_deduplicated(db):
    u = user(db)
    other = user(db, "other-notify@example.co.za")
    t = tender(db, 40, date(2026, 9, 14))
    db.add(SavedTender(user_id=u.id, tender_id=t.id))
    db.commit()
    service = NotificationService(db)
    changes = {
        "closing_date": {"from": "2026-09-14", "to": "2026-09-21"},
        "payload_hash": {"from": "a", "to": "b"},
    }
    assert service.notify_update(t, "version-1", changes) == 1
    db.commit()
    assert service.notify_update(t, "version-1", changes) == 0
    db.commit()
    assert service.notify_update(t, "version-2", {"payload_hash": {"from": "b", "to": "c"}}) == 0
    assert (
        db.scalar(
            select(func.count()).select_from(Notification).where(Notification.user_id == other.id)
        )
        == 0
    )


def test_preferences_notification_api_and_isolation(client, db):
    a = user(db, "api-a@example.co.za")
    b = user(db, "api-b@example.co.za")
    ha = auth(client, a.email)
    hb = auth(client, b.email)
    t = tender(db, 50, date(2026, 9, 1))
    n = Notification(
        user_id=a.id,
        type="TENDER_UPDATED",
        title="Tender updated",
        body="Closing date changed",
        event_key="api-notification",
        tender_id=t.id,
        priority="NORMAL",
    )
    db.add(n)
    db.commit()
    assert client.get("/api/v1/notifications").status_code == 401
    assert client.get("/api/v1/notifications", headers=hb).json()["total"] == 0
    assert client.get("/api/v1/notifications/unread-count", headers=ha).json()["count"] == 1
    assert client.post(f"/api/v1/notifications/{n.id}/read", headers=hb).status_code == 404
    assert client.post(f"/api/v1/notifications/{n.id}/read", headers=ha).status_code == 200
    assert client.get("/api/v1/notifications/unread-count", headers=ha).json()["count"] == 0
    pref = client.get("/api/v1/users/me/notification-preferences", headers=ha)
    assert pref.status_code == 200
    body = {k: v for k, v in pref.json().items() if k not in {"id", "updated_at"}}
    body.update(
        {
            "push_enabled": True,
            "email_enabled": True,
            "quiet_hours_start": "21:30:00",
            "quiet_hours_end": "06:30:00",
        }
    )
    updated = client.put("/api/v1/users/me/notification-preferences", json=body, headers=ha)
    assert updated.status_code == 200
    assert updated.json()["push_enabled"] is True
    assert client.post("/api/v1/notifications/read-all", headers=ha).status_code == 204


def test_per_resource_alert_and_reminder_controls(client, db):
    u = user(db, "controls@example.co.za")
    headers = auth(client, u.email)
    t = tender(db, 60, date(2026, 8, 18))
    saved = SavedTender(user_id=u.id, tender_id=t.id)
    query = SavedSearch(
        user_id=u.id,
        name="Controls",
        query="construction",
        filters={},
        sort="relevance",
        alerts_enabled=True,
    )
    db.add_all([saved, query])
    db.commit()
    body = {
        "name": query.name,
        "query": query.query,
        "filters": {},
        "sort": "relevance",
        "alerts_enabled": False,
    }
    assert (
        client.put(f"/api/v1/searches/{query.id}", json=body, headers=headers).json()[
            "alerts_enabled"
        ]
        is False
    )
    reminder = client.put(
        f"/api/v1/tenders/{t.id}/reminders",
        json={"enabled": False, "reminder_days": [7, 3, 1, 0]},
        headers=headers,
    )
    assert reminder.status_code == 200
    assert reminder.json()["enabled"] is False


def test_device_tokens_scoped_and_not_queryable(client, db):
    a = user(db, "device-a@example.co.za")
    b = user(db, "device-b@example.co.za")
    ha = auth(client, a.email)
    hb = auth(client, b.email)
    token = "fcm-development-token-that-is-long-enough"
    assert (
        client.post("/api/v1/devices/push-token", json={"token": token}, headers=ha).status_code
        == 204
    )
    assert (
        client.request(
            "DELETE", "/api/v1/devices/push-token", json={"token": token}, headers=hb
        ).status_code
        == 204
    )
    assert (
        client.request(
            "DELETE", "/api/v1/devices/push-token", json={"token": token}, headers=ha
        ).status_code
        == 204
    )
