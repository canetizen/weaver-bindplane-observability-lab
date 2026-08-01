"""
Description: Continuously places synthetic orders against the gateway so the pipeline always has traffic.
Created by: Mustafa Can Caliskan
Date: 2026-08-01
"""

import logging
import os
import random
import time

import httpx

from acme_semconv import AcmeCustomerTier

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://gateway:8000")
INTERVAL_SECONDS = float(os.getenv("LOADGEN_INTERVAL_SECONDS", "2"))

_REQUEST_TIMEOUT_SECONDS = 15.0
_MIN_ITEMS = 1
_MAX_ITEMS = 6
_STARTUP_GRACE_SECONDS = 10.0

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("acme-loadgen")


def place_order(client: httpx.Client) -> None:
    """Place one random order and log the outcome.

    Args:
        client: Reused HTTP client pointed at the gateway.

    Note:
        Never raises: connection errors during startup or restarts are logged
        and swallowed so the generator keeps running for the life of the stack.
    """
    payload = {
        "item_count": random.randint(_MIN_ITEMS, _MAX_ITEMS),
        "customer_tier": random.choice(list(AcmeCustomerTier)).value,
    }
    try:
        response = client.post(f"{GATEWAY_URL}/checkout", json=payload)
        response.raise_for_status()
        logger.info("placed order: %s", response.json())
    except httpx.HTTPError as error:
        logger.warning("order failed: %s", error)


def main() -> None:
    """Place an order every `LOADGEN_INTERVAL_SECONDS` until the container stops."""
    time.sleep(_STARTUP_GRACE_SECONDS)
    with httpx.Client(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
        while True:
            place_order(client)
            time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
