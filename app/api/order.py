"""Order status and fulfillment routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.schemas.order import OrderStatusResponse
from app.services.order import OrderNotFoundError, get_order_status

router = APIRouter(prefix="/order-status", tags=["Orders"])


@router.get("", response_model=OrderStatusResponse, summary="Get normalized order progress")
def order_status(
    order_id: UUID,
    settings: Settings = Depends(get_settings),
) -> OrderStatusResponse:
    try:
        return get_order_status(settings, order_id)
    except OrderNotFoundError as error:
        raise HTTPException(404, "Merchant order was not found") from error
