"""Schemas for inventory availability responses."""

from pydantic import BaseModel, ConfigDict, Field


class ProductAvailability(BaseModel):
    """Read-only availability view for an active product SKU."""

    model_config = ConfigDict(frozen=True)

    sku: str
    in_stock: bool
    available_quantity: int = Field(ge=0)
    eta_days: int = Field(ge=0)
    requested_quantity: int | None = Field(default=None, ge=1)
    requested_quantity_available: bool | None = None

