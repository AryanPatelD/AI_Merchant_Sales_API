"""API tests for inventory availability."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.availability import ProductAvailability
from app.services.availability import (
    AvailabilityProductInactiveError,
    AvailabilityProductNotFoundError,
    InventoryNotConfiguredError,
)


client = TestClient(app)


def test_product_availability_with_requested_quantity(monkeypatch) -> None:
    captured = {}

    def fake_availability(settings, sku, requested_quantity) -> ProductAvailability:
        captured["sku"] = sku
        captured["quantity"] = requested_quantity
        return ProductAvailability(
            sku=sku,
            in_stock=True,
            available_quantity=12,
            eta_days=2,
            requested_quantity=requested_quantity,
            requested_quantity_available=True,
        )

    monkeypatch.setattr(
        "app.api.availability.get_product_availability",
        fake_availability,
    )

    response = client.get(
        "/api/v1/availability",
        params={"sku": "TS-MOU-M1", "quantity": 3},
    )

    assert response.status_code == 200
    assert response.json() == {
        "sku": "TS-MOU-M1",
        "in_stock": True,
        "available_quantity": 12,
        "eta_days": 2,
        "requested_quantity": 3,
        "requested_quantity_available": True,
    }
    assert captured == {"sku": "TS-MOU-M1", "quantity": 3}


def test_product_availability_rejects_invalid_quantity() -> None:
    response = client.get(
        "/api/v1/availability",
        params={"sku": "TS-MOU-M1", "quantity": 0},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("service_error", "expected_status", "expected_detail"),
    [
        (
            AvailabilityProductNotFoundError(),
            404,
            "Product SKU was not found",
        ),
        (
            AvailabilityProductInactiveError(),
            409,
            "Product is not active",
        ),
        (
            InventoryNotConfiguredError(),
            503,
            "Inventory is not configured for this product",
        ),
    ],
)
def test_product_availability_errors(
    monkeypatch,
    service_error: Exception,
    expected_status: int,
    expected_detail: str,
) -> None:
    def raise_service_error(settings, sku, requested_quantity) -> None:
        raise service_error

    monkeypatch.setattr(
        "app.api.availability.get_product_availability",
        raise_service_error,
    )

    response = client.get(
        "/api/v1/availability",
        params={"sku": "TS-MOU-M1"},
    )

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}
