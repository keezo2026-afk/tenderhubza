import pytest
from pydantic import ValidationError

from app.core.config import Settings


def production_settings(**overrides):
    values = {
        "environment": "production",
        "database_url": "sqlite+pysqlite:///:memory:",
        "secret_key": "production-test-secret-at-least-32-characters",
        "mail_adapter": "development",
        "expose_development_reset_token": False,
    }
    values.update(overrides)
    return Settings(**values)


def test_configuration_rejects_development_token_exposure_in_production():
    with pytest.raises(ValidationError):
        production_settings(expose_development_reset_token=True)


def test_production_reset_response_never_contains_token(client, user_payload, monkeypatch):
    client.post("/api/v1/auth/register", json=user_payload)
    monkeypatch.setattr("app.api.routes.auth.get_settings", production_settings)
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": user_payload["email"]},
    )
    assert response.status_code == 200
    assert response.json()["development_token"] is None
