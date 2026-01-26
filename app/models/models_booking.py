# app/model_booking.py

from app import db
from app.models.model_base import BookingBase


class Booking(BookingBase):
    """
    Booking class holds all the data for the current booking.
    Data could come from the database or from an incoming zap.
    """

    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)


class Reservation(BookingBase):
    """
    Reservation class holds all the data for the current reservation.
    Data could come from the database or from an incoming zap.
    """

    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)


class SalesReservation(BookingBase):
    """
    Reservation class holds all the data for the current reservation.
    Data could come from the database or from an incoming zap.
    """

    __tablename__ = "sales_reservations"

    id = db.Column(db.Integer, primary_key=True)
