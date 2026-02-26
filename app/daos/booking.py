"""Booking DAO with date-range and search query methods."""

import logging
from datetime import datetime, timedelta

from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.daos.base import BaseDAO
from app.models.booking import Booking

logger = logging.getLogger(__name__)


class BookingDAO(BaseDAO):
    async def get_by_booking_email_service_date_range(self, db: AsyncSession, email, service_date):
        """Find a booking by email within the same Mon-Sun week as service_date."""
        def get_week_start_end(date_str):
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            dow = dt.weekday()
            offsets = ((-1, 5), (-2, 4), (-3, 3), (-4, 2), (-5, 1), (-6, 0), (0, 6))
            week_start = dt + timedelta(days=offsets[dow][0])
            week_end = dt + timedelta(days=offsets[dow][1])
            return (week_start.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d"))

        week_start, week_end = get_week_start_end(service_date)

        result = await db.execute(
            select(self.model)
            .where(self.model.email == email)
            .where(
                and_(
                    self.model.service_date >= week_start,
                    self.model.service_date <= week_end,
                )
            )
        )
        return result.scalars().first()

    async def get_by_date_range(
        self, db: AsyncSession, service_category, booking_status, start_created, end_created
    ):
        """Query bookings by category, status, and created_at date range."""
        logger.debug(
            "params: category=%s date=%s,%s booking_status=%s",
            service_category, start_created, end_created, booking_status,
        )

        result = await db.execute(
            select(self.model)
            .where(
                self.model.service_category == service_category,
                self.model.booking_status == booking_status,
            )
            .where(
                and_(
                    self.model.created_at >= start_created,
                    self.model.created_at <= end_created,
                )
            )
        )
        return result.scalars().all()

    async def completed_bookings_by_service_date(self, db: AsyncSession, from_date, to_date):
        """Return all COMPLETED bookings within a service date range."""
        result = await db.execute(
            select(self.model)
            .where(self.model.booking_status == "COMPLETED")
            .where(
                and_(
                    self.model.service_date >= from_date,
                    self.model.service_date <= to_date,
                )
            )
        )
        return result.scalars().all()

    async def get_bookings_missing_locations(self, db: AsyncSession):
        """Return all bookings that have no location set."""
        result = await db.execute(
            select(self.model).where(self.model.location.is_(None))
        )
        return result.scalars().all()

    async def get_all_bookings_after_service_date(self, db: AsyncSession, date_start):
        """Return all bookings with a service date on or after date_start."""
        result = await db.execute(
            select(self.model).where(self.model.service_date >= date_start)
        )
        return result.scalars().all()


booking_dao = BookingDAO(Booking)
