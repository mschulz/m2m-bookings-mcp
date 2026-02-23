# app/database/update_durations.py

import logging
from datetime import date

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.database import SessionLocal
from app.daos.booking import booking_dao
from config import get_settings

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=10),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
)
def get_booking_from_proxy(booking_id: int) -> dict:
    """Fetch booking details from the proxy API."""
    settings = get_settings()
    url = f"{settings.PROXY_URL}/v1/staff/bookings/{booking_id}"
    headers = {
        "Authorization": f"Bearer {settings.PROXY_API_KEY}",
        "Accept": "application/json",
    }
    with httpx.Client(timeout=30) as client:
        r = client.get(url, headers=headers)
        r.raise_for_status()
    return r.json()


def get_duration_from_id(booking_id: int) -> int | None:
    res = get_booking_from_proxy(booking_id)
    return res.get("duration")


def map_duration_to_str(minutes: int) -> str:
    hrs, mins = divmod(minutes, 60)
    return f"{hrs} hrs {mins} mins"


def main():
    db = SessionLocal()
    try:
        start_date = date(2026, 1, 28)
        res = booking_dao.get_all_bookings_after_service_date(db, start_date)
        number_durations = len(res)

        print(f"Bookings with durations to update = {number_durations}")

        if res:
            for idx, item in enumerate(res):
                booking_id = item.booking_id
                duration = item.duration

                if duration is None:
                    try:
                        new_duration = get_duration_from_id(booking_id)
                        if new_duration is not None:
                            new_duration_str = map_duration_to_str(new_duration)
                            item.duration = new_duration_str
                    except Exception as e:
                        logger.error(
                            "Failed to get duration for booking %s: %s",
                            booking_id, e,
                        )
                print(idx)
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
