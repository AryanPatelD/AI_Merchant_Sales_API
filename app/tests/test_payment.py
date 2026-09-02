"""API, signature and state tests for Razorpay payments."""

import hashlib
import hmac
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.payment import PaymentResponse, PaymentStatus, WebhookResponse
from app.services.payment import (
    MerchantOrderNotFoundError,
    MerchantOrderStatusError,
    PaymentConfigurationError,
    RazorpayGatewayError,
    WebhookSignatureError,
    amount_to_subunits,
    next_gateway_payment_id,
    next_payment_status,
    verify_webhook_signature,
)

client = TestClient(app)
ORDER_ID = "e939539f-29c2-4eb8-b796-5a568341ed21"
IDEMPOTENCY_HEADERS = {"Idempotency-Key": "payment-test-key"}


@pytest.fixture(autouse=True)
def bypass_idempotency_storage(monkeypatch):
    monkeypatch.setattr(
        "app.api.payment.run_idempotent",
        lambda key, endpoint, response_type, operation: operation(),
    )


def test_amount_to_subunits() -> None:
    assert amount_to_subunits(Decimal("1791.36")) == 179136
    with pytest.raises(ValueError):
        amount_to_subunits(Decimal("1.001"))


def test_webhook_signature_uses_raw_body() -> None:
    body = b'{"event":"payment.captured"}'
    signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    verify_webhook_signature(body, signature, "secret")
    with pytest.raises(WebhookSignatureError):
        verify_webhook_signature(body + b" ", signature, "secret")


@pytest.mark.parametrize(
    ("current", "target", "expected"),
    [
        (PaymentStatus.AUTHORIZED, PaymentStatus.CREATED, PaymentStatus.AUTHORIZED),
        (PaymentStatus.CAPTURED, PaymentStatus.AUTHORIZED, PaymentStatus.CAPTURED),
        (PaymentStatus.FAILED, PaymentStatus.CREATED, PaymentStatus.FAILED),
        (PaymentStatus.FAILED, PaymentStatus.CAPTURED, PaymentStatus.CAPTURED),
    ],
)
def test_payment_state_is_monotonic(current, target, expected) -> None:
    assert next_payment_status(current, target) is expected


def test_successful_retry_replaces_failed_gateway_payment_id() -> None:
    assert next_gateway_payment_id(
        PaymentStatus.FAILED,
        PaymentStatus.CAPTURED,
        "pay_failed_attempt",
        "pay_successful_retry",
    ) == "pay_successful_retry"


def test_delayed_failure_cannot_replace_captured_gateway_payment_id() -> None:
    assert next_gateway_payment_id(
        PaymentStatus.CAPTURED,
        PaymentStatus.FAILED,
        "pay_captured",
        "pay_delayed_failure",
    ) == "pay_captured"


def test_payment_route(monkeypatch) -> None:
    def fake_create(settings, order_id):
        return PaymentResponse(
            payment_id=UUID("fe9d0998-e89f-4ad3-b7f8-e6d1214d0705"),
            order_id=order_id,
            gateway="RAZORPAY",
            gateway_order_id="order_test123",
            key_id="rzp_test_public",
            amount=Decimal("1791.36"),
            amount_subunits=179136,
            currency="INR",
            status=PaymentStatus.PENDING,
        )

    monkeypatch.setattr("app.api.payment.create_payment", fake_create)
    response = client.post("/api/v1/payment", json={"order_id": ORDER_ID}, headers=IDEMPOTENCY_HEADERS)
    assert response.status_code == 201
    assert response.json()["gateway_order_id"] == "order_test123"
    assert response.json()["key_id"] == "rzp_test_public"


def test_payment_requires_idempotency_key() -> None:
    response = client.post("/api/v1/payment", json={"order_id": ORDER_ID})
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (PaymentConfigurationError(), 503),
        (MerchantOrderNotFoundError(), 404),
        (MerchantOrderStatusError("PAID"), 409),
        (RazorpayGatewayError(), 502),
    ],
)
def test_payment_route_errors(monkeypatch, error, status_code) -> None:
    def fail(settings, order_id):
        raise error

    monkeypatch.setattr("app.api.payment.create_payment", fail)
    response = client.post("/api/v1/payment", json={"order_id": ORDER_ID}, headers=IDEMPOTENCY_HEADERS)
    assert response.status_code == status_code


def test_webhook_route_forwards_untouched_body(monkeypatch) -> None:
    captured = {}

    def fake_process(settings, raw_body, signature, event_id):
        captured.update(body=raw_body, signature=signature, event_id=event_id)
        return WebhookResponse(
            event_id=event_id,
            event_type="payment.captured",
            processing_status="PROCESSED",
        )

    monkeypatch.setattr("app.api.payment.process_webhook", fake_process)
    body = b'{"event": "payment.captured"}'
    response = client.post(
        "/webhooks/razorpay",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": "signature",
            "X-Razorpay-Event-Id": "event-123",
        },
    )
    assert response.status_code == 200
    assert captured == {
        "body": body,
        "signature": "signature",
        "event_id": "event-123",
    }
