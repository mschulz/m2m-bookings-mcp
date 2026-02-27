"""Klaviyo CRM integration for notifying new house and bond customers."""

import logging
import re
from enum import StrEnum

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
            "quote": _clean_price(data.get("final_price")),
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def post_home_data(self, data):
        """Send a new house-clean customer to Klaviyo."""
        url = f"{self.url}/house/new"
        payload = self._get_payload(data)
        logger.debug("Klaviyo house POST: url=%s payload=%s", url, payload)

        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(url, headers=self.headers, json=payload)

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
    async def post_bond_data(self, data):
        """Send a new bond-clean customer to Klaviyo."""
        payload = self._get_payload(data)

        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(
                f"{self.url}/bond/new", headers=self.headers, json=payload,
            )

        if res.status_code != 201:
            logger.error(
                "Failed (%d) to update bond customer list for %s: %s | payload=%s",
                res.status_code, payload.get("email"), res.text, payload,
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def create_klaviyo_profile(self, data):
        """Create a new Klaviyo profile."""
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(
                f"{self.url}/profile/new",
                headers=self.headers,
                json=data,
            )

        if res.status_code != 201:
            logger.error(
                "Klaviyo profile creation failed (%d) for %s: %s",
                res.status_code, data.get("email"), res.text,
            )

        return res.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def check_profile(self, email):
        """Check if an email exists as a Klaviyo profile."""
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(
                f"{self.url}/profile/check",
                headers=self.headers,
                params={"email": email},
            )

        if res.status_code != 200:
            logger.error(
                "Klaviyo profile check failed (%d) for %s: %s",
                res.status_code, email, res.text,
            )
            return {"exists": False, "profile_id": None}

        return res.json()


def _normalize_phone(phone):
    """Normalize an Australian phone number to E.164 format (+61...)."""
    if not phone:
        return phone
    digits = re.sub(r"\D", "", phone)
    # 0061… international dial prefix (strip leading 00)
    if digits.startswith("0061") and len(digits) == 13:
        return f"+{digits[2:]}"
    # 61… already international (just missing +)
    if digits.startswith("61") and len(digits) == 11:
        return f"+{digits}"
    # 0X… standard Australian local format
    if digits.startswith("0") and len(digits) == 10:
        return f"+61{digits[1:]}"
    # 9 digits — area code without leading 0 (e.g. 3 5272 2221)
    if len(digits) == 9 and digits[0] in "2345789":
        return f"+61{digits}"
    return phone


def _clean_price(value):
    """Convert a price string to a float (e.g. '$143.02' → 143.02)."""
    if not value:
        return value
    try:
        return float(str(value).replace("$", "").strip())
    except ValueError:
        return value


class WebhookRoute(StrEnum):
    BOOKING_NEW = "booking_new"
    BOOKING_UPDATED = "booking_updated"
    BOOKING_RESTORED = "booking_restored"
    BOOKING_COMPLETED = "booking_completed"
    BOOKING_CANCELLATION = "booking_cancellation"
    BOOKING_TEAM_CHANGED = "booking_team_changed"
    CUSTOMER_NEW = "customer_new"
    CUSTOMER_UPDATED = "customer_updated"


async def notify_klaviyo(service_category, data):
    """Dispatch a new-customer notification to the appropriate Klaviyo list."""
    try:
        k = Klaviyo()
        if service_category == "House Clean":
            await k.post_home_data(data)
        else:
            await k.post_bond_data(data)
    except Exception as e:
        logger.error("Klaviyo notification failed for %s: %s", data.get("email"), e)


async def process_with_klaviyo(data, route: WebhookRoute):
    """Central Klaviyo hook called by all POST routes via BackgroundTasks.

    Only booking_new and booking_updated routes trigger notifications,
    and only when the booking is from a new customer in a qualifying category.
    """
    if not isinstance(data, dict):
        return
    if not get_settings().KLAVIYO_ENABLED:
        return
    if route in (
            WebhookRoute.BOOKING_NEW,
            WebhookRoute.BOOKING_UPDATED,
            WebhookRoute.BOOKING_RESTORED,
            WebhookRoute.BOOKING_COMPLETED,
            WebhookRoute.BOOKING_CANCELLATION
        ):
        """
        BOOKING_NEW may conain a new customer.  The other routes
        should refer to existing customer.  HOWEVER, when building
        the database we may have missed the inital creation of the
        customer in the database or in the profile, so we fix
        that here"""
        service_category = data.get("service_category")
        if service_category in ("Bond Clean", "House Clean"):
            logger.debug(
                "New customer: send %s to Klaviyo with %s",
                data.get("email"), service_category,
            )
            await notify_klaviyo(service_category, data)
    elif route == WebhookRoute.CUSTOMER_NEW:
        email = data.get("email")
        if email:
            res = await check_klaviyo_profile(email)
            if res.get("exists"):
                return
            # Create the profile then
            k = Klaviyo()
            await k.create_klaviyo_profile(data)


async def check_klaviyo_profile(email):
    """Check if an email exists as a Klaviyo profile.

    Returns {"exists": bool, "profile_id": str | None}.
    """
    settings = get_settings()
    if not settings.KLAVIYO_ENABLED:
        return {"exists": False, "profile_id": None}

    try:
        return await Klaviyo().check_profile(email)
    except Exception as e:
        logger.error("Klaviyo profile check failed for %s: %s", email, e)
        return {"exists": False, "profile_id": None}
