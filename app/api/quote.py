"""Quote and pricing routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.schemas.discovery import ErrorResponse
from app.schemas.quote import QuoteRequest, QuoteResponse
from app.services.quote import (
    QuoteCurrencyMismatchError,
    QuoteDiscountRuleNotConfiguredError,
    QuoteInsufficientInventoryError,
    QuoteInventoryNotConfiguredError,
    QuoteProductInactiveError,
    QuoteProductNotFoundError,
    QuoteShippingRuleNotConfiguredError,
    QuoteTaxRuleNotConfiguredError,
    create_quote,
)

router = APIRouter(prefix="/quote", tags=["Quotes"])


@router.post(
    "",
    response_model=QuoteResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
    summary="Create a non-persistent price quote",
)
def quote(
    request: QuoteRequest,
    settings: Settings = Depends(get_settings),
) -> QuoteResponse:
    """Validate stock and calculate an expiring quote without reserving it."""
    try:
        return create_quote(settings, request)
    except QuoteProductNotFoundError as error:
        raise HTTPException(404, f"Product SKU was not found: {error.sku}") from error
    except QuoteProductInactiveError as error:
        raise HTTPException(409, f"Product is not active: {error.sku}") from error
    except QuoteInventoryNotConfiguredError as error:
        raise HTTPException(
            503, f"Inventory is not configured for product: {error.sku}"
        ) from error
    except QuoteInsufficientInventoryError as error:
        raise HTTPException(
            409,
            f"Insufficient inventory for {error.sku}: requested {error.requested}, available {error.available}",
        ) from error
    except QuoteCurrencyMismatchError as error:
        raise HTTPException(409, "Product currency is not supported for this quote") from error
    except QuoteShippingRuleNotConfiguredError as error:
        raise HTTPException(
            503, f"Shipping rule is not configured for {error.shipping_type.value}"
        ) from error
    except QuoteTaxRuleNotConfiguredError as error:
        raise HTTPException(
            503, f"Tax rule is not configured for product category: {error.category}"
        ) from error
    except QuoteDiscountRuleNotConfiguredError as error:
        raise HTTPException(
            503, "Discount rule is not configured for this subtotal"
        ) from error
