# app/database/update_status.py

"""
Three steps to the process:

    1: Get COMPLETED bookings from proxy, update database
    2: Get CANCELLED bookings from proxy, update database
    3: Mark remaining as NOT_COMPLETE
"""

import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.database import SessionLocal
from app.models.booking import Booking
from config import get_settings

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=10),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
)
def get_bookings_from_proxy(limit: int, offset: int, options: str = "completed") -> list:
    """Fetch bookings from the proxy API."""
    settings = get_settings()
    url = f"{settings.PROXY_URL}/v1/staff/bookings/"
    headers = {
        "Authorization": f"Bearer {settings.PROXY_API_KEY}",
        "Accept": "application/json",
    }
    params = {
        "limit": limit,
        "offset": offset,
        "date_str": "2020-03-01",
    }
    with httpx.Client(timeout=30) as client:
        r = client.get(url, headers=headers, params=params)
        r.raise_for_status()
    return r.json()


def get_booking_data():
    limit = 100
    offset = 0
    items_read = 100

    while items_read == limit:
        r = get_bookings_from_proxy(limit, offset)
        items_read = len(r)
        offset += limit
        for item in r:
            yield item


def update_booking(db, b_id, status):
    res = db.query(Booking).filter(Booking.booking_id == b_id).first()
    if res is None:
        print(f"Whoops! lost booking {b_id} in Bookings")
        return None
    else:
        res.booking_status = status
        return b_id


def completed_booking_ids(db, bids):
    for b in get_booking_data():
        if "id" in b:
            b_id = b["id"]
            if b_id in bids:
                if update_booking(db, b_id, "COMPLETED") == b_id:
                    print(f"completed match for {b_id}")
                    bids.remove(b_id)
    return bids


def cancelled_booking_ids(db, bids):
    for b in get_booking_data():
        if "id" in b:
            b_id = b["id"]
            if b_id in bids:
                if update_booking(db, b_id, "CANCELLED") == b_id:
                    print(f"cancelled match for {b_id}")
                    bids.remove(b_id)
    return bids


def mark_incomplete_booking_ids(db, bids):
    for b_id in bids:
        if update_booking(db, b_id, "NOT_COMPLETE") == b_id:
            print(f"marked NOT_COMPLETE: {b_id}")


def main():
    db = SessionLocal()
    try:
        res = db.query(Booking).filter(Booking.booking_status.is_(None)).all()

        print(f"booking ids to sort out = {len(res)}")

        if res:
            bids = {item.booking_id for item in res}
            print(bids)

            bids_remaining = completed_booking_ids(db, bids)
            db.commit()

            print(f"booking ids to resolve = {len(bids_remaining)}")

            bids_not_completed = cancelled_booking_ids(db, bids_remaining)
            db.commit()

            print(f"booking ids NOT_COMPLETED = {len(bids_not_completed)}")

            mark_incomplete_booking_ids(db, bids_not_completed)
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
