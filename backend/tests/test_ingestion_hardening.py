from dataclasses import replace

import pytest
from sqlalchemy import func, select

from app.ingestion.engine import IngestionEngine
from app.ingestion.pipeline import IngestionCoordinator
from app.models import (
    District,
    GeographyResolutionIssue,
    Municipality,
    Province,
    RawIngestion,
    Source,
    Tender,
)
from tests.test_phase1 import FIXTURE, FixtureConnector


class GeographyFixtureConnector(FixtureConnector):
    async def normalize(self, release):
        normalized = await super().normalize(release)
        return replace(
            normalized,
            province=" kwazulu natal ",
            district="uMgungundlovu District Municipality",
            municipality="Msunduzi Local Municipality",
        )


class FailingDiscoveryConnector(FixtureConnector):
    NAME = "failing-discovery"

    async def discover(self):
        raise RuntimeError("isolated connector failure")


@pytest.mark.asyncio
async def test_generic_engine_resolves_geography_and_preserves_raw_first(db):
    province = Province(code="KZN", name="KwaZulu-Natal")
    db.add(province)
    db.flush()
    district = District(province_id=province.id, code="DC22", name="uMgungundlovu")
    db.add(district)
    db.flush()
    municipality = Municipality(
        province_id=province.id,
        district_id=district.id,
        code="KZN225",
        name="The Msunduzi",
    )
    source = Source(
        name="Generic engine source",
        source_type="OTHER",
        organisation="Test",
        website_url="https://example.org",
        connector_type="GENERIC_TEST",
        polling_frequency="manual",
    )
    db.add_all([municipality, source])
    db.commit()
    run = await IngestionEngine(db, GeographyFixtureConnector([FIXTURE[0]])).run(source)
    tender = db.scalar(select(Tender).where(Tender.source_id == source.id))
    assert run.records_inserted == 1
    assert tender.province_id == province.id
    assert tender.district_id == district.id
    assert tender.municipality_id == municipality.id
    assert db.scalar(select(func.count()).select_from(RawIngestion)) == 1
    assert db.scalar(select(func.count()).select_from(GeographyResolutionIssue)) == 0


@pytest.mark.asyncio
async def test_generic_engine_records_unresolved_geography(db):
    source = Source(
        name="Unresolved geography source",
        source_type="OTHER",
        organisation="Test",
        website_url="https://example.org",
        connector_type="UNRESOLVED_TEST",
        polling_frequency="manual",
    )
    db.add(source)
    db.commit()
    connector = GeographyFixtureConnector([FIXTURE[0]])
    run = await IngestionEngine(db, connector).run(source)
    issue = db.scalar(select(GeographyResolutionIssue))
    tender = db.scalar(select(Tender))
    assert run.status == "SUCCESS"
    assert issue is not None
    assert tender.municipality_id is None


@pytest.mark.asyncio
async def test_connector_failure_does_not_stop_next_connector(db):
    first = Source(
        name="Failing source",
        source_type="OTHER",
        organisation="Test",
        website_url="https://example.org/fail",
        connector_type="FAIL_TEST",
        polling_frequency="manual",
    )
    second = Source(
        name="Healthy source",
        source_type="OTHER",
        organisation="Test",
        website_url="https://example.org/ok",
        connector_type="OK_TEST",
        polling_frequency="manual",
    )
    db.add_all([first, second])
    db.commit()
    executions = await IngestionCoordinator(db).run_connectors(
        [
            (first, FailingDiscoveryConnector([])),
            (second, FixtureConnector([FIXTURE[1]])),
        ]
    )
    assert [execution.status for execution in executions] == ["FAILED", "SUCCESS"]
    assert db.scalar(select(func.count()).select_from(Tender)) == 1
