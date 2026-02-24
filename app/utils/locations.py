"""Postcode-to-location lookup with TTL caching and retry logic."""

import logging

import httpx
from cachetools import TTLCache
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from config import get_settings

logger = logging.getLogger(__name__)

location_cache: TTLCache = TTLCache(maxsize=1000, ttl=3600)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=10),
    retry=retry_if_exception_type((httpx.RequestError,)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def _fetch_location(postcode: str) -> str | None:
    """Call the zip2location API to resolve a postcode to a location name."""
    settings = get_settings()
    with httpx.Client(timeout=10) as client:
        res = client.get(f"{settings.ZIP2LOCATION_URL}?postcode={postcode}")

    if res.status_code != 200:
        logger.debug("postcode %s not recognized", postcode)
        return None

    data = res.json()
    return data.get("title")


def get_location(postcode) -> str | None:
    """Given a postcode, return the location name. Uses TTL cache."""
    if postcode is None:
        return None

    if not isinstance(postcode, str):
        postcode = str(postcode)

    if postcode in location_cache:
        return location_cache[postcode]

    try:
        title = _fetch_location(postcode)
    except Exception as e:
        logger.error("Failed to fetch location for postcode %s: %s", postcode, e)
        return None

    if title is not None:
        location_cache[postcode] = title

    return title
