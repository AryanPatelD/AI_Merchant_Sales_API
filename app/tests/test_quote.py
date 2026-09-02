"""API and pricing tests for non-persistent quotes."""

from contextlib import contextmanager
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.quote import QuoteRequest, QuoteResponse
from app.services.quote import (
    QuoteInsufficientInventoryError,
    create_quote,
    shipping_amount,
    shipping_type,
)

client = TestClient(app)
IDEMPOTENCY_HEADERS = {"Idempotency-Key": "quote-test-key"}


@pytest.fixture(autouse=True)
def bypass_idempotency_storage(monkeypatch):
    monkeypatch.setattr(
        "app.api.quote.run_idempotent",
        lambda key, endpoint, response_type, operation: operation(),
    )


def quote_payload() -> dict:
    return {
        "items": [{"sku": "TS-MOU-M1", "quantity": 2}],
        "shipping_address": {"state": "Maharashtra", "country": "India"},
    }


def test_quote_route_returns_calculated_response(monkeypatch) -> None:
    captured = {}

    def fake_create(settings, request) -> QuoteResponse:
        captured["request"] = request
        return QuoteResponse.model_validate(
            {
                "quote_id": "41d189fb-78ab-46ab-b531-c7e8ef84e18e",
                "currency": "INR",
                "items": [{
                    "sku": "TS-MOU-M1", "product_name": "Wireless Mouse M1",
                    "quantity": 2, "unit_price": "800.00",
                    "line_subtotal": "1600.00", "discount": "80.00",
                    "discount_type": "PERCENTAGE", "discount_value": "5.00",
                    "discount_rate": "5.00",
                    "taxable_amount": "1520.00", "gst_rate": "18", "tax": "273.60",
                    "line_total": "1793.60",
                }],
                "pricing": {
                    "subtotal": "1600.00", "discount": "80.00",
                    "taxable_amount": "1520.00", "tax": "273.60",
                    "shipping": "0.00", "total": "1793.60",
                },
                "shipping_type": "INTER_STATE", "status": "ACTIVE",
                "valid_for_seconds": 300,
                "created_at": "2026-08-30T11:55:00Z",
                "expires_at": "2026-08-30T12:00:00Z",
                "pricing_explanation": ["Explainable pricing"],
            }
        )

    monkeypatch.setattr("app.api.quote.create_quote", fake_create)
    response = client.post("/api/v1/quote", json=quote_payload(), headers=IDEMPOTENCY_HEADERS)

    assert response.status_code == 201
    assert response.json()["pricing"]["total"] == "1793.60"
    assert response.json()["status"] == "ACTIVE"
    assert captured["request"].items[0].quantity == 2


def test_quote_requires_idempotency_key() -> None:
    response = client.post("/api/v1/quote", json=quote_payload())
    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {"items": [], "shipping_address": {"state": "Gujarat", "country": "India"}},
        {"items": [{"sku": " ", "quantity": 1}], "shipping_address": {"state": "Gujarat", "country": "India"}},
        {"items": [{"sku": "A", "quantity": 0}], "shipping_address": {"state": "Gujarat", "country": "India"}},
        {"items": [{"sku": "A", "quantity": 1}, {"sku": "a", "quantity": 2}], "shipping_address": {"state": "Gujarat", "country": "India"}},
    ],
)
def test_quote_rejects_invalid_requests(payload: dict) -> None:
    assert client.post("/api/v1/quote", json=payload).status_code == 422


def test_quote_maps_insufficient_inventory(monkeypatch) -> None:
    def fail(settings, request):
        raise QuoteInsufficientInventoryError("TS-MOU-M1", 50, 36)

    monkeypatch.setattr("app.api.quote.create_quote", fail)
    response = client.post("/api/v1/quote", json=quote_payload(), headers=IDEMPOTENCY_HEADERS)
    assert response.status_code == 409
    assert response.json() == {
        "detail": "Insufficient inventory for TS-MOU-M1: requested 50, available 36"
    }


class FakeCursor:
    def __init__(self, rows: list[dict], discount_rule: dict) -> None:
        self.rows = rows
        self.discount_rule = discount_rule
        self.statements: list[str] = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def execute(self, statement, parameters) -> None:
        self.statements.append(statement.strip())

    def fetchall(self) -> list[dict]:
        return self.rows

    def fetchone(self) -> dict:
        return self.discount_rule


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self.fake_cursor = cursor

    def cursor(self) -> FakeCursor:
        return self.fake_cursor


def test_create_quote_calculates_and_persists_snapshots(monkeypatch) -> None:
    cursor = FakeCursor(
        [{
            "product_id": UUID(int=3), "sku": "TS-MOU-M1",
            "name": "Wireless Mouse M1", "status": "ACTIVE",
            "category": "Computer Accessories", "price": Decimal("800.00"),
            "currency": "INR", "tax_rate": Decimal("18.00"),
            "tax_name": "GST",
            "merchant_currency": "INR", "merchant_country": "IN",
            "origin_state": "Gujarat",
            "shipping_rules": {
                "INTER_STATE": {
                    "free_shipping_threshold": 1000,
                    "base_charge": 80,
                    "additional_item_charge": 0,
                }
            },
            "inventory_id": UUID(int=1),
            "total_quantity": 10, "reserved_quantity": 2,
        }],
        {
            "rule_name": "Standard 5%",
            "discount_type": "PERCENTAGE",
            "discount_value": Decimal("5.00"),
            "max_discount_amount": None,
        },
    )

    @contextmanager
    def fake_connection():
        yield FakeConnection(cursor)

    monkeypatch.setattr("app.services.quote.database_connection", fake_connection)
    settings = SimpleNamespace(
        merchant_id=UUID(int=2), quote_validity_seconds=300
    )
    result = create_quote(settings, QuoteRequest.model_validate(quote_payload()))

    assert result.pricing.subtotal == Decimal("1600.00")
    assert result.pricing.discount == Decimal("80.00")
    assert result.pricing.taxable_amount == Decimal("1520.00")
    assert result.pricing.tax == Decimal("273.60")
    assert result.pricing.shipping == Decimal("0.00")
    assert result.pricing.total == Decimal("1793.60")
    assert result.items[0].unit_price == Decimal("800.00")
    assert result.items[0].product_name == "Wireless Mouse M1"
    assert result.items[0].line_total == Decimal("1793.60")
    assert result.shipping_type == "INTER_STATE"
    assert result.valid_for_seconds == 300
    assert len(cursor.statements) == 4
    assert all(statement.upper().startswith("SELECT") for statement in cursor.statements[:2])
    assert all(statement.upper().startswith("INSERT") for statement in cursor.statements[2:])


def test_shipping_policy() -> None:
    assert shipping_type("India", "Gujarat", "IN", "Gujarat") == "SAME_STATE"
    domestic = {
        "free_shipping_threshold": 500,
        "base_charge": 40,
        "additional_item_charge": 0,
    }
    international = {
        "free_shipping_threshold": None,
        "base_charge": 500,
        "additional_item_charge": 100,
    }
    assert shipping_amount(domestic, Decimal("499.99"), 1) == Decimal("40")
    assert shipping_amount(domestic, Decimal("500.00"), 1) == Decimal("0.00")
    assert shipping_amount(international, Decimal("2000"), 3) == Decimal("700")
