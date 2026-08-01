"""
Description: Core service that authorizes payments and, on demand, emits deliberately non-conformant telemetry.
Created by: Mustafa Can Caliskan
Date: 2026-08-01
"""

import os
import random
import time

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics.view import ExplicitBucketHistogramAggregation, View
from opentelemetry.trace import SpanKind
from pydantic import BaseModel

from acme_semconv import (
    ACME_ORDER_ID,
    ACME_PAYMENT_DECLINE_REASON,
    ACME_PAYMENT_DURATION,
    ACME_PAYMENT_METHOD,
    EVENT_ACME_PAYMENT_DECLINED,
    SPAN_ACME_PAYMENT_AUTHORIZE,
    AcmePaymentDeclineReason,
    AcmePaymentMethod,
    AcmeServiceTier,
)
from common.instruments import create_histogram
from common.otel_bootstrap import setup_telemetry

SERVICE_NAME = "acme-payment"

# When enabled, the service emits two things the registry does not allow: an
# undeclared attribute carrying a fake card number, and a customer tier outside
# the declared enum. The mask processor scrubs the first; `weaver registry
# live-check` reports both.
EMIT_VIOLATIONS = os.getenv("EMIT_VIOLATIONS", "false").lower() == "true"
UNDECLARED_CARD_ATTRIBUTE = "acme.payment.card_number"
UNDECLARED_TIER_ATTRIBUTE = "acme.customer.tier"
INVALID_TIER_VALUE = "gold"
FAKE_CARD_NUMBER = "4111 1111 1111 1111"

_DECLINE_PROBABILITY = 0.2
_MIN_LATENCY_SECONDS = 0.01
_MAX_LATENCY_SECONDS = 0.12

# The registry declares acme.payment.duration in seconds, but the SDK's default
# histogram buckets are sized for milliseconds and would collapse every real
# measurement into the first bucket. Bucket boundaries follow the declared unit.
_DURATION_BUCKETS_SECONDS = (0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)

tracer, meter, logger = setup_telemetry(
    SERVICE_NAME,
    AcmeServiceTier.CORE,
    views=(
        View(
            instrument_name=ACME_PAYMENT_DURATION.name,
            aggregation=ExplicitBucketHistogramAggregation(
                boundaries=_DURATION_BUCKETS_SECONDS
            ),
        ),
    ),
)
payment_duration = create_histogram(meter, ACME_PAYMENT_DURATION)

app = FastAPI(title=SERVICE_NAME)
FastAPIInstrumentor.instrument_app(app)


class AuthorizationRequest(BaseModel):
    """A request to authorize payment for one order.

    Attributes:
        order_id: Identifier of the order being paid for.
        customer_tier: Commercial tier of the paying customer, used only for logging.
    """

    order_id: str
    customer_tier: str = "free"


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness probe used by the Compose health check."""
    return {"status": "ok"}


@app.post("/authorizations")
async def authorize(payload: AuthorizationRequest) -> dict:
    """Authorize a payment, declining roughly one in five attempts.

    Emits the `acme.payment.authorize` span, records `acme.payment.duration`,
    and on a decline adds the `acme.payment.declined` event plus a warning log.

    Args:
        payload: The authorization request.

    Returns:
        A dict with `authorized`, the payment `method`, and `decline_reason`
        when the attempt was declined.
    """
    method = random.choice(list(AcmePaymentMethod))
    declined = random.random() < _DECLINE_PROBABILITY
    reason = random.choice(list(AcmePaymentDeclineReason)) if declined else None

    with tracer.start_as_current_span(
        SPAN_ACME_PAYMENT_AUTHORIZE, kind=SpanKind.CLIENT
    ) as span:
        started = time.perf_counter()
        time.sleep(random.uniform(_MIN_LATENCY_SECONDS, _MAX_LATENCY_SECONDS))
        elapsed_seconds = time.perf_counter() - started

        span.set_attribute(ACME_ORDER_ID, payload.order_id)
        span.set_attribute(ACME_PAYMENT_METHOD, method.value)

        attributes = {ACME_PAYMENT_METHOD: method.value}
        if reason is not None:
            span.set_attribute(ACME_PAYMENT_DECLINE_REASON, reason.value)
            attributes[ACME_PAYMENT_DECLINE_REASON] = reason.value
            span.add_event(
                EVENT_ACME_PAYMENT_DECLINED,
                {
                    ACME_ORDER_ID: payload.order_id,
                    ACME_PAYMENT_DECLINE_REASON: reason.value,
                    ACME_PAYMENT_METHOD: method.value,
                },
            )

        if EMIT_VIOLATIONS:
            span.set_attribute(UNDECLARED_CARD_ATTRIBUTE, FAKE_CARD_NUMBER)
            span.set_attribute(UNDECLARED_TIER_ATTRIBUTE, INVALID_TIER_VALUE)
            # Leaked into the log body on purpose: the agent's mask processor
            # rewrites it to [masked_credit_card] before it reaches Loki.
            logger.info(
                "charging card %s for order %s", FAKE_CARD_NUMBER, payload.order_id
            )

        payment_duration.record(elapsed_seconds, attributes)

        if reason is not None:
            logger.warning(
                "payment for order %s declined via %s: %s",
                payload.order_id,
                method.value,
                reason.value,
            )

        return {
            "authorized": not declined,
            "method": method.value,
            "decline_reason": reason.value if reason else None,
        }
