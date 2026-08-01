"""
Description: Core service that records an order and asks the payment service to authorize it.
Created by: Mustafa Can Caliskan
Date: 2026-08-01
"""

import os
import uuid

import httpx
from fastapi import FastAPI, Request
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.trace import SpanKind
from pydantic import BaseModel

from acme_semconv import (
    ACME_CUSTOMER_TIER,
    ACME_ORDER_ID,
    ACME_ORDER_ITEM_COUNT,
    ACME_ORDERS_SUBMITTED,
    HTTP_REQUEST_METHOD,
    SERVER_ADDRESS,
    SPAN_ACME_CHECKOUT_SUBMIT_ORDER,
    AcmeCustomerTier,
    AcmeServiceTier,
)
from common.instruments import create_counter
from common.otel_bootstrap import setup_telemetry

SERVICE_NAME = "acme-checkout"
PAYMENT_URL = os.getenv("PAYMENT_URL", "http://payment:8002")
_UPSTREAM_TIMEOUT_SECONDS = 10.0
_ORDER_ID_LENGTH = 6

tracer, meter, logger = setup_telemetry(SERVICE_NAME, AcmeServiceTier.CORE)
HTTPXClientInstrumentor().instrument()

orders_submitted = create_counter(meter, ACME_ORDERS_SUBMITTED)

app = FastAPI(title=SERVICE_NAME)
FastAPIInstrumentor.instrument_app(app)


class OrderRequest(BaseModel):
    """An order handed over by the gateway.

    Attributes:
        item_count: Number of distinct line items.
        customer_tier: Commercial tier of the customer.
    """

    item_count: int = 1
    customer_tier: AcmeCustomerTier = AcmeCustomerTier.FREE


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness probe used by the Compose health check."""
    return {"status": "ok"}


@app.post("/orders")
async def submit_order(order: OrderRequest, request: Request) -> dict:
    """Accept an order, authorize payment for it, and report the outcome.

    Emits the `acme.checkout.submit_order` span and increments
    `acme.orders.submitted`. Both names, and every attribute key set here, come
    from the generated `acme_semconv` package rather than from string literals.

    Args:
        order: The order to process.
        request: The inbound request, used to fill the HTTP attributes the
            registry marks as required on this span.

    Returns:
        A dict with the generated order id, the authorization verdict and, when
        declined, the reason reported by the payment service.
    """
    order_id = f"ord-{uuid.uuid4().hex[:_ORDER_ID_LENGTH]}"

    with tracer.start_as_current_span(
        SPAN_ACME_CHECKOUT_SUBMIT_ORDER, kind=SpanKind.SERVER
    ) as span:
        span.set_attribute(ACME_ORDER_ID, order_id)
        span.set_attribute(ACME_CUSTOMER_TIER, order.customer_tier.value)
        span.set_attribute(ACME_ORDER_ITEM_COUNT, order.item_count)
        span.set_attribute(HTTP_REQUEST_METHOD, request.method)
        span.set_attribute(SERVER_ADDRESS, request.url.hostname or "")

        orders_submitted.add(1, {ACME_CUSTOMER_TIER: order.customer_tier.value})

        async with httpx.AsyncClient(timeout=_UPSTREAM_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{PAYMENT_URL}/authorizations",
                json={"order_id": order_id, "customer_tier": order.customer_tier.value},
            )
            response.raise_for_status()
            authorization = response.json()

        logger.info(
            "order %s for a %s customer was %s",
            order_id,
            order.customer_tier.value,
            "authorized" if authorization["authorized"] else "declined",
        )

        return {"order_id": order_id, **authorization}
