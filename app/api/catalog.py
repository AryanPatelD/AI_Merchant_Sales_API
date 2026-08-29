"""Product catalog routes."""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config import Settings, get_settings
from app.schemas.catalog import (
    CatalogPage,
    CatalogProduct,
    CatalogSortField,
    SortOrder,
)
from app.schemas.discovery import ErrorResponse
from app.services.catalog import (
    CatalogFilters,
    ProductNotFoundError,
    get_product_by_sku,
    list_catalog,
)

router = APIRouter(prefix="/catalog", tags=["Catalog"])


@router.get("", response_model=CatalogPage, summary="List active catalog products")
def catalog_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = Query(None, min_length=1, max_length=150),
    brand: str | None = Query(None, min_length=1, max_length=150),
    min_price: Decimal | None = Query(None, ge=0),
    max_price: Decimal | None = Query(None, ge=0),
    sort_by: CatalogSortField = CatalogSortField.NAME,
    sort_order: SortOrder = SortOrder.ASC,
    settings: Settings = Depends(get_settings),
) -> CatalogPage:
    """Return a validated and filtered page of active products."""
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="min_price cannot be greater than max_price",
        )

    return list_catalog(
        settings,
        CatalogFilters(
            page=page,
            page_size=page_size,
            category=category,
            brand=brand,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
            sort_order=sort_order,
        ),
    )


@router.get(
    "/{sku}",
    response_model=CatalogProduct,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
    summary="Get an active product by SKU",
)
def catalog_detail(
    sku: str,
    settings: Settings = Depends(get_settings),
) -> CatalogProduct:
    """Return one active product identified by its stable SKU."""
    try:
        return get_product_by_sku(settings, sku)
    except ProductNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active product was not found",
        ) from error
