"""Atomic, idempotent checkout and order creation service."""

from uuid import uuid4

from psycopg.types.json import Jsonb

from app.config import Settings
from app.database.connection import database_connection
from app.schemas.checkout import CheckoutRequest, CheckoutResponse, OrderStatus

CHECKOUT_ENDPOINT = "/api/v1/checkout"


class CheckoutQuoteNotFoundError(Exception):
    pass


class CheckoutQuoteExpiredError(Exception):
    pass


class CheckoutQuoteStatusError(Exception):
    def __init__(self, status: str) -> None:
        self.status = status


class CheckoutAddressMismatchError(Exception):
    pass


class CheckoutInventoryNotConfiguredError(Exception):
    def __init__(self, sku: str) -> None:
        self.sku = sku


class CheckoutInsufficientInventoryError(Exception):
    def __init__(self, sku: str, requested: int, available: int) -> None:
        self.sku = sku
        self.requested = requested
        self.available = available


class CheckoutIdempotencyConflictError(Exception):
    pass


def checkout(
    settings: Settings,
    request: CheckoutRequest,
    idempotency_key: str,
) -> CheckoutResponse:
    """Consume a quote and reserve stock in one PostgreSQL transaction."""
    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO idempotency_keys (
                    idempotency_key, endpoint, created_at, expires_at
                )
                VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '24 hours')
                ON CONFLICT (idempotency_key) DO NOTHING
                RETURNING idempotency_key
                """,
                (idempotency_key, CHECKOUT_ENDPOINT),
            )
            owns_key = cursor.fetchone() is not None
            if not owns_key:
                cursor.execute(
                    """
                    SELECT endpoint, response_status, response_body
                    FROM idempotency_keys
                    WHERE idempotency_key = %s
                    FOR UPDATE
                    """,
                    (idempotency_key,),
                )
                existing = cursor.fetchone()
                if (
                    existing is None
                    or existing["endpoint"] != CHECKOUT_ENDPOINT
                    or existing["response_body"] is None
                ):
                    raise CheckoutIdempotencyConflictError
                return CheckoutResponse.model_validate(existing["response_body"])

            cursor.execute(
                """
                SELECT quote_id, status, expires_at, subtotal, discount_amount,
                       tax_amount, shipping_amount, total_amount, currency,
                       shipping_state, shipping_country
                FROM quotes
                WHERE quote_id = %s AND merchant_id = %s
                FOR UPDATE
                """,
                (request.quote_id, settings.merchant_id),
            )
            quote = cursor.fetchone()
            if quote is None:
                raise CheckoutQuoteNotFoundError
            if quote["status"] != "ACTIVE":
                raise CheckoutQuoteStatusError(quote["status"])

            cursor.execute(
                "SELECT %s <= CURRENT_TIMESTAMP AS expired",
                (quote["expires_at"],),
            )
            if cursor.fetchone()["expired"]:
                raise CheckoutQuoteExpiredError

            address = request.shipping_address
            if (
                quote["shipping_state"].strip().casefold() != address.state.strip().casefold()
                or quote["shipping_country"].strip().casefold()
                != address.country.strip().casefold()
            ):
                raise CheckoutAddressMismatchError

            cursor.execute(
                """
                SELECT qi.product_id, qi.sku, qi.product_name, qi.quantity,
                       qi.unit_price_snapshot, qi.line_subtotal,
                       qi.discount_amount, qi.gst_rate_snapshot,
                       qi.tax_amount, qi.line_total
                FROM quote_items AS qi
                WHERE qi.quote_id = %s
                ORDER BY qi.quote_item_id
                """,
                (request.quote_id,),
            )
            items = cursor.fetchall()
            for item in items:
                cursor.execute(
                    """
                    SELECT inventory_id, total_quantity, reserved_quantity
                    FROM inventory
                    WHERE product_id = %s
                    FOR UPDATE
                    """,
                    (item["product_id"],),
                )
                inventory = cursor.fetchone()
                if inventory is None:
                    raise CheckoutInventoryNotConfiguredError(item["sku"])
                item.update(inventory)
                available = item["total_quantity"] - item["reserved_quantity"]
                if available < item["quantity"]:
                    raise CheckoutInsufficientInventoryError(
                        item["sku"], item["quantity"], available
                    )

            buyer = request.buyer
            customer = None
            if buyer.email is not None:
                cursor.execute(
                    """
                    SELECT customer_id FROM customers
                    WHERE merchant_id = %s AND LOWER(email) = LOWER(%s)
                    FOR UPDATE
                    """,
                    (settings.merchant_id, str(buyer.email)),
                )
                customer = cursor.fetchone()
            elif buyer.phone is not None:
                cursor.execute(
                    """
                    SELECT customer_id FROM customers
                    WHERE merchant_id = %s AND phone = %s
                    ORDER BY created_at LIMIT 1 FOR UPDATE
                    """,
                    (settings.merchant_id, buyer.phone),
                )
                customer = cursor.fetchone()

            customer_id = customer["customer_id"] if customer else uuid4()
            if customer is None:
                cursor.execute(
                    """
                    INSERT INTO customers (
                        customer_id, merchant_id, name, email, phone
                    ) VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        customer_id, settings.merchant_id, buyer.name,
                        str(buyer.email) if buyer.email is not None else None,
                        buyer.phone,
                    ),
                )

            address_id = uuid4()
            cursor.execute(
                """
                INSERT INTO addresses (
                    address_id, customer_id, recipient_name, address_line1,
                    address_line2, city, state, postal_code, country
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    address_id, customer_id, address.recipient_name,
                    address.address_line1, address.address_line2, address.city,
                    address.state, address.postal_code, address.country,
                ),
            )

            for item in items:
                cursor.execute(
                    """
                    UPDATE inventory
                    SET reserved_quantity = reserved_quantity + %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE inventory_id = %s
                      AND total_quantity - reserved_quantity >= %s
                    RETURNING inventory_id
                    """,
                    (item["quantity"], item["inventory_id"], item["quantity"]),
                )
                if cursor.fetchone() is None:
                    raise CheckoutInsufficientInventoryError(
                        item["sku"], item["quantity"], 0
                    )

            order_id = uuid4()
            cursor.execute(
                """
                INSERT INTO orders (
                    order_id, merchant_id, customer_id, quote_id,
                    shipping_address_id, subtotal, tax_amount, shipping_amount,
                    total_amount, currency, order_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'PENDING_PAYMENT')
                """,
                (
                    order_id, settings.merchant_id, customer_id, request.quote_id,
                    address_id, quote["subtotal"], quote["tax_amount"],
                    quote["shipping_amount"], quote["total_amount"], quote["currency"],
                ),
            )

            for item in items:
                cursor.execute(
                    """
                    INSERT INTO order_items (
                        order_item_id, order_id, product_id, sku, product_name,
                        quantity, unit_price, total_price, line_subtotal,
                        discount_amount, gst_rate_snapshot, tax_amount
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        uuid4(), order_id, item["product_id"], item["sku"],
                        item["product_name"], item["quantity"],
                        item["unit_price_snapshot"], item["line_total"],
                        item["line_subtotal"], item["discount_amount"],
                        item["gst_rate_snapshot"], item["tax_amount"],
                    ),
                )

            cursor.execute(
                """
                UPDATE quotes SET status = 'CONSUMED'
                WHERE quote_id = %s AND status = 'ACTIVE'
                RETURNING quote_id
                """,
                (request.quote_id,),
            )
            if cursor.fetchone() is None:
                raise CheckoutQuoteStatusError("NOT_ACTIVE")

            response = CheckoutResponse(
                order_id=order_id,
                quote_id=request.quote_id,
                status=OrderStatus.PENDING_PAYMENT,
                subtotal=quote["subtotal"],
                tax=quote["tax_amount"],
                shipping=quote["shipping_amount"],
                total=quote["total_amount"],
                currency=quote["currency"],
            )
            cursor.execute(
                """
                UPDATE idempotency_keys
                SET response_status = 201, response_body = %s
                WHERE idempotency_key = %s
                """,
                (Jsonb(response.model_dump(mode="json")), idempotency_key),
            )

    return response
