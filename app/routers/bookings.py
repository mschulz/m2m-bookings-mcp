"""Booking webhook endpoints and search routes."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.utils.local_date_time import UTC_now, local_to_utc

from app.daos.booking import booking_dao

from app.utils.notifications import (
    is_missing_booking,
    is_completed,
    notify_cancelled_completed,
)

from app.services.bookings import (
    reject_booking,
    update_table,
    search_bookings,
    search_completed_bookings_by_service_date,
    get_booking_by_email_service_date,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/booking",
    tags=["bookings"],
    dependencies=[Depends(verify_api_key)],
)


# --- POST endpoints ---


@router.post("/new", operation_id="create_new_booking")
def new(data: dict, db: Session = Depends(get_db)):
    """Receive a new booking webhook from Zapier. Creates or updates the booking record."""
    logger.info("Processing a new booking ...")
    return update_table(data, db, status="NOT_COMPLETE")


@router.post("/restored", operation_id="restore_booking")
def restored(data: dict, db: Session = Depends(get_db)):
    """Receive a restored booking webhook from Zapier. Re-activates a previously cancelled booking."""
    logger.info("Processing a RESTORED booking ...")
    return update_table(data, db, status="NOT_COMPLETE", is_restored=True)


@router.post("/completed", operation_id="complete_booking")
def completed(data: dict, db: Session = Depends(get_db)):
    """Receive a completed booking webhook from Zapier. Marks the booking as completed."""
    logger.info("Processing a completed booking")
    return update_table(data, db, status="COMPLETED")


@router.post("/cancellation", operation_id="cancel_booking")
def cancellation(data: dict, db: Session = Depends(get_db)):
    """Receive a cancellation webhook from Zapier. Marks the booking as cancelled and records the cancellation time."""
    logger.info("Processing a cancelled booking")
    if reject_booking(data):
        return "OK"

    if not is_missing_booking(data, db, booking_dao):
        if is_completed(data, db, booking_dao):
            notify_cancelled_completed(data)

    data["_cancellation_datetime"] = UTC_now()
    return update_table(data, db, status="CANCELLED")


@router.post("/updated", operation_id="update_booking")
def updated(data: dict, db: Session = Depends(get_db)):
    """Receive an updated booking webhook from Zapier. Updates existing booking data."""
    logger.info("Processing an updated booking")
    return update_table(data, db)


@router.post("/team_changed", operation_id="change_booking_team")
def team_changed(data: dict, db: Session = Depends(get_db)):
    """Receive a team change webhook from Zapier. Updates the team assigned to a booking."""
    logger.info("Processing a team assignment change")
    return update_table(data, db, is_restored=True)


# --- GET endpoints ---


@router.get("", operation_id="search_bookings")
def search(
    category: str = Query(..., description="Service category to filter by (e.g. 'House Clean', 'Bond Clean')"),
    date: str = Query(..., description="Date to search bookings for, in YYYY-MM-DD format"),
    booking_status: str = Query(..., description="Booking status filter (e.g. 'NOT_COMPLETE', 'COMPLETED', 'CANCELLED')"),
    db: Session = Depends(get_db),
):
    """Search bookings by service category, date, and status. Returns a list of matching bookings with name, location, and booking ID."""
    created_at = datetime.strptime(date, "%Y-%m-%d")
    start_created = local_to_utc(
        created_at.replace(hour=0, minute=0, second=0, microsecond=0)
    )
    end_created = local_to_utc(
        created_at.replace(hour=23, minute=59, second=59, microsecond=0)
    )
    return search_bookings(db, category, start_created, end_created, booking_status.upper())


@router.get("/{booking_id}", operation_id="get_booking_details")
def get_booking_details(booking_id: int, db: Session = Depends(get_db)):
    """Get full details of a specific booking by its ID. Returns all booking fields including customer info, dates, pricing, and team assignment."""
    res = booking_dao.get_by_booking_id(db, booking_id)
    if res is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return res.model_dump(mode="json")


@router.get("/was_new_customer/{booking_id}", operation_id="check_was_new_customer")
def get_was_new_customer(booking_id: int, db: Session = Depends(get_db)):
    """Check whether a booking was from a new customer."""
    res = booking_dao.get_by_booking_id(db, booking_id)
    if res is not None:
        return {
            "was_new_customer": res.was_new_customer
            if hasattr(res, "was_new_customer")
            else False
        }
    return {"was_new_customer": False}


@router.get("/search/completed", operation_id="search_completed_bookings")
def search_by_dates(
    from_date: str = Query(..., alias="from", description="Start date for the search range, in YYYY-MM-DD format"),
    to_date: str = Query(..., alias="to", description="End date for the search range, in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
):
    """Search completed bookings within a service date range. Returns booking details including team assignment, service info, and customer email."""
    return search_completed_bookings_by_service_date(db, from_date, to_date)


@router.get("/service_date/search", operation_id="search_by_email_and_date")
def search_by_service_date_and_email(
    service_date: str = Query(..., description="Service date to search for, in YYYY-MM-DD format"),
    email: str = Query(..., description="Customer email address to search for"),
    db: Session = Depends(get_db),
):
    """Find a booking by customer email and service date. Returns full booking details if found, or a 'not found' status."""
    return get_booking_by_email_service_date(db, email, service_date)
