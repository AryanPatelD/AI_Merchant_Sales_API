"""Schemas for Razorpay payment order creation and webhooks."""

from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PaymentStatus(StrEnum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    order_id: UUID


class PaymentResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    payment_id: UUID
    order_id: UUID
    gateway: str
    gateway_order_id: str
    key_id: str
    amount: Decimal = Field(gt=0, decimal_places=2)
    amount_subunits: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    status: PaymentStatus


class WebhookResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: str
    event_type: str
    processing_status: str
    duplicate: bool = False
