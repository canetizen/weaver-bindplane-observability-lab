"""
Description: Attribute keys and enum values generated from the Acme telemetry registry.
Created by: OpenTelemetry Weaver
Date: generated

DO NOT EDIT. Regenerate with `make generate`. Source of truth: semconv/model/.
Schema URL: https://acme.example/schemas/0.2.0
"""

from enum import Enum

SCHEMA_URL = "https://acme.example/schemas/0.2.0"
"""URL identifying the version of the Acme telemetry schema these symbols came from."""

# --- registry.acme.order: Attributes describing an order flowing through the Acme Shop. ---

ACME_CUSTOMER_TIER = "acme.customer.tier"
"""Commercial tier of the customer that placed the order."""

ACME_ORDER_ID = "acme.order.id"
"""Opaque identifier of the order, unique for the lifetime of the shop."""

ACME_ORDER_ITEM_COUNT = "acme.order.item_count"
"""Number of distinct line items in the order."""

# --- registry.acme.payment: Attributes describing a payment authorization attempt. ---

ACME_PAYMENT_DECLINE_REASON = "acme.payment.decline_reason"
"""Why the payment authorization was declined."""

ACME_PAYMENT_METHOD = "acme.payment.method"
"""Instrument used to authorize the payment."""

# --- registry.acme.pipeline: Attributes added by the collector pipeline rather than by application code. They are declared here because telemetry that the pipeline enriches is still telemetry the schema is responsible for. ---

ACME_AGENT_NAME = "acme.agent.name"
"""Name of the sidecar collector that first received the signal."""

ACME_LOG_SERVICE_NAME = "acme.log.service_name"
"""Service whose log records a log-derived metric counted."""

ACME_LOG_SEVERITY = "acme.log.severity"
"""Severity text of the log records counted by a log-derived metric."""

ACME_PIPELINE_TIER = "acme.pipeline.tier"
"""Collector tier that last processed the signal."""

# --- registry.acme.service: Attributes describing an Acme service instance. ---

ACME_SERVICE_TIER = "acme.service.tier"
"""Position of the service in the Acme deployment topology."""

# --- Attributes imported from the OpenTelemetry semantic conventions ---

HTTP_REQUEST_METHOD = "http.request.method"
"""HTTP request method."""

SERVER_ADDRESS = "server.address"
"""Server domain name if available without reverse DNS lookup; otherwise, IP address or Unix domain socket name."""

SERVICE_NAME = "service.name"
"""Logical name of the service."""



class AcmeCustomerTier(str, Enum):
    """Allowed values for the `acme.customer.tier` attribute.

    Emitting a value outside this enum is a schema violation and is reported by
    `weaver registry live-check`.
    """

    FREE = "free"
    """Customer on the free plan."""

    PLUS = "plus"
    """Customer on the paid self-serve plan."""

    ENTERPRISE = "enterprise"
    """Customer on a negotiated enterprise contract."""



class AcmePaymentDeclineReason(str, Enum):
    """Allowed values for the `acme.payment.decline_reason` attribute.

    Emitting a value outside this enum is a schema violation and is reported by
    `weaver registry live-check`.
    """

    INSUFFICIENT_FUNDS = "insufficient_funds"
    """The instrument did not have enough available balance."""

    FRAUD_SUSPECTED = "fraud_suspected"
    """The risk engine rejected the attempt."""

    EXPIRED_CARD = "expired_card"
    """The card is past its expiry date."""



class AcmePaymentMethod(str, Enum):
    """Allowed values for the `acme.payment.method` attribute.

    Emitting a value outside this enum is a schema violation and is reported by
    `weaver registry live-check`.
    """

    CARD = "card"
    """Credit or debit card."""

    WIRE = "wire"
    """Bank wire transfer."""

    WALLET = "wallet"
    """Third-party digital wallet."""



class AcmePipelineTier(str, Enum):
    """Allowed values for the `acme.pipeline.tier` attribute.

    Emitting a value outside this enum is a schema violation and is reported by
    `weaver registry live-check`.
    """

    AGENT = "agent"
    """Sidecar collector running next to a service."""

    GATEWAY = "gateway"
    """Central collector that aggregates every agent."""



class AcmeServiceTier(str, Enum):
    """Allowed values for the `acme.service.tier` attribute.

    Emitting a value outside this enum is a schema violation and is reported by
    `weaver registry live-check`.
    """

    EDGE = "edge"
    """Public-facing service."""

    CORE = "core"
    """Internal business-logic service."""

