import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))
from app.core import config
from app.main import app
from app.api import routes as routes_module

client = TestClient(app)


def reload_settings(monkeypatch, **overrides):
    for key, value in overrides.items():
        monkeypatch.setenv(key.upper(), str(value).lower() if isinstance(value, bool) else str(value))
    config.settings = config.Settings()
    routes_module.rate_limits.clear()
    return config.settings


def test_query_requires_api_key_when_enabled(monkeypatch):
    reload_settings(monkeypatch, require_api_key=True, api_key="super-secret")

    response = client.post(
        "/api/v1/consultations/query",
        json={
            "message": "Need guidance for a turmeric product in Germany",
            "language": "en",
            "jurisdiction_mode": "international",
            "target_country": "DE",
            "user_id": "demo-user",
        },
    )

    assert response.status_code == 401
    assert "api key" in response.json()["detail"].lower()


def test_query_respects_rate_limit(monkeypatch):
    reload_settings(monkeypatch, require_api_key=False, enable_rate_limit=True, rate_limit_per_minute=1)

    first = client.post(
        "/api/v1/consultations/query",
        json={
            "message": "Need guidance for a turmeric product in Germany",
            "language": "en",
            "jurisdiction_mode": "international",
            "target_country": "DE",
            "user_id": "demo-user",
        },
    )
    second = client.post(
        "/api/v1/consultations/query",
        json={
            "message": "Need guidance for a turmeric product in Germany",
            "language": "en",
            "jurisdiction_mode": "international",
            "target_country": "DE",
            "user_id": "demo-user",
        },
    )

    assert first.status_code in {200, 422}
    assert second.status_code == 429
