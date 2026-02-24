# app/daos/booking.py

import logging
from datetime import datetime, timedelta

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.daos.base import BaseDAO
from app.models.booking import Booking

logger = logging.getLogger(__name__)


class BookingDAO(BaseDAO):
    def __init__(self, model):
        super().__init__(model)

    def get_by_booking_email_service_date_range(self, db: Session, email, service_date):
        def get_week_start_end(date_str):
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            dow = dt.weekday()
            offsets = ((-1, 5), (-2, 4), (-3, 3), (-4, 2), (-5, 1), (-6, 0), (0, 6))
            week_start = dt + timedelta(days=offsets[dow][0])
            week_end = dt + timedelta(days=offsets[dow][1])
            return (week_start.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d"))

        week_start, week_end = get_week_start_end(service_date)

        return (
            db.query(self.model)
            .filter_by(email=email)
            .filter(
                and_(
                    self.model._service_date >= week_start,
                    self.model._service_date <= week_end,
                )
            )
            .first()
        )

    def get_by_date_range(
        self, db: Session, service_category, booking_status, start_created, end_created
    ):
        logger.debug(
            "params: category=%s date=%s,%s booking_status=%s",
            service_category, start_created, end_created, booking_status,
        )

        return (
            db.query(self.model)
            .filter_by(service_category=service_category, booking_status=booking_status)
            .filter(
                and_(
                    self.model._created_at >= start_created,
                    self.model._created_at <= end_created,
                )
            )
            .all()
        )

    def completed_bookings_by_service_date(self, db: Session, from_date, to_date):
        return (
            db.query(self.model)
            .filter_by(booking_status="COMPLETED")
            .filter(
                and_(
                    self.model._service_date >= from_date,
                    self.model._service_date <= to_date,
                )
            )
            .all()
        )

    def get_bookings_missing_locations(self, db: Session):
        return db.query(self.model).filter(self.model.location.is_(None)).all()

    def get_all_bookings_after_service_date(self, db: Session, date_start):
        return db.query(self.model).filter(self.model._service_date >= date_start).all()


booking_dao = BookingDAO(Booking)
