# app/commands/completed/booking.py

import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class Booking:
    def __init__(self):
        settings = get_settings()
        self.proxy_url = settings.PROXY_URL
        self.headers = {
            "Authorization": f"Bearer {settings.PROXY_API_KEY}",
            "Content-Type": "application/json",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    )
    async def get_all_in_tz(self, today_date_string, tz_name):
        url = f"{self.proxy_url}/v1/staff/bookings/tocomplete/{today_date_string}"
        params = {"tz_name": tz_name}
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, headers=self.headers, params=params)
            r.raise_for_status()
        return r.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    )
    async def complete(self, booking_id):
        settings = get_settings()
        if settings.testing:
            return 0
        url = f"{self.proxy_url}/v1/staff/bookings/{booking_id}/complete"
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, headers=self.headers)
            r.raise_for_status()
        return r.json().get("res", 0)
