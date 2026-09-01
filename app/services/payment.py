"""Razorpay order creation and verified webhook reconciliation."""

import hashlib
import hmac
import json
from decimal import Decimal
from uuid import UUID, uuid4

import httpx
from psycopg.types.json import Jsonb

from app.config import Settings
from app.database.connection import database_connection
from app.schemas.payment import (
    PaymentResponse,
    PaymentStatus,
    WebhookResponse,
)

RAZORPAY_ORDERS_URL = "https://api.razorpay.com/v1/orders"
SUPPORTED_EVENTS = {
    "payment.created": PaymentStatus.CREATED,
    "payment.authorized": PaymentStatus.AUTHORIZED,
    "payment.captured": PaymentStatus.CAPTURED,
    "payment.failed": PaymentStatus.FAILED,
}


class PaymentConfigurationError(Exception):
    pass


class MerchantOrderNotFoundError(Exception):
    pass


class MerchantOrderStatusError(Exception):
    def __init__(self, status: str) -> None:
        self.status = status


class RazorpayGatewayError(Exception):
    pass


class WebhookSignatureError(Exception):
    pass


class WebhookPayloadError(Exception):
    pass


def amount_to_subunits(amount: Decimal) -> int:
    """Convert the project's two-decimal currencies to integer subunits."""
    subunits = amount * 100
    if subunits != subunits.to_integral_value() or subunits <= 0:
        raise ValueError("payment amount must be positive with at most two decimals")
    return int(subunits)


def create_gateway_order(
    key_id: str,
    key_secret: str,
    amount_subunits: int,
    currency: str,
    receipt: str,
    merchant_order_id: UUID,
) -> dict:
    """Create a Razorpay order using HTTP Basic authentication."""
    try:
        response = httpx.post(
            RAZORPAY_ORDERS_URL,
            auth=(key_id, key_secret),
            json={
                "amount": amount_subunits,
                "currency": currency,
                "receipt": receipt[:40],
                "notes": {"merchant_order_id": str(merchant_order_id)},
            },
            timeout=15.0,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise RazorpayGatewayError from error
    if not payload.get("id") or payload.get("amount") != amount_subunits:
        raise RazorpayGatewayError
    return payload


def create_payment(
    settings: Settings,
    order_id: UUID,
) -> PaymentResponse:
    """Create one persisted Razorpay order for a merchant order."""
    if settings.razorpay_key_id is None or settings.razorpay_key_secret is None:
        raise PaymentConfigurationError
    key_id = settings.razorpay_key_id
    key_secret = settings.razorpay_key_secret.get_secret_value()

    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT order_id, total_amount, currency, order_status
                FROM orders
                WHERE order_id = %s AND merchant_id = %s
                FOR UPDATE
                """,
                (order_id, settings.merchant_id),
            )
            order = cursor.fetchone()
            if order is None:
                raise MerchantOrderNotFoundError
            if order["order_status"] != "PENDING_PAYMENT":
                raise MerchantOrderStatusError(order["order_status"])

            cursor.execute(
                """
                SELECT payment_id, gateway_order_id, amount, currency,
                       payment_status
                FROM payments
                WHERE order_id = %s AND payment_gateway = 'RAZORPAY'
                """,
                (order_id,),
            )
            existing = cursor.fetchone()
            if existing is not None and existing["gateway_order_id"] is not None:
                return PaymentResponse(
                    payment_id=existing["payment_id"],
                    order_id=order_id,
                    gateway="RAZORPAY",
                    gateway_order_id=existing["gateway_order_id"],
                    key_id=key_id,
                    amount=existing["amount"],
                    amount_subunits=amount_to_subunits(existing["amount"]),
                    currency=existing["currency"],
                    status=existing["payment_status"],
                )

            payment_id = existing["payment_id"] if existing else uuid4()
            if existing is None:
                cursor.execute(
                    """
                    INSERT INTO payments (
                        payment_id, order_id, payment_gateway, amount,
                        currency, payment_status
                    ) VALUES (%s, %s, 'RAZORPAY', %s, %s, 'CREATED')
                    """,
                    (
                        payment_id, order_id, order["total_amount"],
                        order["currency"],
                    ),
                )

            amount_subunits = amount_to_subunits(order["total_amount"])
            gateway_order = create_gateway_order(
                key_id,
                key_secret,
                amount_subunits,
                order["currency"],
                f"order-{str(order_id)[:32]}",
                order_id,
            )
            cursor.execute(
                """
                UPDATE payments
                SET gateway_order_id = %s, payment_status = 'PENDING',
                    updated_at = CURRENT_TIMESTAMP
                WHERE payment_id = %s
                """,
                (gateway_order["id"], payment_id),
            )

    return PaymentResponse(
        payment_id=payment_id,
        order_id=order_id,
        gateway="RAZORPAY",
        gateway_order_id=gateway_order["id"],
        key_id=key_id,
        amount=order["total_amount"],
        amount_subunits=amount_subunits,
        currency=order["currency"],
        status=PaymentStatus.PENDING,
    )


def verify_webhook_signature(raw_body: bytes, signature: str, secret: str) -> None:
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise WebhookSignatureError


def _payment_entity(payload: dict) -> dict:
    try:
        entity = payload["payload"]["payment"]["entity"]
    except (KeyError, TypeError) as error:
        raise WebhookPayloadError from error
    if not isinstance(entity, dict):
        raise WebhookPayloadError
    return entity


def next_payment_status(
    current: PaymentStatus, target: PaymentStatus
) -> PaymentStatus:
    """Prevent delayed or out-of-order webhooks from downgrading state."""
    if current in {PaymentStatus.CAPTURED, PaymentStatus.REFUNDED}:
        return current
    if current is PaymentStatus.FAILED and target is not PaymentStatus.CAPTURED:
        return current
    if current is PaymentStatus.AUTHORIZED and target is PaymentStatus.CREATED:
        return current
    return target


def next_gateway_payment_id(
    current: PaymentStatus,
    target: PaymentStatus,
    existing_payment_id: str | None,
    incoming_payment_id: str,
) -> str:
    """Track the accepted attempt without letting delayed events replace it."""
    accepted_status = next_payment_status(current, target)
    if accepted_status is target:
        return incoming_payment_id
    return existing_payment_id or incoming_payment_id


def process_webhook(
    settings: Settings,
    raw_body: bytes,
    signature: str,
    event_id: str,
) -> WebhookResponse:
    """Verify, deduplicate and reconcile a Razorpay payment webhook."""
    if settings.razorpay_webhook_secret is None:
        raise PaymentConfigurationError
    verify_webhook_signature(
        raw_body, signature, settings.razorpay_webhook_secret.get_secret_value()
    )
    try:
        payload = json.loads(raw_body)
        event_type = payload["event"]
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise WebhookPayloadError from error

    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO payment_webhook_events (
                    webhook_event_id, gateway, gateway_event_id, event_type,
                    payload, processing_status
                ) VALUES (%s, 'RAZORPAY', %s, %s, %s, 'RECEIVED')
                ON CONFLICT (gateway_event_id) DO NOTHING
                RETURNING webhook_event_id
                """,
                (uuid4(), event_id, event_type, Jsonb(payload)),
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    """
                    SELECT event_type, processing_status
                    FROM payment_webhook_events
                    WHERE gateway_event_id = %s
                    """,
                    (event_id,),
                )
                existing = cursor.fetchone()
                return WebhookResponse(
                    event_id=event_id,
                    event_type=existing["event_type"],
                    processing_status=existing["processing_status"],
                    duplicate=True,
                )

            target_status = SUPPORTED_EVENTS.get(event_type)
            if target_status is None:
                processing_status = "IGNORED"
            else:
                entity = _payment_entity(payload)
                gateway_order_id = entity.get("order_id")
                gateway_payment_id = entity.get("id")
                if not gateway_order_id or not gateway_payment_id:
                    raise WebhookPayloadError
                cursor.execute(
                    """
                    SELECT payment_id, order_id, amount, currency, payment_status,
                           gateway_payment_id
                    FROM payments
                    WHERE gateway_order_id = %s
                    FOR UPDATE
                    """,
                    (gateway_order_id,),
                )
                payment = cursor.fetchone()
                if payment is None:
                    processing_status = "IGNORED"
                else:
                    event_amount = entity.get("amount")
                    event_currency = entity.get("currency")
                    if (
                        event_amount != amount_to_subunits(payment["amount"])
                        or event_currency != payment["currency"]
                    ):
                        raise WebhookPayloadError

                    current = PaymentStatus(payment["payment_status"])
                    new_status = next_payment_status(current, target_status)
                    accepted_gateway_payment_id = next_gateway_payment_id(
                        current,
                        target_status,
                        payment["gateway_payment_id"],
                        gateway_payment_id,
                    )

                    failure_reason = None
                    if new_status is PaymentStatus.FAILED:
                        failure_reason = entity.get("error_description") or entity.get("error_reason")
                    cursor.execute(
                        """
                        UPDATE payments
                        SET gateway_payment_id = %s,
                            payment_status = %s, failure_reason = %s,
                            paid_at = CASE WHEN %s = 'CAPTURED' THEN CURRENT_TIMESTAMP ELSE paid_at END,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE payment_id = %s
                        """,
                        (
                            accepted_gateway_payment_id, new_status.value, failure_reason,
                            new_status.value, payment["payment_id"],
                        ),
                    )
                    if new_status is PaymentStatus.CAPTURED:
                        cursor.execute(
                            """
                            UPDATE orders SET order_status = 'PAID', updated_at = CURRENT_TIMESTAMP
                            WHERE order_id = %s AND order_status IN ('PENDING_PAYMENT', 'PAYMENT_FAILED')
                            """,
                            (payment["order_id"],),
                        )
                    elif new_status is PaymentStatus.FAILED:
                        cursor.execute(
                            """
                            UPDATE orders SET order_status = 'PAYMENT_FAILED', updated_at = CURRENT_TIMESTAMP
                            WHERE order_id = %s AND order_status = 'PENDING_PAYMENT'
                            """,
                            (payment["order_id"],),
                        )
                    processing_status = "PROCESSED"

            cursor.execute(
                """
                UPDATE payment_webhook_events
                SET processing_status = %s, processed_at = CURRENT_TIMESTAMP
                WHERE gateway_event_id = %s
                """,
                (processing_status, event_id),
            )

    return WebhookResponse(
        event_id=event_id,
        event_type=event_type,
        processing_status=processing_status,
    )
