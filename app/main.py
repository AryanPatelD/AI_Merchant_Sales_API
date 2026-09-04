"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    availability,
    catalog,
    checkout,
    discovery,
    order,
    payment,
    quote,
    search,
)
from app.config import get_settings
from app.middleware.security import security_middleware

API_V1_PREFIX = "/api/v1"
settings = get_settings()

app = FastAPI(
    title="AI Merchant Sales API",
    version="1.0.0",
    description="Machine-readable commerce APIs for autonomous AI buyers.",
)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def commerce_infrastructure(request, call_next):
    return await security_middleware(request, call_next, get_settings())

@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }
# The discovery manifest uses the standard well-known URL outside /api/v1.
app.include_router(discovery.router)

app.include_router(catalog.router, prefix=API_V1_PREFIX)
app.include_router(search.router, prefix=API_V1_PREFIX)
app.include_router(availability.router, prefix=API_V1_PREFIX)
app.include_router(quote.router, prefix=API_V1_PREFIX)
app.include_router(checkout.router, prefix=API_V1_PREFIX)
app.include_router(payment.router, prefix=API_V1_PREFIX)
app.include_router(payment.webhook_router)
app.include_router(order.router, prefix=API_V1_PREFIX)
