from datetime import date, timedelta

from sqlalchemy import func, select

from app.core.security import hash_password
from app.models import Notification, SavedSearch, SavedTender, Source, Tender, User
from app.notifications.service import NotificationService


def test_phase3_idempotent_acceptance_scenario(db):
    today = date(2026, 8, 17)
    user = User(
        email="acceptance@example.co.za",
        password_hash=hash_password("StrongPass123!"),
        first_name="Acceptance",
        last_name="User",
    )
    source = Source(
        name="Phase 3 acceptance source",
        source_type="OTHER",
        organisation="Test",
        website_url="https://example.org",
        connector_type="P3_ACCEPTANCE",
        polling_frequency="manual",
    )
    db.add_all([user, source])
    db.flush()
    search = SavedSearch(
        user_id=user.id,
        name="KwaZulu-Natal Construction",
        query="construction",
        filters={"category": "Construction", "status": "OPEN"},
        sort="relevance",
        alerts_enabled=True,
    )
    tender = Tender(
        source_id=source.id,
        source_reference="p3-acceptance",
        title="Construction of municipal offices",
        organisation="Municipality",
        province="KwaZulu-Natal",
        category="Construction",
        status="OPEN",
        source_url="https://example.org/tender",
        closing_date=today + timedelta(days=1),
    )
    db.add_all([search, tender])
    db.commit()
    service = NotificationService(db)
    assert service.match_new_tender(tender) == 1
    db.commit()
    assert service.match_new_tender(tender) == 0
    db.commit()
    db.add(SavedTender(user_id=user.id, tender_id=tender.id))
    db.commit()
    assert service.create_closing_reminders(today) == 1
    db.commit()
    assert service.create_closing_reminders(today) == 0
    db.commit()
    tender.closing_date = today + timedelta(days=4)
    db.commit()
    changes = {"closing_date": {"from": "2026-08-18", "to": "2026-08-21"}}
    assert service.notify_update(tender, "acceptance-version", changes) == 1
    db.commit()
    assert service.notify_update(tender, "acceptance-version", changes) == 0
    db.commit()
    assert db.scalar(select(func.count()).select_from(Notification)) == 3
