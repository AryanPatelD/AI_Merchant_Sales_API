"""Product catalog query service."""

from dataclasses import dataclass
from decimal import Decimal
from math import ceil

from app.config import Settings
from app.database.connection import database_connection
from app.schemas.catalog import (
    CatalogPage,
    CatalogProduct,
    CatalogSortField,
    SortOrder,
)


class ProductNotFoundError(Exception):
    """Raised when an active product cannot be found by SKU."""


@dataclass(frozen=True)
class CatalogFilters:
    page: int = 1
    page_size: int = 20
    category: str | None = None
    brand: str | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    sort_by: CatalogSortField = CatalogSortField.NAME
    sort_order: SortOrder = SortOrder.ASC


PRODUCT_COLUMNS = """
    sku, name, description, category, brand, price, currency, status,
    (status = 'ACTIVE') AS active
"""

SORT_COLUMNS = {
    CatalogSortField.NAME: "name",
    CatalogSortField.PRICE: "price",
    CatalogSortField.CATEGORY: "category",
    CatalogSortField.BRAND: "brand",
    CatalogSortField.SKU: "sku",
}


def _where_clause(
    settings: Settings,
    filters: CatalogFilters,
) -> tuple[str, list[object]]:
    conditions = ["merchant_id = %s", "status = 'ACTIVE'"]
    parameters: list[object] = [settings.merchant_id]

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


def list_catalog(settings: Settings, filters: CatalogFilters) -> CatalogPage:
    """Return a filtered, deterministic page of active merchant products."""
    where_clause, parameters = _where_clause(settings, filters)
    sort_column = SORT_COLUMNS[filters.sort_by]
    sort_direction = "DESC" if filters.sort_order is SortOrder.DESC else "ASC"
    offset = (filters.page - 1) * filters.page_size

    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT COUNT(*) AS total FROM products WHERE {where_clause}",
                parameters,
            )
            total_items = cursor.fetchone()["total"]

            cursor.execute(
                f"""
                SELECT {PRODUCT_COLUMNS}
                FROM products
                WHERE {where_clause}
                ORDER BY {sort_column} {sort_direction}, sku ASC
                LIMIT %s OFFSET %s
                """,
                [*parameters, filters.page_size, offset],
            )
            items = [CatalogProduct(**row) for row in cursor.fetchall()]

    return CatalogPage(
        items=items,
        page=filters.page,
        page_size=filters.page_size,
        total_items=total_items,
        total_pages=ceil(total_items / filters.page_size) if total_items else 0,
    )


def get_product_by_sku(settings: Settings, sku: str) -> CatalogProduct:
    """Return one active merchant product by stable, case-sensitive SKU."""
    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT {PRODUCT_COLUMNS}
                FROM products
                WHERE merchant_id = %s AND sku = %s AND status = 'ACTIVE'
                """,
                (settings.merchant_id, sku),
            )
            row = cursor.fetchone()

    if row is None:
        raise ProductNotFoundError
    return CatalogProduct(**row)

