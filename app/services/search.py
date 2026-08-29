"""Ranked SQL keyword search for active merchant products."""

import re
from dataclasses import dataclass
from decimal import Decimal

from app.config import Settings
from app.database.connection import database_connection
from app.schemas.catalog import SortOrder
from app.schemas.search import ProductSearchResponse, SearchResult, SearchSortField


@dataclass(frozen=True)
class SearchFilters:
    category: str | None = None
    brand: str | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    sort_by: SearchSortField = SearchSortField.RELEVANCE
    sort_order: SortOrder = SortOrder.DESC
    limit: int = 20


SORT_COLUMNS = {
    SearchSortField.RELEVANCE: "relevance_score",
    SearchSortField.PRICE: "price",
    SearchSortField.NAME: "name",
    SearchSortField.SKU: "sku",
}


def normalize_query(query: str) -> str:
    """Trim and collapse repeated whitespace for reproducible searching."""
    return re.sub(r"\s+", " ", query).strip()


def _where_clause(
    settings: Settings,
    tokens: list[str],
    filters: SearchFilters,
) -> tuple[str, list[object]]:
    conditions = ["merchant_id = %s", "status = 'ACTIVE'"]
    parameters: list[object] = [settings.merchant_id]

    # Every query token must occur somewhere in the searchable product text.
    for token in tokens:
        conditions.append(
            "concat_ws(' ', name, description, category, brand) ILIKE %s"
        )
        parameters.append(f"%{token}%")

    if filters.category:
        conditions.append("LOWER(category) = LOWER(%s)")
        parameters.append(filters.category)
    if filters.brand:
        conditions.append("LOWER(brand) = LOWER(%s)")
        parameters.append(filters.brand)
    if filters.min_price is not None:
        conditions.append("price >= %s")
        parameters.append(filters.min_price)
    if filters.max_price is not None:
        conditions.append("price <= %s")
        parameters.append(filters.max_price)

    return " AND ".join(conditions), parameters


def search_products(
    settings: Settings,
    query: str,
    filters: SearchFilters,
) -> ProductSearchResponse:
    """Search and consistently rank active products using PostgreSQL ILIKE."""
    normalized_query = normalize_query(query)
    tokens = normalized_query.split(" ")
    where_clause, where_parameters = _where_clause(settings, tokens, filters)

    exact = normalized_query
    prefix = f"{normalized_query}%"
    contains = f"%{normalized_query}%"
    score_parameters = [exact, prefix, contains, contains, contains, contains]

    sort_column = SORT_COLUMNS[filters.sort_by]
    sort_direction = "DESC" if filters.sort_order is SortOrder.DESC else "ASC"

    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT COUNT(*) AS total FROM products WHERE {where_clause}",
                where_parameters,
            )
            total_matches = cursor.fetchone()["total"]

            cursor.execute(
                f"""
                SELECT
                    sku, name, description, category, brand, price, currency,
                    status, (status = 'ACTIVE') AS active,
                    CASE
                        WHEN LOWER(name) = LOWER(%s) THEN 100
                        WHEN name ILIKE %s THEN 80
                        WHEN name ILIKE %s THEN 60
                        WHEN description ILIKE %s THEN 40
                        WHEN category ILIKE %s THEN 30
                        WHEN brand ILIKE %s THEN 20
                        ELSE 10
                    END AS relevance_score
                FROM products
                WHERE {where_clause}
                ORDER BY {sort_column} {sort_direction}, name ASC, sku ASC
                LIMIT %s
                """,
                [*score_parameters, *where_parameters, filters.limit],
            )
            results = [SearchResult(**row) for row in cursor.fetchall()]

    return ProductSearchResponse(
        query=query,
        normalized_query=normalized_query,
        results=results,
        total_matches=total_matches,
        limit=filters.limit,
    )

