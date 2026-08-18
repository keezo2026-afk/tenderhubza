from datetime import UTC, datetime

import pytest

from app.connectors.phase5 import register_phase5_connectors
from app.models import ConnectorState
from app.services.connector_scheduler import run_due_connectors
from tests.test_scheduler_hardening import FailingFixture, add


@pytest.mark.asyncio
async def test_failed_scheduled_run_does_not_advance_high_water(db):
    registry = register_phase5_connectors()
    registry._connectors["national-treasury-etenders-ocds"] = FailingFixture
    source = add(db, "national-treasury-etenders-ocds", "Failed National")
    result = await run_due_connectors(db, datetime(2026, 8, 17, tzinfo=UTC))
    assert result[0].status == "FAILED"
    assert db.get(ConnectorState, source.id) is None
