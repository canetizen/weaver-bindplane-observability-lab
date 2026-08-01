"""
Description: Span, event and entity names generated from the Acme telemetry registry.
Created by: OpenTelemetry Weaver
Date: generated

DO NOT EDIT. Regenerate with `make generate`. Source of truth: semconv/model/.
Schema URL: https://acme.example/schemas/0.2.0
"""


SPAN_ACME_CHECKOUT_SUBMIT_ORDER = "acme.checkout.submit_order"
"""Handling of a customer order submission by the checkout service, from request acceptance until the payment result is known.

Span kind: server. Required attributes:
- acme.customer.tier
- acme.order.id
- http.request.method
"""

SPAN_ACME_PAYMENT_AUTHORIZE = "acme.payment.authorize"
"""A single authorization attempt against the payment provider. One checkout may produce at most one authorization span.

Span kind: client. Required attributes:
- acme.order.id
- acme.payment.method
"""

EVENT_ACME_PAYMENT_DECLINED = "acme.payment.declined"
"""Emitted once per declined authorization attempt."""

ENTITY_ACME_SERVICE = "acme.service"
"""An Acme Shop service instance."""
