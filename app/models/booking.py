# app/models/booking.py

from sqlalchemy import Column, Integer

from app.models.base import BookingBase


class Booking(BookingBase):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)


class Reservation(BookingBase):
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True)


class SalesReservation(BookingBase):
    __tablename__ = "sales_reservations"
    id = Column(Integer, primary_key=True)
