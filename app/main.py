"""FastAPI application entry point."""

from fastapi import FastAPI

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

API_V1_PREFIX = "/api/v1"

app = FastAPI(
    title="AI Merchant Sales API",
    version="1.0.0",
    description="Machine-readable commerce APIs for autonomous AI buyers.",
)

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
app.include_router(order.router, prefix=API_V1_PREFIX)
