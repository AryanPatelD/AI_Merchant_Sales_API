"""API tests for merchant discovery."""

from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.discovery import MerchantDiscoveryManifest
from app.services.discovery import (
    MerchantInactiveError,
    MerchantNotFoundError,
    MerchantVersionMismatchError,
)


client = TestClient(app)


def test_discovery_manifest(monkeypatch) -> None:
    expected = MerchantDiscoveryManifest(
        merchant_id=UUID("00000000-0000-0000-0000-000000000001"),
        merchant="TechStore",
        api_version="1.0",
        currency="INR",
        country="IN",
        capabilities=[],
        payment_gateways=[],
        api_base_url="/api/v1",
    )
    monkeypatch.setattr(
        "app.api.discovery.get_merchant_manifest",
        lambda settings: expected,
    )

    response = client.get("/.well-known/ai-commerce")

    assert response.status_code == 200
    assert response.json() == {
        "merchant_id": "00000000-0000-0000-0000-000000000001",
        "merchant": "TechStore",
        "api_version": "1.0",
        "currency": "INR",
        "country": "IN",
        "capabilities": [],
        "payment_gateways": [],
        "api_base_url": "/api/v1",
    }


@pytest.mark.parametrize(
    ("service_error", "expected_status", "expected_detail"),
    [
        (
            MerchantNotFoundError(),
            404,
            "Configured merchant was not found",
        ),
        (
            MerchantInactiveError(),
            409,
            "Merchant is not active",
        ),
        (
            MerchantVersionMismatchError(),
            503,
            "Merchant API version is not supported by this application",
        ),
    ],
)
def test_discovery_errors(
    monkeypatch,
    service_error: Exception,
    expected_status: int,
    expected_detail: str,
) -> None:
    def raise_service_error(settings) -> None:
        raise service_error

    monkeypatch.setattr(
        "app.api.discovery.get_merchant_manifest",
        raise_service_error,
    )

    response = client.get("/.well-known/ai-commerce")

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}
