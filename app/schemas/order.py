"""Normalized order-status and fulfillment schemas."""

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.payment import PaymentStatus


class OrderLifecycleStatus(StrEnum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    PAID = "PAID"
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    RETURN_REQUESTED = "RETURN_REQUESTED"
    RETURNED = "RETURNED"
    REFUND_PENDING = "REFUND_PENDING"
    REFUNDED = "REFUNDED"


class TrackingDetails(BaseModel):
    model_config = ConfigDict(frozen=True)
    courier_name: str | None
    tracking_number: str | None
    shipment_status: str | None
    shipped_at: datetime | None
    delivered_at: datetime | None


class OrderStatusHistoryEntry(BaseModel):
    model_config = ConfigDict(frozen=True)
    previous_status: str | None
    status: OrderLifecycleStatus
    changed_at: datetime


class OrderStatusResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    order_id: UUID
    order_status: OrderLifecycleStatus
    payment_status: PaymentStatus | None
    tracking: TrackingDetails | None
    estimated_delivery_date: date | None
    eta_days: int | None
    status_history: list[OrderStatusHistoryEntry]
