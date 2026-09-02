"""Shared API infrastructure tests."""

from fastapi.testclient import TestClient

from app.main import app
from app.middleware.security import InMemoryRateLimiter, hash_api_key


def test_api_key_hash_is_peppered_and_not_plaintext() -> None:
    digest = hash_api_key("ai_client_key", "pepper")
    assert digest != "ai_client_key"
    assert digest == hash_api_key("ai_client_key", "pepper")
    assert digest != hash_api_key("ai_client_key", "other-pepper")


def test_rate_limiter_is_scoped_by_client_and_endpoint() -> None:
    limiter = InMemoryRateLimiter()
    assert limiter.allow("client-a", "/payment", 1, 60)
    assert not limiter.allow("client-a", "/payment", 1, 60)
    assert limiter.allow("client-a", "/quote", 1, 60)
    assert limiter.allow("client-b", "/payment", 1, 60)


def test_request_id_is_returned() -> None:
    response = TestClient(app).get("/health", headers={"X-Request-ID": "req-test-123"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-test-123"
