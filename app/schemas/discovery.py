"""Schemas for the AI-commerce discovery manifest."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MerchantDiscoveryManifest(BaseModel):
    """Machine-readable description of active merchant capabilities."""

    model_config = ConfigDict(frozen=True)

    merchant_id: UUID
    merchant: str
    api_version: str
    currency: str
    country: str
    capabilities: list[str]
    payment_gateways: list[str]
    api_base_url: str


class ErrorResponse(BaseModel):
    detail: str

