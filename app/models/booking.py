"""Concrete booking model."""

from sqlmodel import Field

from app.models.base import BookingBase


class Booking(BookingBase, table=True):
    """Standard cleaning booking."""

    __tablename__ = "bookings"
    id: int | None = Field(default=None, primary_key=True)
