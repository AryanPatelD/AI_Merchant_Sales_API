"""Schemas for product search requests and responses."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.catalog import CatalogProduct


class SearchSortField(StrEnum):
    RELEVANCE = "relevance"
    PRICE = "price"
    NAME = "name"
    SKU = "sku"


class SearchResult(CatalogProduct):
    """Catalog product with its deterministic keyword relevance score."""

    relevance_score: int = Field(ge=0)


class ProductSearchResponse(BaseModel):
    """Normalized product search response."""

    model_config = ConfigDict(frozen=True)

    query: str
    normalized_query: str
    results: list[SearchResult]
    total_matches: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)

