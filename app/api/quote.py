"""Quote and pricing routes."""

from fastapi import APIRouter

router = APIRouter(prefix="/quote", tags=["Quotes"])
