import copy
import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path

import httpx
import pytest
from sqlalchemy import func, select

from app.connectors.national.etenders import ETendersConnector
from app.core.errors import ApiError
from app.core.rate_limit import InMemoryRateLimiter
from app.ingestion.contracts import DiscoveredItem, RawPayload
from app.ingestion.etenders_runner import ETendersIngestionService
from app.models import (
    ConnectorState,
    GeographyDataset,
    Province,
    RawIngestion,
    Source,
    Tender,
    TenderDocument,
    TenderDuplicateCandidate,
    TenderSourceVersion,
)
from app.services.geography_import import import_census_geography

FIXTURE = json.loads((Path(__file__).parent / "fixtures/etenders_releases.json").read_text())[
    "releases"
]


class FixtureConnector(ETendersConnector):
    def __init__(self, releases):
        self.releases = releases
        self.page_number = 1
        self.page_size = 100
        self.date_from = None
        self.date_to = None
        self.timeout = 1
        self.max_attempts = 1
        self._client = None

    async def discover(self):
        return [
            DiscoveredItem(
                r["ocid"],
                f"https://ocds-api.etenders.gov.za/api/OCDSReleases/release/{r['ocid']}",
                r.get("id"),
            )
            for r in self.releases
        ]

    async def fetch(self, item):
        release = next(r for r in self.releases if r["ocid"] == item.source_identifier)
        digest = hashlib.sha256(
            json.dumps(release, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return RawPayload(
            item.source_identifier,
            item.url,
            copy.deepcopy(release),
            datetime.now(UTC),
            self.VERSION,
            200,
            "application/json",
            item.url,
            digest,
            release.get("id"),
        )


def source(db):
    item = Source(
        name="National Treasury eTender OCDS",
        source_type="NATIONAL",
        organisation="National Treasury",
        website_url="https://www.etenders.gov.za",
        api_url="https://ocds-api.etenders.gov.za/api/OCDSReleases",
        connector_type="ETENDERS_OCDS",
        polling_frequency="daily",
    )
    db.add(item)
    db.add(Province(code="KZN", name="KwaZulu-Natal"))
    db.commit()
    return item


@pytest.mark.asyncio
async def test_raw_first_insert_duplicate_update_and_failure_isolation(db):
    src = source(db)
    run = await ETendersIngestionService(db, FixtureConnector(FIXTURE)).run(
        src, high_water_candidate=date(2026, 8, 17)
    )
    assert db.get(ConnectorState, src.id) is None
    assert (run.status, run.records_discovered, run.records_inserted, run.records_failed) == (
        "PARTIAL",
        3,
        2,
        1,
    )
    assert db.scalar(select(func.count()).select_from(RawIngestion)) == 3
    assert db.scalar(select(func.count()).select_from(Tender)) == 2
    first = db.scalar(select(Tender).where(Tender.source_reference == "ocds-9t57fa-200001"))
    assert first.province == "KwaZulu-Natal"
    assert first.province_id is not None
    assert db.scalar(select(func.count()).select_from(TenderDocument)) == 1
    other = Source(
        name="Deterministic second source",
        source_type="OTHER",
        organisation="Second registry",
        website_url="https://second.example.org",
        connector_type="TEST_SECOND",
        polling_frequency="manual",
    )
    db.add(other)
    db.commit()
    cross = await ETendersIngestionService(db, FixtureConnector([FIXTURE[0]])).run(other)
    assert cross.records_inserted == 1
    assert db.scalar(select(func.count()).select_from(TenderDuplicateCandidate)) == 1
    duplicate = db.scalar(select(TenderDuplicateCandidate))
    assert duplicate.confidence == 1
    assert duplicate.match_method == "EXACT_REFERENCE_ORGANISATION"
    assert duplicate.signals == ["REFERENCE_MATCH", "ORGANISATION_MATCH"]
    second = await ETendersIngestionService(db, FixtureConnector(FIXTURE[:2])).run(
        src, high_water_candidate=date(2026, 8, 17)
    )
    assert second.records_skipped == 2
    assert db.scalar(select(func.count()).select_from(Tender)) == 3
    assert db.get(ConnectorState, src.id).high_water_date == date(2026, 8, 17)
    changed = copy.deepcopy(FIXTURE[0])
    changed["tender"]["title"] = "Updated construction and refurbishment"
    changed["tender"]["tenderPeriod"]["endDate"] = "2026-09-28T11:00:00+02:00"
    third = await ETendersIngestionService(db, FixtureConnector([changed])).run(src)
    assert third.records_updated == 1
    db.refresh(first)
    assert first.closing_date == date(2026, 9, 28)
    versions = list(
        db.scalars(select(TenderSourceVersion).where(TenderSourceVersion.tender_id == first.id))
    )
    assert len(versions) == 2
    assert "closing_date" in versions[-1].change_summary


@pytest.mark.asyncio
async def test_ocds_normalization_maps_without_inventing_data():
    normalized = await ETendersConnector().normalize(FIXTURE[0])
    assert normalized.reference_number == "ZNT-CONSTRUCTION-001"
    assert normalized.closing_time.hour == 11
    assert normalized.currency == "ZAR"
    assert normalized.municipality is None
    assert len(normalized.documents) == 1


@pytest.mark.asyncio
async def test_connector_retries_transient_response(monkeypatch):
    calls = 0

    async def no_sleep(_):
        pass

    monkeypatch.setattr("app.connectors.national.etenders.connector.asyncio.sleep", no_sleep)

    def handler(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, request=request)
        return httpx.Response(200, json={"releases": [FIXTURE[0]]}, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        items = await ETendersConnector(max_attempts=2, client=client).discover()
    assert calls == 2
    assert items[0].source_identifier == FIXTURE[0]["ocid"]


def test_refresh_rotation_reuse_detection_and_password_reset(client, user_payload):
    client.post("/api/v1/auth/register", json=user_payload)
    login = client.post(
        "/api/v1/auth/login",
        json={"email": user_payload["email"], "password": user_payload["password"]},
    )
    assert login.status_code == 200
    old = login.json()["refresh_token"]
    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": old})
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != old
    reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": old})
    assert reuse.status_code == 401
    assert reuse.json()["error"]["code"] == "REFRESH_TOKEN_REUSE"
    reset = client.post(
        "/api/v1/auth/password-reset/request", json={"email": user_payload["email"]}
    )
    assert reset.status_code == 200
    token = reset.json()["development_token"]
    assert token
    assert (
        client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": token, "new_password": "DifferentPass123!"},
        ).status_code
        == 204
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"email": user_payload["email"], "password": "DifferentPass123!"},
        ).status_code
        == 200
    )


def test_admin_data_quality_is_protected_and_reports_counts(client, db):
    assert client.get("/api/v1/admin/data-quality").status_code == 401
    from app.core.security import hash_password
    from app.models import User

    admin = User(
        email="quality-admin@example.co.za",
        password_hash=hash_password("AdminPass123!"),
        first_name="Quality",
        last_name="Admin",
        role="ADMIN",
    )
    db.add(admin)
    db.commit()
    token = client.post(
        "/api/v1/auth/login", json={"email": admin.email, "password": "AdminPass123!"}
    ).json()["access_token"]
    response = client.get(
        "/api/v1/admin/data-quality", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert set(response.json()) >= {
        "sources",
        "tender_ingestion",
        "processing_last_30_days",
        "duplicates",
        "documents",
    }


def test_rate_limiter_blocks_excess_attempts():
    rate = InMemoryRateLimiter()
    rate.check("login:test", 1)
    with pytest.raises(ApiError) as exc:
        rate.check("login:test", 1)
    assert exc.value.status_code == 429


def test_error_envelope(client):
    response = client.post("/api/v1/auth/register", json={"email": "bad", "password": "x"})
    assert response.status_code == 422
    assert set(response.json()["error"]) == {"code", "message", "details"}


def test_relevance_pagination_has_deterministic_tie_breaker(client, db):
    src = source(db)
    for index in range(45):
        db.add(
            Tender(
                source_id=src.id,
                source_reference=f"tie-{index}",
                title="Construction opportunity",
                organisation="Public Works",
                source_url=f"https://example.org/tie/{index}",
                status="OPEN",
                closing_date=date(2026, 9, 30),
            )
        )
    db.commit()
    first = client.get("/api/v1/tenders?q=construction&page=1&page_size=20").json()
    second = client.get("/api/v1/tenders?q=construction&page=2&page_size=20").json()
    assert {item["id"] for item in first["items"]}.isdisjoint(
        {item["id"] for item in second["items"]}
    )


def test_authoritative_geography_import_is_idempotent(db):
    for code, name in [
        ("EC", "Eastern Cape"),
        ("FS", "Free State"),
        ("GP", "Gauteng"),
        ("KZN", "KwaZulu-Natal"),
        ("LP", "Limpopo"),
        ("MP", "Mpumalanga"),
        ("NC", "Northern Cape"),
        ("NW", "North West"),
        ("WC", "Western Cape"),
    ]:
        db.add(Province(code=code, name=name))
    db.commit()
    result = import_census_geography(db)
    assert result["districts"] == 52
    assert result["municipalities"] == 213
    assert import_census_geography(db)["unchanged"] is True
    assert db.scalar(select(GeographyDataset)).source.startswith("Statistics South Africa")


def test_search_filters_dates_and_pagination(client, db):
    src = source(db)
    kzn = db.scalar(select(Province).where(Province.code == "KZN"))
    for i in range(5):
        db.add(
            Tender(
                source_id=src.id,
                source_reference=f"ref-{i}",
                title=("Construction project" if i % 2 == 0 else "Office supplies"),
                organisation="Public Works",
                province="KwaZulu-Natal",
                province_id=kzn.id,
                source_url=f"https://example.gov.za/{i}",
                status="OPEN",
                issue_date=date(2026, 8, 10 + i),
                closing_date=date(2026, 9, 10 + i),
            )
        )
    db.commit()
    result = client.get(
        f"/api/v1/tenders?q=construction&province_id={kzn.id}&closing_from=2026-09-10&closing_to=2026-09-30&page=1&page_size=2"
    )
    assert result.status_code == 200
    body = result.json()
    assert body["total"] == 3
    assert body["total_pages"] == 2
    ids1 = {x["id"] for x in body["items"]}
    ids2 = {
        x["id"]
        for x in client.get(
            f"/api/v1/tenders?q=construction&province_id={kzn.id}&page=2&page_size=2"
        ).json()["items"]
    }
    assert not ids1 & ids2
