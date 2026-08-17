from app.core.security import hash_password
from app.models import User


def test_health(client):
    assert client.get("/api/v1/health").json()["status"] == "ok"


def test_register_login_me_logout(client, user_payload):
    created = client.post("/api/v1/auth/register", json=user_payload)
    assert created.status_code == 201
    assert "password" not in created.text
    duplicate = client.post("/api/v1/auth/register", json=user_payload)
    assert duplicate.status_code == 409
    login = client.post(
        "/api/v1/auth/login",
        json={"email": user_payload["email"], "password": user_payload["password"]},
    )
    assert login.status_code == 200
    headers = {"Authorization": "Bearer " + login.json()["access_token"]}
    assert client.get("/api/v1/users/me", headers=headers).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401


def test_registration_validation(client):
    assert (
        client.post("/api/v1/auth/register", json={"email": "bad", "password": "short"}).status_code
        == 422
    )


def test_anonymous_and_user_cannot_admin(client, auth_headers):
    body = {
        "name": "National Treasury",
        "source_type": "NATIONAL",
        "organisation": "Treasury",
        "website_url": "https://example.org",
        "connector_type": "treasury",
    }
    assert client.post("/api/v1/sources", json=body).status_code == 401
    assert client.post("/api/v1/sources", json=body, headers=auth_headers).status_code == 403


def test_source_and_tender_creation_and_retrieval(client, db):
    admin = User(
        email="admin@example.co.za",
        password_hash=hash_password("AdminPass123!"),
        first_name="Admin",
        last_name="User",
        role="ADMIN",
    )
    db.add(admin)
    db.commit()
    token = client.post(
        "/api/v1/auth/login", json={"email": admin.email, "password": "AdminPass123!"}
    ).json()["access_token"]
    headers = {"Authorization": "Bearer " + token}
    source_body = {
        "name": "eTender Publication Portal",
        "source_type": "NATIONAL",
        "organisation": "National Treasury",
        "website_url": "https://www.etenders.gov.za",
        "connector_type": "etenders",
    }
    response = client.post("/api/v1/sources", json=source_body, headers=headers)
    assert response.status_code == 201
    source_id = response.json()["id"]
    assert client.get("/api/v1/sources").json()["total"] == 1
    tender = {
        "source_id": source_id,
        "source_reference": "ABC-1",
        "title": "Supply of office equipment",
        "organisation": "National Treasury",
        "source_url": "https://example.org/tender/1",
    }
    response = client.post("/api/v1/tenders", json=tender, headers=headers)
    assert response.status_code == 201
    tender_id = response.json()["id"]
    assert client.get(f"/api/v1/tenders/{tender_id}").status_code == 200
    assert client.get("/api/v1/tenders").json()["total"] == 1
