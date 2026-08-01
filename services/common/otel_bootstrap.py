"""
Description: Shared OpenTelemetry wiring for the Acme services, exporting OTLP to the local BDOT agent.
Created by: Mustafa Can Caliskan
Date: 2026-08-01
"""

import logging
import os

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.metrics.view import View
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from acme_semconv import ACME_SERVICE_TIER, SCHEMA_URL, AcmeServiceTier

_DEFAULT_ENDPOINT = "http://localhost:4317"
_METRIC_EXPORT_INTERVAL_MS = 5_000


def setup_telemetry(
    service_name: str,
    service_tier: AcmeServiceTier,
    views: tuple[View, ...] = (),
) -> tuple[trace.Tracer, metrics.Meter, logging.Logger]:
    """Install global tracer, meter and logger providers that export OTLP to the sidecar agent.

    The resource carries the Acme schema URL, so every signal this process emits
    is self-describing: a consumer can look up exactly which version of the
    registry the telemetry was written against.

    Args:
        service_name: Value for the `service.name` resource attribute.
        service_tier: Value for the `acme.service.tier` resource attribute, as
            declared by the `acme.service` entity in the registry.
        views: Metric views to install, typically to give a histogram bucket
            boundaries that match the unit the registry declares.

    Returns:
        A tuple of the tracer, meter and stdlib logger this service should use.
        The logger both prints to stdout and ships log records over OTLP.

    Note:
        Reads `OTEL_EXPORTER_OTLP_ENDPOINT`; defaults to the local agent on
        `http://localhost:4317`. Called once at import time by each service —
        calling it twice would install a second set of providers and silently
        drop the first one's buffered signals.
    """
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", _DEFAULT_ENDPOINT)
    resource = Resource.create(
        attributes={
            "service.name": service_name,
            ACME_SERVICE_TIER: service_tier.value,
        },
        schema_url=SCHEMA_URL,
    )

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
    )
    trace.set_tracer_provider(tracer_provider)

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[
            PeriodicExportingMetricReader(
                OTLPMetricExporter(endpoint=endpoint, insecure=True),
                export_interval_millis=_METRIC_EXPORT_INTERVAL_MS,
            )
        ],
        views=list(views),
    )
    metrics.set_meter_provider(meter_provider)

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=endpoint, insecure=True))
    )

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger = logging.getLogger(service_name)
    logger.addHandler(LoggingHandler(level=logging.INFO, logger_provider=logger_provider))

    return (
        trace.get_tracer(service_name),
        metrics.get_meter(service_name),
        logger,
    )
