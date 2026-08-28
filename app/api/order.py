"""Order status and fulfillment routes."""

from fastapi import APIRouter

router = APIRouter(prefix="/order-status", tags=["Orders"])
