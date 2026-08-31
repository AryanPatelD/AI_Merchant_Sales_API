"""API tests for checkout and atomic order creation."""

from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.checkout import CheckoutResponse, OrderStatus
from app.services.checkout import (
    CheckoutAddressMismatchError,
    CheckoutIdempotencyConflictError,
    CheckoutInsufficientInventoryError,
    CheckoutInventoryNotConfiguredError,
    CheckoutQuoteExpiredError,
    CheckoutQuoteNotFoundError,
    CheckoutQuoteStatusError,
)

client = TestClient(app)
QUOTE_ID = "b504183a-a77b-4d9d-af76-7dc1151c8ea8"


def checkout_payload() -> dict:
    return {
        "quote_id": QUOTE_ID,
        "buyer": {
            "name": "Asha Patel",
            "email": "asha@example.com",
            "phone": "+919876543210",
        },
        "shipping_address": {
            "recipient_name": "Asha Patel",
            "address_line1": "12 Market Road",
            "city": "Mumbai",
            "state": "Maharashtra",
            "postal_code": "400001",
            "country": "India",
        },
    }


def test_checkout_forwards_idempotency_key(monkeypatch) -> None:
    captured = {}

    def fake_checkout(settings, request, idempotency_key) -> CheckoutResponse:
        captured["quote_id"] = request.quote_id
        captured["idempotency_key"] = idempotency_key
        return CheckoutResponse(
            order_id=UUID("e939539f-29c2-4eb8-b796-5a568341ed21"),
            quote_id=request.quote_id,
            status=OrderStatus.PENDING_PAYMENT,
            subtotal=Decimal("1598.00"),
            tax=Decimal("273.26"),
            shipping=Decimal("0.00"),
            total=Decimal("1791.36"),
            currency="INR",
        )

    monkeypatch.setattr("app.api.checkout.checkout", fake_checkout)
    response = client.post(
        "/api/v1/checkout",
        json=checkout_payload(),
        headers={"Idempotency-Key": "checkout-123"},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "PENDING_PAYMENT"
    assert captured == {
        "quote_id": UUID(QUOTE_ID),
        "idempotency_key": "checkout-123",
    }


def test_checkout_requires_idempotency_key() -> None:
    assert client.post("/api/v1/checkout", json=checkout_payload()).status_code == 422


def test_checkout_requires_buyer_contact() -> None:
    payload = checkout_payload()
    payload["buyer"] = {"name": "Asha Patel"}
    response = client.post(
        "/api/v1/checkout",
        json=payload,
        headers={"Idempotency-Key": "checkout-contact"},
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("service_error", "expected_status"),
    [
        (CheckoutQuoteNotFoundError(), 404),
        (CheckoutQuoteExpiredError(), 409),
        (CheckoutQuoteStatusError("CONSUMED"), 409),
        (CheckoutAddressMismatchError(), 409),
        (CheckoutInventoryNotConfiguredError("TS-MOU-M1"), 503),
        (CheckoutInsufficientInventoryError("TS-MOU-M1", 2, 1), 409),
        (CheckoutIdempotencyConflictError(), 409),
    ],
)
def test_checkout_maps_service_errors(monkeypatch, service_error, expected_status) -> None:
    def fail(settings, request, idempotency_key):
        raise service_error

    monkeypatch.setattr("app.api.checkout.checkout", fail)
    response = client.post(
        "/api/v1/checkout",
        json=checkout_payload(),
        headers={"Idempotency-Key": "checkout-error"},
    )
    assert response.status_code == expected_status
