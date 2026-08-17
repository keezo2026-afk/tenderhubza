from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.connectors.national.etenders import ETendersConnector
from app.connectors.testing import ConnectorContractHarness
from app.core.security import hash_password
from app.ingestion.engine import IngestionEngine
from app.models import (
    Municipality,
    MunicipalitySourceCoverage,
    Notification,
    SavedSearch,
    Source,
    SourceDiscovery,
    Tender,
    User,
)
from app.sources.health import health_for
from app.sources.registry import ConnectorRegistry
from tests.test_phase1 import FIXTURE, FixtureConnector


def admin_headers(client, db):
    user = User(
        email="phase4-admin@example.co.za",
        password_hash=hash_password("AdminPass123!"),
        first_name="Admin",
        last_name="Four",
        role="ADMIN",
    )
    db.add(user)
    db.commit()
    token = client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": "AdminPass123!"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def payload(status="DISCOVERED"):
    return {
        "data": {
            "name": "Test Municipality Procurement",
            "slug": "test-municipality-procurement",
            "source_type": "MUNICIPAL",
            "organisation": "Test Municipality",
            "website_url": "https://municipality.example.org",
            "procurement_url": "https://municipality.example.org/tenders",
            "connector_type": "TEST_FIXTURE",
            "priority": 4,
            "polling_interval_minutes": 1440,
            "status": status,
        },
        "discovery": {
            "discovered_by": "Acceptance test",
            "discovery_method": "OFFICIAL_WEBSITE_RESEARCH",
            "evidence_url": "https://municipality.example.org/tenders",
            "notes": "Fixture source",
        },
    }


def test_admin_source_lifecycle_authorization_and_ssrf(client, db):
    headers = admin_headers(client, db)
    assert client.get("/api/v1/admin/sources").status_code == 401
    created = client.post("/api/v1/admin/sources", json=payload(), headers=headers)
    assert created.status_code == 201
    item = created.json()
    identifier = item["id"]
    assert item["active"] is False
    direct = payload("ACTIVE")["data"]
    assert (
        client.put(f"/api/v1/admin/sources/{identifier}", json=direct, headers=headers).status_code
        == 409
    )
    approved = {**direct, "status": "APPROVED"}
    assert (
        client.put(
            f"/api/v1/admin/sources/{identifier}", json=approved, headers=headers
        ).status_code
        == 200
    )
    active = {**direct, "status": "ACTIVE"}
    assert (
        client.put(f"/api/v1/admin/sources/{identifier}", json=active, headers=headers).json()[
            "active"
        ]
        is True
    )
    paused = {**direct, "status": "PAUSED"}
    assert (
        client.put(f"/api/v1/admin/sources/{identifier}", json=paused, headers=headers).json()[
            "active"
        ]
        is False
    )
    retired = {**direct, "status": "RETIRED"}
    assert (
        client.put(f"/api/v1/admin/sources/{identifier}", json=retired, headers=headers).status_code
        == 200
    )
    bad = payload()
    bad["data"]["website_url"] = "https://127.0.0.1/internal"
    assert client.post("/api/v1/admin/sources", json=bad, headers=headers).status_code == 422
    assert db.scalar(select(func.count()).select_from(SourceDiscovery)) == 1


def test_connector_registry_capabilities_and_harness():
    registry = ConnectorRegistry()
    registry.register("etenders", ETendersConnector)
    description = registry.describe("etenders")
    assert description["version"] == "1.0.0"
    assert description["capabilities"]["supports_api"] is True
    with pytest.raises(ValueError):
        registry.register("etenders", ETendersConnector)


@pytest.mark.asyncio
async def test_connector_contract_harness():
    harness = ConnectorContractHarness(FixtureConnector(FIXTURE[:1]))
    results = await harness.exercise()
    harness.assert_contract(results)
    assert len(results) == 1
    assert len(results[0]["documents"]) == 1


def test_coverage_counts_actual_records(client, db):
    headers = admin_headers(client, db)
    municipality = Municipality(
        province_id="province", code="TEST001", name="Test Municipality", active=True
    )
    db.add(municipality)
    # use valid province FK under SQLite tests where enforcement is off; coverage is count based
    db.flush()
    db.add(
        MunicipalitySourceCoverage(
            municipality_id=municipality.id,
            source_identified=True,
            verification_status="REVIEW",
            connector_implemented=False,
        )
    )
    db.commit()
    data = client.get("/api/v1/admin/source-coverage", headers=headers).json()
    assert data["total_municipalities"] >= 1
    assert data["source_identified"] == 1
    assert data["connector_implemented"] == 0
    assert data["needs_investigation"] == data["total_municipalities"] - 1


def test_stale_and_failure_health():
    source = Source(
        name="Health",
        slug="health",
        source_type="OTHER",
        organisation="Health",
        website_url="https://example.org",
        connector_type="TEST",
        polling_interval_minutes=60,
        status="ACTIVE",
        active=True,
        consecutive_failures=0,
        last_successful_run=datetime.now(UTC) - timedelta(hours=3),
    )
    assert health_for(source) == "STALE"
    source.consecutive_failures = 3
    assert health_for(source) == "FAILING"


@pytest.mark.asyncio
async def test_phase4_source_enters_search_and_notifications(db):
    source = Source(
        name="Municipal fixture",
        slug="municipal-fixture",
        source_type="MUNICIPAL",
        organisation="Municipality",
        website_url="https://example.org",
        connector_type="FIXTURE",
        status="ACTIVE",
        active=True,
    )
    user = User(email="phase4@example.org", password_hash="x", first_name="Phase", last_name="Four")
    db.add_all([source, user])
    db.flush()
    db.add(
        SavedSearch(
            user_id=user.id,
            name="Construction",
            query="construction",
            filters={},
            sort="relevance",
            alerts_enabled=True,
        )
    )
    db.commit()
    run = await IngestionEngine(db, FixtureConnector(FIXTURE)).run(source)
    assert run.records_inserted == 2
    assert run.records_failed == 1
    assert db.scalar(select(func.count()).select_from(Notification)) == 1
    repeat = await IngestionEngine(db, FixtureConnector(FIXTURE[:2])).run(source)
    assert repeat.records_skipped == 2
    assert (
        db.scalar(select(func.count()).select_from(Tender).where(Tender.source_id == source.id))
        == 2
    )
    zero = await IngestionEngine(db, FixtureConnector([])).run(source)
    db.refresh(source)
    assert zero.status == "SUCCESS_WITH_ZERO_RESULTS"
    assert zero.zero_result_anomaly is True
    assert source.status == "FAILING"
