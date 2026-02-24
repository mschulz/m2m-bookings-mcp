"""Booking status checks and cancellation notification webhook."""

import json
import logging
from datetime import datetime

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from config import get_settings

logger = logging.getLogger(__name__)


def is_missing_booking(data, db: Session, dao):
    """Check if this booking exists in the database."""
    booking_id = data.get("id")

    if not booking_id:
        logger.error("booking has no booking_id - ignore this data")
        raise HTTPException(status_code=422, detail="booking has no booking_id")

    b = dao.get_by_booking_id(db, booking_id)
    return b is None


def is_completed(data, db: Session, dao):
    """Check if booking is already marked COMPLETED."""
    booking_id = data.get("id")
    if not booking_id:
        return False
    b = dao.get_by_booking_id(db, booking_id)
    if b is None:
        return False
    return b.booking_status == "COMPLETED"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=10),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def notify_cancelled_completed(data):
    """Send cancellation data to the notification webhook."""
    settings = get_settings()
    url = settings.NOTIFICATION_URL
    data["APP_NAME"] = settings.APP_NAME

    updated_at_date = datetime.strptime(
        data["updated_at"], "%Y-%m-%dT%H:%M:%S%z"
    ).date()
    data["cancellation_date"] = updated_at_date.strftime("%d/%m/%Y")
    headers = {"content-type": "application/json"}

    with httpx.Client(timeout=10) as client:
        response = client.post(url, content=json.dumps(data), headers=headers)

    if response.status_code != 200:
        logger.warning(
            "Notification returned status_code=%d: %s",
            response.status_code, data,
        )
