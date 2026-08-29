"""API and normalization tests for product search."""

from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.search import ProductSearchResponse, SearchResult
from app.services.search import normalize_query


client = TestClient(app)

RESULT = SearchResult(
    sku="TS-MOU-M1",
    name="Wireless Mouse M1",
    description="Ergonomic 2.4 GHz wireless optical mouse",
    category="Computer Accessories",
    brand="TechStore",
    price=Decimal("799.00"),
    currency="INR",
    status="ACTIVE",
    active=True,
    relevance_score=60,
)


def test_normalize_query() -> None:
    assert normalize_query("  wireless   mouse  ") == "wireless mouse"


def test_search_forwards_query_and_filters(monkeypatch) -> None:
    captured = {}

    def fake_search(settings, query, filters) -> ProductSearchResponse:
        captured["query"] = query
        captured["filters"] = filters
        return ProductSearchResponse(
            query=query,
            normalized_query=normalize_query(query),
            results=[RESULT],
            total_matches=1,
            limit=filters.limit,
        )

    monkeypatch.setattr("app.api.search.search_products", fake_search)

    response = client.get(
        "/api/v1/search",
        params={
            "q": "  wireless   mouse  ",
            "category": "Computer Accessories",
            "brand": "TechStore",
            "min_price": "500",
            "max_price": "1000",
            "sort_by": "price",
            "sort_order": "asc",
            "limit": 5,
        },
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["price"] == 799.0
    assert captured["query"] == "  wireless   mouse  "
    assert captured["filters"].min_price == Decimal("500")
    assert captured["filters"].max_price == Decimal("1000")
    assert captured["filters"].limit == 5


def test_search_rejects_whitespace_query() -> None:
    response = client.get("/api/v1/search", params={"q": "   "})

    assert response.status_code == 422
    assert response.json() == {
        "detail": "q must contain at least one non-whitespace character"
    }


def test_search_rejects_inverted_price_range() -> None:
    response = client.get(
        "/api/v1/search",
        params={"q": "mouse", "min_price": "1000", "max_price": "500"},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "min_price cannot be greater than max_price"}


def test_search_requires_query() -> None:
    response = client.get("/api/v1/search")

    assert response.status_code == 422
