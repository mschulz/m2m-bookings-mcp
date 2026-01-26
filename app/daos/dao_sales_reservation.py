# app/daos/dao_sales_reservation.py

from app import db
from app.daos.dao_base import BaseDAO

from app.models.models_booking import SalesReservation
from flask import current_app, abort
from sqlalchemy import exc


class SalesReservationDAO(BaseDAO):
    def __init__(self, model):
        self.model = model
        super().__init__(model)

    def mark_converted(self, booking_id):
        if booking_id is None:
            return
        b = db.session.query(self.model).filter_by(booking_id=booking_id).first()
        current_app.logger.info("mark this booking as CONVERTED in table")
        b.booking_status = "CONVERTED"
        try:
            db.session.commit()
            current_app.logger.info(
                f"Sales Reservation status changed to CONVERTED: {booking_id=}"
            )
        except exc.DataError:
            abort(422, description=f"Sales Reservation data error: {booking_id=}")
        except exc.IntegrityError:
            db.session.rollback()
            current_app.logger.info(f"Sales Reservation Inegrity error: {booking_id=}")
        except exc.OperationalError:
            db.session.rollback()
            current_app.logger.info("SSL connection has been closed unexpectedly")


sales_reservation_dao = SalesReservationDAO(SalesReservation)
