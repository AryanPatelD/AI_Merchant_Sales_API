"""API tests for catalog management."""

from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.catalog import CatalogPage, CatalogProduct
from app.services.catalog import ProductNotFoundError


client = TestClient(app)

PRODUCT = CatalogProduct(
    sku="TS-MOU-M1",
    name="Wireless Mouse M1",
    description="Ergonomic wireless mouse",
    category="Computer Accessories",
    brand="TechStore",
    price=Decimal("799.00"),
    currency="INR",
    status="ACTIVE",
    active=True,
)


def test_catalog_list_forwards_filters(monkeypatch) -> None:
    captured = {}

    def fake_list(settings, filters) -> CatalogPage:
        captured["filters"] = filters
        return CatalogPage(
            items=[PRODUCT],
            page=filters.page,
            page_size=filters.page_size,
            total_items=1,
            total_pages=1,
        )

    monkeypatch.setattr("app.api.catalog.list_catalog", fake_list)

    response = client.get(
        "/api/v1/catalog",
        params={
            "page": 2,
            "page_size": 5,
            "category": "Computer Accessories",
            "brand": "TechStore",
            "min_price": "500",
            "max_price": "1000",
            "sort_by": "price",
            "sort_order": "desc",
        },
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["price"] == 799.0
    assert captured["filters"].page == 2
    assert captured["filters"].page_size == 5
    assert captured["filters"].min_price == Decimal("500")
    assert captured["filters"].max_price == Decimal("1000")
    assert captured["filters"].sort_by == "price"
    assert captured["filters"].sort_order == "desc"


def test_catalog_rejects_inverted_price_range() -> None:
    response = client.get(
        "/api/v1/catalog",
        params={"min_price": "1000", "max_price": "500"},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "min_price cannot be greater than max_price"}


def test_catalog_detail(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.catalog.get_product_by_sku",
        lambda settings, sku: PRODUCT,
    )

    response = client.get("/api/v1/catalog/TS-MOU-M1")

    assert response.status_code == 200
    assert response.json()["sku"] == "TS-MOU-M1"


def test_catalog_detail_returns_404(monkeypatch) -> None:
    def missing_product(settings, sku) -> None:
        raise ProductNotFoundError

    monkeypatch.setattr("app.api.catalog.get_product_by_sku", missing_product)

    response = client.get("/api/v1/catalog/DOES-NOT-EXIST")

    assert response.status_code == 404
    assert response.json() == {"detail": "Active product was not found"}
