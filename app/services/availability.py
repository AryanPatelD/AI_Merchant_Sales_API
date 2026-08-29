"""Read-only product inventory availability service."""

from app.config import Settings
from app.database.connection import database_connection
from app.schemas.availability import ProductAvailability


class AvailabilityProductNotFoundError(Exception):
    """Raised when the merchant does not have the requested SKU."""


class AvailabilityProductInactiveError(Exception):
    """Raised when the requested product is not active."""


class InventoryNotConfiguredError(Exception):
    """Raised when an active product has no inventory record."""


def get_product_availability(
    settings: Settings,
    sku: str,
    requested_quantity: int | None = None,
) -> ProductAvailability:
    """Compute availability without reserving or mutating inventory."""
    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    p.sku,
                    p.status,
                    i.inventory_id,
                    i.total_quantity,
                    i.reserved_quantity,
                    i.eta_days
                FROM products AS p
                LEFT JOIN inventory AS i ON i.product_id = p.product_id
                WHERE p.merchant_id = %s AND p.sku = %s
                """,
                (settings.merchant_id, sku),
            )
            row = cursor.fetchone()

    if row is None:
        raise AvailabilityProductNotFoundError
    if row["status"].upper() != "ACTIVE":
        raise AvailabilityProductInactiveError
    if row["inventory_id"] is None:
        raise InventoryNotConfiguredError

    available_quantity = row["total_quantity"] - row["reserved_quantity"]
    requested_quantity_available = (
        available_quantity >= requested_quantity
        if requested_quantity is not None
        else None
    )

    return ProductAvailability(
        sku=row["sku"],
        in_stock=available_quantity > 0,
        available_quantity=available_quantity,
        eta_days=row["eta_days"],
        requested_quantity=requested_quantity,
        requested_quantity_available=requested_quantity_available,
    )

