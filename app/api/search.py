"""Product search routes."""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config import Settings, get_settings
from app.schemas.catalog import SortOrder
from app.schemas.search import ProductSearchResponse, SearchSortField
from app.services.search import (
    SearchFilters,
    normalize_query,
    search_products,
)

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=ProductSearchResponse, summary="Search products")
def product_search(
    q: str = Query(..., min_length=1, max_length=200),
    category: str | None = Query(None, min_length=1, max_length=150),
    brand: str | None = Query(None, min_length=1, max_length=150),
    min_price: Decimal | None = Query(None, ge=0),
    max_price: Decimal | None = Query(None, ge=0),
    sort_by: SearchSortField = SearchSortField.RELEVANCE,
    sort_order: SortOrder = SortOrder.DESC,
    limit: int = Query(20, ge=1, le=100),
    settings: Settings = Depends(get_settings),
) -> ProductSearchResponse:
    """Return consistently ranked active products matching the buyer query."""
    if not normalize_query(q):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="q must contain at least one non-whitespace character",
        )
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="min_price cannot be greater than max_price",
        )

    return search_products(
        settings,
        q,
        SearchFilters(
            category=category,
            brand=brand,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
        ),
    )
