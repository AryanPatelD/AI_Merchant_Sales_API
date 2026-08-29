"""Schemas for catalog requests and responses."""

from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer


JsonMoney = Annotated[
    Decimal,
    PlainSerializer(lambda value: float(value), return_type=float, when_used="json"),
]


class CatalogSortField(StrEnum):
    NAME = "name"
    PRICE = "price"
    CATEGORY = "category"
    BRAND = "brand"
    SKU = "sku"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class CatalogProduct(BaseModel):
    """Normalized active product returned to an AI buyer."""

    model_config = ConfigDict(frozen=True)

    sku: str
    name: str
    description: str | None
    category: str | None
    brand: str | None
    price: JsonMoney
    currency: str
    status: str
    active: bool


class CatalogPage(BaseModel):
    """Paginated collection of catalog products."""

    items: list[CatalogProduct]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)

