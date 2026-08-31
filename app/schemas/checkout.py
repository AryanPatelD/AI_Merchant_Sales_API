"""Schemas for atomic checkout and order creation."""

from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class Buyer(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=3, max_length=30)

    @model_validator(mode="after")
    def require_contact(self) -> "Buyer":
        if self.email is None and self.phone is None:
            raise ValueError("buyer email or phone is required")
        return self


class CheckoutShippingAddress(BaseModel):
    model_config = ConfigDict(frozen=True)

    recipient_name: str = Field(min_length=1, max_length=150)
    address_line1: str = Field(min_length=1, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(min_length=1, max_length=20)
    country: str = Field(default="India", min_length=2, max_length=100)


class CheckoutRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    quote_id: UUID
    buyer: Buyer
    shipping_address: CheckoutShippingAddress


class OrderStatus(StrEnum):
    PENDING_PAYMENT = "PENDING_PAYMENT"


class CheckoutResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    order_id: UUID
    quote_id: UUID
    status: OrderStatus
    subtotal: Decimal = Field(ge=0, decimal_places=2)
    tax: Decimal = Field(ge=0, decimal_places=2)
    shipping: Decimal = Field(ge=0, decimal_places=2)
    total: Decimal = Field(ge=0, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
