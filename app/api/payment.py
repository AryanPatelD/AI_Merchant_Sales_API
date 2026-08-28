"""Razorpay payment and webhook routes."""

from fastapi import APIRouter

router = APIRouter(prefix="/payment", tags=["Payments"])
