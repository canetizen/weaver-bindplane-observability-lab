"""
Description: Public edge service that accepts customer orders and forwards them to checkout.
Created by: Mustafa Can Caliskan
Date: 2026-08-01
"""

import os

import httpx
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from pydantic import BaseModel

from acme_semconv import AcmeCustomerTier, AcmeServiceTier
from common.otel_bootstrap import setup_telemetry

SERVICE_NAME = "acme-gateway"
CHECKOUT_URL = os.getenv("CHECKOUT_URL", "http://checkout:8001")
_UPSTREAM_TIMEOUT_SECONDS = 10.0

tracer, meter, logger = setup_telemetry(SERVICE_NAME, AcmeServiceTier.EDGE)
HTTPXClientInstrumentor().instrument()

app = FastAPI(title=SERVICE_NAME)
FastAPIInstrumentor.instrument_app(app)


class OrderRequest(BaseModel):
    """An incoming order from a customer.

    Attributes:
        item_count: Number of distinct line items.
        customer_tier: Commercial tier of the customer, as declared by the registry.
    """

    item_count: int = 1
    customer_tier: AcmeCustomerTier = AcmeCustomerTier.FREE


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness probe used by the Compose health check."""
    return {"status": "ok"}


@app.post("/checkout")
async def checkout(order: OrderRequest) -> dict:
    """Forward an order to the checkout service and relay its verdict.

    The gateway adds no Acme attributes of its own; its span is the one produced
    by the FastAPI instrumentation, which is why the trace still starts here.

    Args:
        order: The customer's order.

    Returns:
        The checkout service's response body verbatim.
    """
    async with httpx.AsyncClient(timeout=_UPSTREAM_TIMEOUT_SECONDS) as client:
        response = await client.post(f"{CHECKOUT_URL}/orders", json=order.model_dump())
        response.raise_for_status()
        return response.json()
