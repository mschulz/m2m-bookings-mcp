"""Booking webhook endpoints and search routes."""

import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.utils.local_date_time import UTC_now, local_to_utc

from app.daos.booking import booking_dao

from app.services.bookings import (
    reject_booking,
    update_table,
    search_bookings,
    search_completed_bookings_by_service_date,
    get_booking_by_email_service_date,
)
from app.utils.klaviyo import process_with_klaviyo, WebhookRoute

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/booking",
    tags=["bookings"],
    dependencies=[Depends(verify_api_key)],
)


# --- POST endpoints ---


@router.post("/new", operation_id="create_new_booking")
async def new(data: dict, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Receive a new booking webhook from Zapier. Creates or updates the booking record."""
    logger.info("Processing a new booking ...")
    result = await update_table(data, db, status="NOT_COMPLETE")
    background_tasks.add_task(process_with_klaviyo, result, WebhookRoute.BOOKING_NEW)
    return "OK"


@router.post("/restored", operation_id="restore_booking")
async def restored(data: dict, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Receive a restored booking webhook from Zapier. Re-activates a previously cancelled booking."""
    logger.info("Processing a RESTORED booking ...")
    result = await update_table(data, db, status="NOT_COMPLETE", is_restored=True)
    background_tasks.add_task(process_with_klaviyo, result, WebhookRoute.BOOKING_RESTORED)
    return "OK"


@router.post("/completed", operation_id="complete_booking")
async def completed(data: dict, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Receive a completed booking webhook from Zapier. Marks the booking as completed."""
    logger.info("Processing a completed booking")
    result = await update_table(data, db, status="COMPLETED")
    background_tasks.add_task(process_with_klaviyo, result, WebhookRoute.BOOKING_COMPLETED)
    return "OK"


@router.post("/cancellation", operation_id="cancel_booking")
async def cancellation(data: dict, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Receive a cancellation webhook from Zapier. Marks the booking as cancelled and records the cancellation time."""
    logger.info("Processing a cancelled booking")
    if reject_booking(data):
        return "OK"

    data["_cancellation_datetime"] = UTC_now()
    result = await update_table(data, db, status="CANCELLED")
    background_tasks.add_task(process_with_klaviyo, result, WebhookRoute.BOOKING_CANCELLATION)
    return "OK"


@router.post("/updated", operation_id="update_booking")
async def updated(data: dict, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Receive an updated booking webhook from Zapier. Updates existing booking data."""
    logger.info("Processing an updated booking")
    result = await update_table(data, db)
    background_tasks.add_task(process_with_klaviyo, result, WebhookRoute.BOOKING_UPDATED)
    return "OK"


@router.post("/team_changed", operation_id="change_booking_team")
async def team_changed(data: dict, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Receive a team change webhook from Zapier. Updates the team assigned to a booking."""
    logger.info("Processing a team assignment change")
    result = await update_table(data, db, is_restored=True)
    background_tasks.add_task(process_with_klaviyo, result, WebhookRoute.BOOKING_TEAM_CHANGED)
    return "OK"


# --- GET endpoints ---


@router.get("", operation_id="search_bookings")
async def search(
    category: str = Query(..., description="Service category to filter by (e.g. 'House Clean', 'Bond Clean')"),
    date: str = Query(..., description="Date to search bookings for, in YYYY-MM-DD format"),
    booking_status: str = Query(..., description="Booking status filter (e.g. 'NOT_COMPLETE', 'COMPLETED', 'CANCELLED')"),
    db: AsyncSession = Depends(get_db),
):
    """Search bookings by service category, date, and status. Returns a list of matching bookings with name, location, and booking ID."""
    created_at = datetime.strptime(date, "%Y-%m-%d")
    start_created = local_to_utc(
        created_at.replace(hour=0, minute=0, second=0, microsecond=0)
    )
    end_created = local_to_utc(
        created_at.replace(hour=23, minute=59, second=59, microsecond=0)
    )
    return await search_bookings(db, category, start_created, end_created, booking_status.upper())


@router.get("/{booking_id}", operation_id="get_booking_details")
async def get_booking_details(booking_id: int, db: AsyncSession = Depends(get_db)):
    """Get full details of a specific booking by its ID. Returns all booking fields including customer info, dates, pricing, and team assignment."""
    res = await booking_dao.get_by_booking_id(db, booking_id)
    if res is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return res.model_dump(mode="json")


@router.get("/was_new_customer/{booking_id}", operation_id="check_was_new_customer")
async def get_was_new_customer(booking_id: int, db: AsyncSession = Depends(get_db)):
    """Check whether a booking was from a new customer."""
    res = await booking_dao.get_by_booking_id(db, booking_id)
    if res is not None:
        return {
            "was_new_customer": res.was_new_customer
            if hasattr(res, "was_new_customer")
            else False
        }
    return {"was_new_customer": False}


@router.get("/search/completed", operation_id="search_completed_bookings")
async def search_by_dates(
    from_date: str = Query(..., alias="from", description="Start date for the search range, in YYYY-MM-DD format"),
    to_date: str = Query(..., alias="to", description="End date for the search range, in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db),
):
    """Search completed bookings within a service date range. Returns booking details including team assignment, service info, and customer email."""
    return await search_completed_bookings_by_service_date(db, from_date, to_date)


@router.get("/service_date/search", operation_id="search_by_email_and_date")
async def search_by_service_date_and_email(
    service_date: str = Query(..., description="Service date to search for, in YYYY-MM-DD format"),
    email: str = Query(..., description="Customer email address to search for"),
    db: AsyncSession = Depends(get_db),
):
    """Find a booking by customer email and service date. Returns full booking details if found, or a 'not found' status."""
    return await get_booking_by_email_service_date(db, email, service_date)
