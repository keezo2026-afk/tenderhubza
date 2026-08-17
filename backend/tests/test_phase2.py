from datetime import date

from sqlalchemy import func, select

from app.models import SavedSearch, SavedTender, Source, Tender


def register(client, email):
    payload = {
        "email": email,
        "password": "StrongPass123!",
        "first_name": "Test",
        "last_name": "User",
    }
    client.post("/api/v1/auth/register", json=payload)
    token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": payload["password"]}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def tender(db, index=1):
    source = db.scalar(select(Source).where(Source.name == "Phase 2 source"))
    if not source:
        source = Source(
            name="Phase 2 source",
            source_type="OTHER",
            organisation="Test",
            website_url="https://example.org",
            connector_type="PHASE2_TEST",
            polling_frequency="manual",
        )
        db.add(source)
        db.flush()
    item = Tender(
        source_id=source.id,
        source_reference=f"phase2-{index}",
        reference_number=f"P2-{index}",
        title=f"Construction opportunity {index}",
        organisation="Public Works",
        province="KwaZulu-Natal",
        category="Construction",
        source_url=f"https://example.org/{index}",
        status="OPEN",
        closing_date=date(2026, 9, index),
    )
    db.add(item)
    db.commit()
    return item


def test_saved_tender_save_duplicate_list_unsave_and_auth(client, db):
    item = tender(db)
    a = register(client, "saved-a@example.co.za")
    b = register(client, "saved-b@example.co.za")
    assert client.post(f"/api/v1/tenders/{item.id}/save").status_code == 401
    assert client.post(f"/api/v1/tenders/{item.id}/save", headers=a).status_code == 201
    assert client.post(f"/api/v1/tenders/{item.id}/save", headers=a).status_code == 201
    assert db.scalar(select(func.count()).select_from(SavedTender)) == 1
    result = client.get("/api/v1/users/me/saved-tenders", headers=a).json()
    assert result["total"] == 1
    assert result["items"][0]["tender"]["id"] == item.id
    assert client.get("/api/v1/users/me/saved-tenders", headers=b).json()["total"] == 0
    state = client.get(f"/api/v1/tenders/{item.id}/saved", headers=a)
    assert state.json()["saved"] is True
    assert client.delete(f"/api/v1/tenders/{item.id}/save", headers=a).status_code == 204
    assert client.get(f"/api/v1/tenders/{item.id}/saved", headers=a).json()["saved"] is False


def test_saved_tender_pagination(client, db):
    a = register(client, "pages@example.co.za")
    for i in range(1, 4):
        client.post(f"/api/v1/tenders/{tender(db, i).id}/save", headers=a)
    one = client.get("/api/v1/users/me/saved-tenders?page=1&page_size=2", headers=a).json()
    two = client.get("/api/v1/users/me/saved-tenders?page=2&page_size=2", headers=a).json()
    assert one["total_pages"] == 2
    assert {x["tender"]["id"] for x in one["items"]}.isdisjoint(
        {x["tender"]["id"] for x in two["items"]}
    )


def test_saved_search_crud_and_user_isolation(client, db):
    a = register(client, "search-a@example.co.za")
    b = register(client, "search-b@example.co.za")
    body = {
        "name": "KZN Construction",
        "query": "construction",
        "filters": {"provinceId": "kzn", "category": "Construction"},
        "sort": "closing_soon",
    }
    assert client.post("/api/v1/searches", json=body).status_code == 401
    created = client.post("/api/v1/searches", json=body, headers=a)
    assert created.status_code == 201
    identifier = created.json()["id"]
    assert client.get(f"/api/v1/searches/{identifier}", headers=b).status_code == 404
    assert (
        client.put(
            f"/api/v1/searches/{identifier}", json={**body, "name": "Renamed"}, headers=b
        ).status_code
        == 404
    )
    updated = client.put(
        f"/api/v1/searches/{identifier}", json={**body, "name": "Renamed"}, headers=a
    )
    assert updated.json()["name"] == "Renamed"
    assert client.get("/api/v1/searches", headers=a).json()["total"] == 1
    assert client.delete(f"/api/v1/searches/{identifier}", headers=b).status_code == 404
    assert client.delete(f"/api/v1/searches/{identifier}", headers=a).status_code == 204
    assert db.scalar(select(func.count()).select_from(SavedSearch)) == 0


def test_profile_get_and_update_is_scoped(client):
    a = register(client, "profile@example.co.za")
    body = {
        "first_name": "Nomsa",
        "last_name": "Dlamini",
        "phone": "0820000000",
        "province": "KwaZulu-Natal",
        "city": "Durban",
    }
    response = client.put("/api/v1/users/me/profile", json=body, headers=a)
    assert response.status_code == 200
    assert response.json()["city"] == "Durban"
    assert client.get("/api/v1/users/me/profile", headers=a).json()["first_name"] == "Nomsa"
