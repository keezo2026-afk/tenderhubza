from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.phase5 import register_phase5_connectors
from app.models import ConnectorRegistration, ConnectorRun, ConnectorState, Source
from app.services.connector_execution import ConnectorAlreadyRunning, connector_lock
from app.services.connector_scheduler import run_due_connectors
from tests.test_phase1 import FIXTURE, FixtureConnector


class ScheduledFixture(FixtureConnector):
    NAME = "scheduled-fixture"

    def __init__(self):
        super().__init__(FIXTURE[:1])


class FailingFixture(ScheduledFixture):
    async def discover(self):
        raise RuntimeError("controlled failure")


def add(db, slug, name="Source", active=True, status="ACTIVE", registration="ACTIVE", last=None):
    source = Source(
        name=name,
        slug=name.lower().replace(" ", "-"),
        source_type="OTHER",
        organisation=name,
        website_url="https://example.org",
        connector_type=slug,
        active=active,
        status=status,
        polling_interval_minutes=60,
        last_attempted_at=last,
    )
    db.add(source)
    db.flush()
    db.add(
        ConnectorRegistration(
            source_id=source.id,
            name=name,
            slug=slug,
            version="1.0.0",
            connector_type="HTML",
            capabilities={},
            status=registration,
        )
    )
    db.commit()
    return source


@pytest.mark.asyncio
async def test_active_due_executes_and_persists_run(db):
    registry = register_phase5_connectors()
    registry._connectors["scheduled-active"] = ScheduledFixture
    source = add(db, "scheduled-active")
    result = await run_due_connectors(db)
    assert result[0].status == "SUCCESS"
    assert result[0].run_id
    assert db.scalar(select(ConnectorRun).where(ConnectorRun.source_id == source.id))


@pytest.mark.asyncio
async def test_disabled_not_due_and_unknown_are_safe(db):
    registry = register_phase5_connectors()
    registry._connectors["scheduled-disabled"] = ScheduledFixture
    registry._connectors["scheduled-due"] = ScheduledFixture
    add(db, "scheduled-disabled", "Disabled", active=False)
    add(db, "scheduled-due", "Not Due", last=datetime.now(UTC))
    add(db, "unknown-approved", "Unknown")
    results = await run_due_connectors(db)
    assert {r.status for r in results} == {"SKIPPED", "REJECTED"}
    assert not db.scalars(select(ConnectorRun)).all()


@pytest.mark.asyncio
async def test_failure_does_not_stop_next_connector(db):
    registry = register_phase5_connectors()
    registry._connectors["scheduled-fail"] = FailingFixture
    registry._connectors["scheduled-ok"] = ScheduledFixture
    add(db, "scheduled-fail", "A Failure")
    good = add(db, "scheduled-ok", "B Healthy")
    results = await run_due_connectors(db)
    assert [r.status for r in results] == ["FAILED", "SUCCESS"]
    assert (
        db.scalar(select(ConnectorRun).where(ConnectorRun.source_id == good.id)).status == "SUCCESS"
    )


def test_duplicate_concurrent_execution_is_prevented(db):
    with connector_lock(db, "concurrency-test"):
        with Session(db.bind) as other:
            with pytest.raises(ConnectorAlreadyRunning):
                with connector_lock(other, "concurrency-test"):
                    pass


@pytest.mark.asyncio
async def test_high_water_advances_only_success(db):
    registry = register_phase5_connectors()
    registry._connectors["national-treasury-etenders-ocds"] = ScheduledFixture
    source = add(db, "national-treasury-etenders-ocds", "National Test")
    result = await run_due_connectors(db, datetime(2026, 8, 17, tzinfo=UTC))
    assert result[0].status == "SUCCESS"
    assert db.get(ConnectorState, source.id).high_water_date.isoformat() == "2026-08-17"
