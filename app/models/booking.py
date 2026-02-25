"""Concrete booking models: Booking, Reservation, and SalesReservation."""

from sqlmodel import Field

from app.models.base import BookingBase


class Booking(BookingBase, table=True):
    """Standard cleaning booking."""

    __tablename__ = "bookings"
    id: int | None = Field(default=None, primary_key=True)


class Reservation(BookingBase, table=True):
    """NDIS reservation booking."""

    __tablename__ = "reservations"
    id: int | None = Field(default=None, primary_key=True)


class SalesReservation(BookingBase, table=True):
    """Sales reservation booking."""

    __tablename__ = "sales_reservations"
    id: int | None = Field(default=None, primary_key=True)
