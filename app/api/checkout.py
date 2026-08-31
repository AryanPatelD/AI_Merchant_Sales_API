"""Checkout and order-creation routes."""

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.config import Settings, get_settings
from app.schemas.checkout import CheckoutRequest, CheckoutResponse
from app.schemas.discovery import ErrorResponse
from app.services.checkout import (
    CheckoutAddressMismatchError,
    CheckoutIdempotencyConflictError,
    CheckoutInsufficientInventoryError,
    CheckoutInventoryNotConfiguredError,
    CheckoutQuoteExpiredError,
    CheckoutQuoteNotFoundError,
    CheckoutQuoteStatusError,
    checkout,
)

router = APIRouter(prefix="/checkout", tags=["Checkout"])


@router.post(
    "",
    response_model=CheckoutResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
    summary="Atomically create an order from a quote",
)
def create_order(
    request: CheckoutRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=255),
    settings: Settings = Depends(get_settings),
) -> CheckoutResponse:
    try:
        return checkout(settings, request, idempotency_key)
    except CheckoutQuoteNotFoundError as error:
        raise HTTPException(404, "Quote was not found") from error
    except CheckoutQuoteExpiredError as error:
        raise HTTPException(409, "Quote has expired") from error
    except CheckoutQuoteStatusError as error:
        raise HTTPException(409, f"Quote cannot be checked out with status {error.status}") from error
    except CheckoutAddressMismatchError as error:
        raise HTTPException(409, "Shipping address does not match the quoted location") from error
    except CheckoutInventoryNotConfiguredError as error:
        raise HTTPException(503, f"Inventory is not configured for product: {error.sku}") from error
    except CheckoutInsufficientInventoryError as error:
        raise HTTPException(
            409,
            f"Insufficient inventory for {error.sku}: requested {error.requested}, available {error.available}",
        ) from error
    except CheckoutIdempotencyConflictError as error:
        raise HTTPException(409, "Idempotency key is already used by another request") from error
