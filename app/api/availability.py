"""Inventory availability routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config import Settings, get_settings
from app.schemas.availability import ProductAvailability
from app.schemas.discovery import ErrorResponse
from app.services.availability import (
    AvailabilityProductInactiveError,
    AvailabilityProductNotFoundError,
    InventoryNotConfiguredError,
    get_product_availability,
)

router = APIRouter(prefix="/availability", tags=["Availability"])


@router.get(
    "",
    response_model=ProductAvailability,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
    summary="Check product availability",
)
def product_availability(
    sku: str = Query(..., min_length=1, max_length=100),
    quantity: int | None = Query(None, ge=1),
    settings: Settings = Depends(get_settings),
) -> ProductAvailability:
    """Return current stock availability without reserving inventory."""
    try:
        return get_product_availability(settings, sku, quantity)
    except AvailabilityProductNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product SKU was not found",
        ) from error
    except AvailabilityProductInactiveError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product is not active",
        ) from error
    except InventoryNotConfiguredError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Inventory is not configured for this product",
        ) from error
