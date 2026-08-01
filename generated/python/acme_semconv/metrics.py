"""
Description: Metric definitions generated from the Acme telemetry registry.
Created by: OpenTelemetry Weaver
Date: generated

DO NOT EDIT. Regenerate with `make generate`. Source of truth: semconv/model/.
Schema URL: https://acme.example/schemas/0.2.0
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricDef:
    """A metric as declared in the registry.

    Attributes:
        name: Instrument name to register with the OpenTelemetry meter.
        instrument: Instrument kind (`counter`, `histogram`, `updowncounter`, `gauge`).
        unit: UCUM unit string.
        brief: Human description, reused as the instrument description.
        attribute_keys: Attribute keys this metric is dimensioned by.
    """

    name: str
    instrument: str
    unit: str
    brief: str
    attribute_keys: tuple[str, ...]



ACME_LOG_COUNT = MetricDef(
    name="acme.log.count",
    instrument="gauge",
    unit="{logs}",
    brief="Log records observed by the gateway collector during one interval.",
    attribute_keys=("acme.log.service_name", "acme.log.severity", ),
)
"""Log records observed by the gateway collector during one interval."""


ACME_ORDERS_SUBMITTED = MetricDef(
    name="acme.orders.submitted",
    instrument="counter",
    unit="{order}",
    brief="Number of orders accepted by the checkout service.",
    attribute_keys=("acme.customer.tier", ),
)
"""Number of orders accepted by the checkout service."""


ACME_PAYMENT_DURATION = MetricDef(
    name="acme.payment.duration",
    instrument="histogram",
    unit="s",
    brief="End-to-end duration of a payment authorization attempt.",
    attribute_keys=("acme.payment.decline_reason", "acme.payment.method", ),
)
"""End-to-end duration of a payment authorization attempt."""
