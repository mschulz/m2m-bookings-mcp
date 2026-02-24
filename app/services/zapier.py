"""Zapier webhook integration for outbound event notifications."""

import json
import logging

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from config import get_settings

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=10),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def post_to_zapier(url, data):
    """POST JSON data to a Zapier webhook URL with retry."""
    headers = {"content-type": "application/json"}
    with httpx.Client(timeout=10) as client:
        r = client.post(url, headers=headers, content=data)
        r.raise_for_status()
    logger.info("Posted to Zapier: %s", data)
    return r


def post_new_bond_agent_calls(d):
    """Send new bond agent call data to the configured Zapier webhook."""
    settings = get_settings()
    url = settings.NEW_BOND_AGENT_CALLS
    if not url:
        logger.warning("NEW_BOND_AGENT_CALLS URL not configured")
        return None
    data = json.dumps({"result": d}, indent=2)
    return post_to_zapier(url, data)
