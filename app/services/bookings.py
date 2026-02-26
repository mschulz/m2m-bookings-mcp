"""Booking business logic extracted from the router layer."""

import logging
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import exc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.daos.booking import booking_dao
from app.daos.customer import customer_dao

from app.utils.klaviyo import notify_klaviyo

logger = logging.getLogger(__name__)


def reject_booking(d: dict) -> bool:
    """Reject outright any booking request for a meeting or TBC/TBA postcodes."""
    if d.get("service_category") == "Internal Meeting":
        return True
    postcode = d.get("zip")
    if postcode is None or postcode.isnumeric():
        return False
    return postcode.lower() in ["tbc", "tba"]


async def update_table(
    data: dict,
    db: AsyncSession,
    status: str | None = None,
    is_restored: bool = False,
):
    """Route webhook data to the booking DAO.

    Returns the data dict so callers can trigger post-DB work (e.g. Klaviyo)
    after the DB session is released.
    """
    if reject_booking(data):
        return "OK"
    if status:
        data["booking_status"] = status

    logger.debug("Update Booking table")
    await booking_dao.create_update_booking(db, data)
    if not is_restored:
        await customer_dao.create_or_update_customer(db, data["customer"])
    return data


async def maybe_notify_klaviyo(data):
    """Send a Klaviyo notification if the booking is from a new customer."""
    if not isinstance(data, dict):
        return
    if not get_settings().KLAVIYO_ENABLED:
        return
    if data.get("is_new_customer"):
        logger.debug(
            "New customer: send %s to Klaviyo with %s",
            data.get("email"), data.get("service_category"),
        )
        if data.get("service_category") in ["Bond Clean", "House Clean"]:
            await notify_klaviyo(data["service_category"], data)


# --- Search helpers ---


async def search_bookings(
    db: AsyncSession, service_category, start_created, end_created, booking_status
):
    """Query bookings by category, status, and date range."""
    try:
        res = await booking_dao.get_by_date_range(
            db, service_category, booking_status, start_created, end_created
        )
    except exc.OperationalError as e:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from e

    return [
        {
            "category": item.service_category,
            "name": item.name,
            "location": item.location,
            "booking_id": item.booking_id,
        }
        for item in res
    ]


async def search_completed_bookings_by_service_date(db: AsyncSession, from_date_str, to_date_str):
    """Return completed bookings within a service date range as dicts."""
    start_date = datetime.strptime(from_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(to_date_str, "%Y-%m-%d").date()

    try:
        res = await booking_dao.completed_bookings_by_service_date(db, start_date, end_date)
    except exc.OperationalError as e:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from e

    return [
        {
            "booking_id": item.booking_id,
            "date_received": item.service_date.isoformat() if item.service_date else None,
            "service_date": item.service_date.isoformat() if item.service_date else None,
            "full_name": item.name,
            "email": item.email,
            "postcode": item.postcode,
            "location_name": item.location,
            "team_assigned": item.teams_assigned,
            "created_by": item.created_by,
            "service_category": item.service_category,
            "service": item.service,
            "frequency": item.frequency,
        }
        for item in res
    ]


async def get_booking_by_email_service_date(db: AsyncSession, email, service_date):
    """Look up a booking by customer email and service date week."""
    row = await booking_dao.get_by_booking_email_service_date_range(db, email, service_date)
    if row:
        return {
            "data": {
                "booking_id": row.booking_id,
                "date_received": None,
                "service_date": row.service_date.isoformat() if row.service_date else None,
                "full_name": f"{row.first_name} {row.last_name}",
                "email": row.email,
                "rating": None,
                "comment": "",
                "postcode": row.postcode,
                "location_name": row.location,
                "team_assigned": row.teams_assigned,
                "created_by": "",
                "service_category": row.service_category,
                "service": row.service,
                "frequency": row.frequency,
            },
            "status": "found",
        }
    return {"data": {}, "status": "not found"}
