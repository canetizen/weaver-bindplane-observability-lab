"""
Description: Turns registry-generated MetricDef records into live OpenTelemetry instruments.
Created by: Mustafa Can Caliskan
Date: 2026-08-01
"""

from opentelemetry.metrics import Counter, Histogram, Meter

from acme_semconv import MetricDef

_COUNTER = "counter"
_HISTOGRAM = "histogram"


def create_counter(meter: Meter, definition: MetricDef) -> Counter:
    """Create a counter whose name, unit and description come from the registry.

    Args:
        meter: Meter to register the instrument on.
        definition: Generated metric definition; must declare `instrument: counter`.

    Returns:
        The registered counter.

    Raises:
        ValueError: If the registry declares a different instrument kind, which
            means the code and the schema have drifted apart.
    """
    if definition.instrument != _COUNTER:
        raise ValueError(
            f"{definition.name} is declared as '{definition.instrument}' in the registry, not a counter"
        )
    return meter.create_counter(
        name=definition.name, unit=definition.unit, description=definition.brief
    )


def create_histogram(meter: Meter, definition: MetricDef) -> Histogram:
    """Create a histogram whose name, unit and description come from the registry.

    Args:
        meter: Meter to register the instrument on.
        definition: Generated metric definition; must declare `instrument: histogram`.

    Returns:
        The registered histogram.

    Raises:
        ValueError: If the registry declares a different instrument kind.
    """
    if definition.instrument != _HISTOGRAM:
        raise ValueError(
            f"{definition.name} is declared as '{definition.instrument}' in the registry, not a histogram"
        )
    return meter.create_histogram(
        name=definition.name, unit=definition.unit, description=definition.brief
    )
