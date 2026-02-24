"""Concrete booking models: Booking, Reservation, and SalesReservation."""

from sqlalchemy import Column, Integer

from app.models.base import BookingBase


class Booking(BookingBase):
    """Standard cleaning booking."""

    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)


class Reservation(BookingBase):
    """NDIS reservation booking."""

    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True)


class SalesReservation(BookingBase):
    """Sales reservation booking."""

    __tablename__ = "sales_reservations"
    id = Column(Integer, primary_key=True)
