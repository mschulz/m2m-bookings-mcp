# app/daos/base.py

import logging

from fastapi import HTTPException
from sqlalchemy import exc
from sqlalchemy.orm import Session

from app.models.cancellation import import_cancel_dict

logger = logging.getLogger(__name__)


class BaseDAO:
    def __init__(self, model):
        self.model = model

    def get_by_booking_id(self, db: Session, booking_id):
        return db.query(self.model).filter_by(booking_id=booking_id).first()

    def create_update_booking(self, db: Session, new_data):
        booking_id = new_data.get("id")
        if not booking_id:
            logger.error("booking has no booking_id - ignore this data")
            raise HTTPException(status_code=422, detail="booking has no booking_id")

        b = db.query(self.model).filter_by(booking_id=booking_id).first()

        if b is None:
            logger.info("haven't seen this booking - ADDING to database")
            b = self.model()
            b.import_dict(b, new_data)
            db.add(b)
        else:
            logger.info("have seen this booking - UPDATING database")
            bb = self.model()
            bb.import_dict(b, new_data)
            logger.info(
                'Loading ... Name: "%s" team: "%s" booking_id: %s',
                b.name, b.teams_assigned, b.booking_id,
            )

        try:
            db.commit()
        except exc.DataError:
            db.rollback()
            raise HTTPException(
                status_code=422, detail=f"Data error for booking: {b.to_dict()}"
            )
        except exc.IntegrityError:
            db.rollback()
            logger.info("Data already loaded into database: %s", b.to_dict())
        except exc.OperationalError:
            db.rollback()
            logger.info("SSL connection has been closed unexpectedly")

    def update_booking(self, db: Session, new_data):
        booking_id = new_data.get("booking_id")
        b = db.query(self.model).filter_by(booking_id=booking_id).first()
        logger.info("have seen this booking - UPDATING database")

        import_cancel_dict(b, new_data)

        logger.info(
            'Loading ... Name: "%s" team: "%s" booking_id: %s',
            b.name, b.teams_assigned, b.booking_id,
        )

        try:
            db.commit()
        except exc.DataError:
            db.rollback()
            raise HTTPException(
                status_code=422, detail=f"Data error for booking: {b.to_dict()}"
            )
        except exc.IntegrityError:
            db.rollback()
            logger.info("Data already loaded into database: %s", b.to_dict())
        except exc.OperationalError:
            db.rollback()
            logger.info("SSL connection has been closed unexpectedly")

    def cancel_booking(self, db: Session, new_data):
        booking_id = new_data.get("id")
        if booking_id is None:
            return
        db.query(self.model).filter_by(booking_id=booking_id).delete()
        try:
            db.commit()
            logger.info("Booking deleted from table: %s", booking_id)
        except exc.DataError:
            db.rollback()
            raise HTTPException(
                status_code=422, detail=f"Data error: {new_data}"
            )
        except exc.IntegrityError:
            db.rollback()
            logger.info("Integrity error: %s", new_data)
        except exc.OperationalError:
            db.rollback()
            logger.info("SSL connection has been closed unexpectedly")

    def mark_converted(self, db: Session, booking_id):
        """Mark a reservation as CONVERTED. Shared by Reservation and SalesReservation DAOs."""
        if booking_id is None:
            return
        b = db.query(self.model).filter_by(booking_id=booking_id).first()
        logger.info("mark this booking as CONVERTED in database")
        b.booking_status = "CONVERTED"
        try:
            db.commit()
            logger.info(
                "Reservation status changed to CONVERTED: booking_id=%s", booking_id
            )
        except exc.DataError:
            db.rollback()
            raise HTTPException(
                status_code=422,
                detail=f"Reservation data error: booking_id={booking_id}",
            )
        except exc.IntegrityError:
            db.rollback()
            logger.info("Reservation integrity error: booking_id=%s", booking_id)
        except exc.OperationalError:
            db.rollback()
            logger.info("SSL connection has been closed unexpectedly")
