# app/daos/dao_reservation.py

from flask import abort, current_app
from sqlalchemy import exc

from app import db
from app.daos.dao_base import BaseDAO
from app.models.models_booking import Reservation


class ReservationDAO(BaseDAO):
    def __init__(self, model):
        self.model = model
        super().__init__(model)

    def mark_converted(self, booking_id):
        if booking_id is None:
            return
        b = db.session.query(self.model).filter_by(booking_id=booking_id).first()
        current_app.logger.info("mark this booking as CONVERTED in database")
        b.booking_status = "CONVERTED"
        try:
            db.session.commit()
            current_app.logger.info(
                f"NDIS Reservation status changed to CONVERTED: {booking_id=}"
            )
        except exc.DataError:
            abort(422, description=f"NDIS Reservation data error: {booking_id=}")
        except exc.IntegrityError:
            db.session.rollback()
            current_app.logger.info(f"NDIS Reservation Inegrity error: {booking_id=}")
        except exc.OperationalError:
            db.session.rollback()
            current_app.logger.info("SSL connection has been closed unexpectedly")


reservation_dao = ReservationDAO(Reservation)
