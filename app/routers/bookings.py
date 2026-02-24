"""Booking webhook endpoints and search routes."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import exc
from sqlalchemy.orm import Session

from app.auth import verify_api_key
from app.database import get_db
from app.local_date_time import UTC_now, local_to_utc
from config import get_settings

from app.daos.booking import booking_dao
from app.daos.customer import customer_dao
from app.daos.reservation import reservation_dao
from app.daos.sales_reservation import sales_reservation_dao

from app.services.klaviyo import notify_klaviyo
from app.services.notifications import (
    is_missing_booking,
    is_completed,
    notify_cancelled_completed,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/booking",
    tags=["bookings"],
    dependencies=[Depends(verify_api_key)],
)


def reject_booking(d: dict) -> bool:
    """Reject outright any booking request for a meeting or TBC/TBA postcodes."""
    if d.get("service_category") == "Internal Meeting":
        return True
    postcode = d.get("zip")
    if postcode is None or postcode.isnumeric():
        return False
    return postcode.lower() in ["tbc", "tba"]


def update_table(
    data: dict,
    db: Session,
    status: str | None = None,
    check_ndis_reservation: bool = False,
    is_restored: bool = False,
):
    """Route webhook data to the correct DAO based on service_category."""
    settings = get_settings()

    if reject_booking(data):
        return "OK"
    if status:
        data["booking_status"] = status
    if data.get("service_category") == settings.RESERVATION_CATEGORY:
        logger.debug("Update NDIS Reservation table")
        reservation_dao.create_update_booking(db, data)
    elif data.get("service_category") == settings.SALES_RESERVATION_CATEGORY:
        logger.debug("Update Sales Reservation table")
        sales_reservation_dao.create_update_booking(db, data)
    else:
        logger.debug("Update Booking table")
        booking_id = data.get("id")
        if check_ndis_reservation:
            if reservation_dao.get_by_booking_id(db, booking_id):
                reservation_dao.mark_converted(db, booking_id)
            elif sales_reservation_dao.get_by_booking_id(db, booking_id):
                sales_reservation_dao.mark_converted(db, booking_id)
        booking_dao.create_update_booking(db, data)
        if not is_restored:
            customer_dao.create_or_update_customer(db, data["customer"])
        if data.get("is_new_customer"):
            logger.debug(
                "New customer: send %s to Klaviyo with %s",
                data.get("email"), data.get("service_category"),
            )
            if data.get("service_category") in ["Bond Clean", "House Clean"]:
                notify_klaviyo(data["service_category"], data)
    return "OK"


# --- Search helpers ---


def search_bookings(
    db: Session, service_category, start_created, end_created, booking_status
):
    """Query bookings or reservations by category, status, and date range."""
    settings = get_settings()
    try:
        if service_category == settings.RESERVATION_CATEGORY:
            res = reservation_dao.get_by_date_range(
                db, service_category, booking_status, start_created, end_created
            )
        else:
            res = booking_dao.get_by_date_range(
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


def search_completed_bookings_by_service_date(db: Session, from_date_str, to_date_str):
    """Return completed bookings within a service date range as dicts."""
    start_date = datetime.strptime(from_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(to_date_str, "%Y-%m-%d").date()

    try:
        res = booking_dao.completed_bookings_by_service_date(db, start_date, end_date)
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


def get_booking_by_email_service_date(db: Session, email, service_date):
    """Look up a booking by customer email and service date week."""
    row = booking_dao.get_by_booking_email_service_date_range(db, email, service_date)
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
    """Receive an updated booking webhook from Zapier. Updates existing booking data and checks for NDIS reservation conversion."""
    logger.info("Processing an updated booking")
    return update_table(data, db, check_ndis_reservation=True)


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
    return res.to_json()


@router.get("/was_new_customer/{booking_id}", operation_id="check_was_new_customer")
def get_was_new_customer(booking_id: int, db: Session = Depends(get_db)):
    """Check whether a booking was from a new customer. Searches across bookings, NDIS reservations, and sales reservations."""
    res = booking_dao.get_by_booking_id(db, booking_id)
    if res is not None:
        return {
            "was_new_customer": res.was_new_customer
            if hasattr(res, "was_new_customer")
            else False
        }
    res = reservation_dao.get_by_booking_id(db, booking_id)
    if res is not None:
        return {
            "was_new_customer": res.was_new_customer
            if hasattr(res, "was_new_customer")
            else False
        }
    res = sales_reservation_dao.get_by_booking_id(db, booking_id)
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
