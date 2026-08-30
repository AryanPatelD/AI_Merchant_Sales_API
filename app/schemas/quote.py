"""Schemas for non-persistent quote calculation."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class QuoteStatus(StrEnum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CONSUMED = "CONSUMED"
    CANCELLED = "CANCELLED"


class ShippingType(StrEnum):
    SAME_STATE = "SAME_STATE"
    INTER_STATE = "INTER_STATE"
    INTERNATIONAL = "INTERNATIONAL"


class QuoteRequestItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    sku: str = Field(min_length=1, max_length=100)
    quantity: int = Field(ge=1, le=1000)

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("sku must contain at least one non-whitespace character")
        return value


class ShippingAddress(BaseModel):
    model_config = ConfigDict(frozen=True)

    state: str = Field(min_length=1, max_length=100)
    country: str = Field(min_length=2, max_length=100)

    @field_validator("state", "country")
    @classmethod
    def normalize_location(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("location must contain non-whitespace characters")
        return value


class QuoteRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[QuoteRequestItem] = Field(min_length=1, max_length=50)
    shipping_address: ShippingAddress

    @model_validator(mode="after")
    def reject_duplicate_skus(self) -> "QuoteRequest":
        normalized = [item.sku.casefold() for item in self.items]
        if len(normalized) != len(set(normalized)):
            raise ValueError("duplicate SKUs are not allowed")
        return self


class QuotedItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    sku: str
    quantity: int = Field(ge=1)
    unit_price: Decimal = Field(ge=0, decimal_places=2)
    line_subtotal: Decimal = Field(ge=0, decimal_places=2)
    discount: Decimal = Field(ge=0, decimal_places=2)
    taxable_amount: Decimal = Field(ge=0, decimal_places=2)
    gst_rate: Decimal = Field(ge=0, le=100)
    tax: Decimal = Field(ge=0, decimal_places=2)


class QuotePricing(BaseModel):
    model_config = ConfigDict(frozen=True)

    subtotal: Decimal = Field(ge=0, decimal_places=2)
    discount: Decimal = Field(ge=0, decimal_places=2)
    taxable_amount: Decimal = Field(ge=0, decimal_places=2)
    tax: Decimal = Field(ge=0, decimal_places=2)
    shipping: Decimal = Field(ge=0, decimal_places=2)
    total: Decimal = Field(ge=0, decimal_places=2)


class QuoteResponse(BaseModel):
    """An expiring calculation; persistence is intentionally deferred."""

    model_config = ConfigDict(frozen=True)

    quote_id: UUID
    currency: str = Field(min_length=3, max_length=3)
    items: list[QuotedItem]
    pricing: QuotePricing
    shipping_type: ShippingType
    status: QuoteStatus
    valid_for_seconds: int = Field(ge=1)
    expires_at: datetime
    pricing_explanation: list[str]
