"""AI-commerce merchant discovery routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.schemas.discovery import ErrorResponse, MerchantDiscoveryManifest
from app.services.discovery import (
    MerchantInactiveError,
    MerchantNotFoundError,
    MerchantVersionMismatchError,
    get_merchant_manifest,
)

router = APIRouter(prefix="/.well-known", tags=["Discovery"])


@router.get(
    "/ai-commerce",
    response_model=MerchantDiscoveryManifest,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
    summary="Discover AI-commerce support",
)
def merchant_discovery(
    settings: Settings = Depends(get_settings),
) -> MerchantDiscoveryManifest:
    """Return the validated manifest for the configured active merchant."""
    try:
        return get_merchant_manifest(settings)
    except MerchantNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configured merchant was not found",
        ) from error
    except MerchantInactiveError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Merchant is not active",
        ) from error
    except MerchantVersionMismatchError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Merchant API version is not supported by this application",
        ) from error
