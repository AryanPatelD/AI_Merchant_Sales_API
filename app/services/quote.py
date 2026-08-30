"""Read-only quote validation and pricing calculations."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from app.config import Settings
from app.database.connection import database_connection
from app.schemas.quote import (
    QuotePricing,
    QuoteRequest,
    QuoteResponse,
    QuoteStatus,
    QuotedItem,
    ShippingType,
)

MONEY = Decimal("0.01")


class QuoteProductNotFoundError(Exception):
    def __init__(self, sku: str) -> None:
        self.sku = sku


class QuoteProductInactiveError(Exception):
    def __init__(self, sku: str) -> None:
        self.sku = sku


class QuoteInventoryNotConfiguredError(Exception):
    def __init__(self, sku: str) -> None:
        self.sku = sku


class QuoteInsufficientInventoryError(Exception):
    def __init__(self, sku: str, requested: int, available: int) -> None:
        self.sku = sku
        self.requested = requested
        self.available = available


class QuoteCurrencyMismatchError(Exception):
    """Raised when requested products do not share the merchant currency."""


class QuoteShippingRuleNotConfiguredError(Exception):
    def __init__(self, shipping_type: ShippingType) -> None:
        self.shipping_type = shipping_type


class QuoteTaxRuleNotConfiguredError(Exception):
    def __init__(self, sku: str, category: str | None) -> None:
        self.sku = sku
        self.category = category


class QuoteDiscountRuleNotConfiguredError(Exception):
    """Raised when no active rule covers the calculated subtotal."""


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def shipping_type(
    country: str,
    state: str,
    merchant_country: str,
    merchant_state: str,
) -> ShippingType:
    country_codes = {"india": "in", "in": "in"}
    customer_country = country_codes.get(country.strip().casefold(), country.casefold())
    origin_country = country_codes.get(
        merchant_country.strip().casefold(), merchant_country.casefold()
    )
    if customer_country != origin_country:
        return ShippingType.INTERNATIONAL
    if state.strip().casefold() == merchant_state.strip().casefold():
        return ShippingType.SAME_STATE
    return ShippingType.INTER_STATE


def shipping_amount(
    rule: dict, discounted_subtotal: Decimal, item_count: int
) -> Decimal:
    threshold = rule["free_shipping_threshold"]
    if threshold is not None and discounted_subtotal >= Decimal(str(threshold)):
        return Decimal("0.00")
    return Decimal(str(rule["base_charge"])) + Decimal(
        str(rule["additional_item_charge"])
    ) * max(item_count - 1, 0)


def discount_amount(subtotal: Decimal, rule: dict) -> Decimal:
    value = Decimal(str(rule["discount_value"]))
    if rule["discount_type"] == "PERCENTAGE":
        discount = subtotal * value / 100
    else:
        discount = value
    maximum = rule["max_discount_amount"]
    if maximum is not None:
        discount = min(discount, Decimal(str(maximum)))
    return money(min(discount, subtotal))


def create_quote(settings: Settings, request: QuoteRequest) -> QuoteResponse:
    """Validate and price a quote without persisting or reserving inventory."""
    requested_by_sku = {item.sku: item.quantity for item in request.items}
    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT p.sku, p.status, p.category, p.price, p.currency,
                       tr.tax_rate, tr.tax_name,
                       i.inventory_id, i.total_quantity,
                       i.reserved_quantity, m.currency AS merchant_currency,
                       m.country_code AS merchant_country, m.origin_state,
                       COALESCE((
                           SELECT jsonb_object_agg(
                               sr.shipping_type,
                               jsonb_build_object(
                                   'free_shipping_threshold', sr.free_shipping_threshold,
                                   'base_charge', sr.base_charge,
                                   'additional_item_charge', sr.additional_item_charge
                               )
                           )
                           FROM merchant_shipping_rules AS sr
                           WHERE sr.merchant_id = m.merchant_id
                       ), '{}'::jsonb) AS shipping_rules
                FROM products AS p
                JOIN merchants AS m ON m.merchant_id = p.merchant_id
                LEFT JOIN LATERAL (
                    SELECT tax_rate, tax_name
                    FROM tax_rules
                    WHERE merchant_id = p.merchant_id
                      AND LOWER(category) = LOWER(p.category)
                      AND is_active = TRUE
                      AND LOWER(country) IN (LOWER(m.country_code), 'india')
                    ORDER BY updated_at DESC
                    LIMIT 1
                ) AS tr ON TRUE
                LEFT JOIN inventory AS i ON i.product_id = p.product_id
                WHERE p.merchant_id = %s AND p.sku = ANY(%s)
                """,
                (settings.merchant_id, list(requested_by_sku)),
            )
            rows_by_sku = {row["sku"]: row for row in cursor.fetchall()}

    quoted_items: list[QuotedItem] = []
    subtotal = Decimal("0.00")
    product_rows = []
    for request_item in request.items:
        row = rows_by_sku.get(request_item.sku)
        if row is None:
            raise QuoteProductNotFoundError(request_item.sku)
        if row["status"].upper() != "ACTIVE":
            raise QuoteProductInactiveError(request_item.sku)
        if row["inventory_id"] is None:
            raise QuoteInventoryNotConfiguredError(request_item.sku)
        available = row["total_quantity"] - row["reserved_quantity"]
        if available < request_item.quantity:
            raise QuoteInsufficientInventoryError(
                request_item.sku, request_item.quantity, available
            )
        if row["currency"].upper() != row["merchant_currency"].upper():
            raise QuoteCurrencyMismatchError
        if row["tax_rate"] is None:
            raise QuoteTaxRuleNotConfiguredError(request_item.sku, row["category"])
        line_subtotal = money(row["price"] * request_item.quantity)
        subtotal += line_subtotal
        product_rows.append((request_item, row, line_subtotal))

    subtotal = money(subtotal)
    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT rule_name, discount_type, discount_value,
                       max_discount_amount
                FROM discount_rules
                WHERE merchant_id = %s
                  AND is_active = TRUE
                  AND %s >= min_subtotal
                  AND (max_subtotal IS NULL OR %s <= max_subtotal)
                ORDER BY priority ASC, min_subtotal DESC
                LIMIT 1
                """,
                (settings.merchant_id, subtotal, subtotal),
            )
            discount_rule = cursor.fetchone()
    if discount_rule is None:
        raise QuoteDiscountRuleNotConfiguredError

    quote_discount = discount_amount(subtotal, discount_rule)
    total_discount = Decimal("0.00")
    total_taxable = Decimal("0.00")
    total_tax = Decimal("0.00")

    for index, (request_item, row, line_subtotal) in enumerate(product_rows):
        if index == len(product_rows) - 1:
            discount = money(quote_discount - total_discount)
        else:
            discount = money(quote_discount * line_subtotal / subtotal)
        taxable = money(line_subtotal - discount)
        rate = row["tax_rate"]
        tax = money(taxable * rate / 100)
        quoted_items.append(
            QuotedItem(
                sku=request_item.sku,
                quantity=request_item.quantity,
                unit_price=money(row["price"]),
                line_subtotal=line_subtotal,
                discount=discount,
                taxable_amount=taxable,
                gst_rate=rate,
                tax=tax,
            )
        )
        total_discount += discount
        total_taxable += taxable
        total_tax += tax

    total_discount = money(total_discount)
    total_taxable = money(total_taxable)
    total_tax = money(total_tax)
    kind = shipping_type(
        request.shipping_address.country,
        request.shipping_address.state,
        product_rows[0][1]["merchant_country"],
        product_rows[0][1]["origin_state"],
    )
    rules = product_rows[0][1]["shipping_rules"]
    rule = rules.get(kind.value)
    if rule is None:
        raise QuoteShippingRuleNotConfiguredError(kind)
    total_quantity = sum(item.quantity for item in request.items)
    shipping = money(shipping_amount(rule, total_taxable, total_quantity))
    total = money(total_taxable + total_tax + shipping)

    explanations = []
    explanations.append(
        f"{discount_rule['rule_name']} applied: {discount_rule['discount_type'].lower()} "
        f"discount value {discount_rule['discount_value']}"
    )
    for item in quoted_items:
        explanations.append(
            f"{item.gst_rate}% GST applied to discounted amount for {item.sku}"
        )
    if shipping == 0:
        explanations.append(
            f"Free {kind.value.lower().replace('_', ' ')} shipping threshold met"
        )
    elif kind is ShippingType.INTERNATIONAL:
        explanations.append(
            f"International shipping is INR {rule['base_charge']} plus INR "
            f"{rule['additional_item_charge']} per additional item"
        )
    else:
        explanations.append(f"{kind.value.lower().replace('_', ' ')} shipping is INR {shipping}")

    now = datetime.now(timezone.utc)
    return QuoteResponse(
        quote_id=uuid4(),
        currency=product_rows[0][1]["merchant_currency"].upper(),
        items=quoted_items,
        pricing=QuotePricing(
            subtotal=subtotal,
            discount=total_discount,
            taxable_amount=total_taxable,
            tax=total_tax,
            shipping=shipping,
            total=total,
        ),
        shipping_type=kind,
        status=QuoteStatus.ACTIVE,
        valid_for_seconds=settings.quote_validity_seconds,
        expires_at=now + timedelta(seconds=settings.quote_validity_seconds),
        pricing_explanation=explanations,
    )
