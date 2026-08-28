"""AI-commerce merchant discovery routes."""

from fastapi import APIRouter

router = APIRouter(prefix="/.well-known", tags=["Discovery"])
