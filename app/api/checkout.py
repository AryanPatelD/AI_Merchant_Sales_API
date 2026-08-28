"""Checkout and order-creation routes."""

from fastapi import APIRouter

router = APIRouter(prefix="/checkout", tags=["Checkout"])
