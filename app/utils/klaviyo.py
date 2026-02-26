"""Klaviyo CRM integration for notifying new house and bond customers."""

import logging
import re

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class Klaviyo:
    """HTTP client for the Klaviyo customer notification API."""

    def __init__(self):
        settings = get_settings()
        self.url = settings.MY_KLAVIYO_URL
        self.headers = {
            "Authorization": f"Bearer {settings.MY_KLAVIYO_API_KEY}",
            "Content-Type": "application/json",
        }

    def _get_payload(self, data):
        """Build the Klaviyo API payload from booking data."""
        return {
            "email": data.get("email"),
            "first_name": data.get("first_name"),
            "phone": _normalize_phone(data.get("phone")),
            "postcode": data.get("postcode", data.get("zip", "")),
            "quote": data.get("final_price"),
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def post_home_data(self, data):
        """Send a new house-clean customer to Klaviyo."""
        url = f"{self.url}/house/new"
        payload = self._get_payload(data)
        logger.debug("Klaviyo house POST: url=%s payload=%s", url, payload)

        with httpx.Client(timeout=10) as client:
            res = client.post(url, headers=self.headers, json=payload)

        if res.status_code != 201:
            logger.error(
                "Failed (%d) to update house customer list for %s: %s | payload=%s",
                res.status_code, payload.get("email"), res.text, payload,
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def post_bond_data(self, data):
        """Send a new bond-clean customer to Klaviyo."""
        payload = self._get_payload(data)

        with httpx.Client(timeout=10) as client:
            res = client.post(
                f"{self.url}/bond/new", headers=self.headers, json=payload,
            )

        if res.status_code != 201:
            logger.error(
                "Failed (%d) to update bond customer list for %s: %s | payload=%s",
                res.status_code, payload.get("email"), res.text, payload,
            )


def _normalize_phone(phone):
    """Normalize an Australian phone number to E.164 format (+61...)."""
    if not phone:
        return phone
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("61") and len(digits) == 11:
        return f"+{digits}"
    if digits.startswith("0") and len(digits) == 10:
        return f"+61{digits[1:]}"
    return phone


def notify_klaviyo(service_category, data):
    """Dispatch a new-customer notification to the appropriate Klaviyo list."""
    try:
        k = Klaviyo()
        if service_category == "House Clean":
            k.post_home_data(data)
        else:
            k.post_bond_data(data)
    except Exception as e:
        logger.error("Klaviyo notification failed for %s: %s", data.get("email"), e)
