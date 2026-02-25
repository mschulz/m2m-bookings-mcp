"""Pydantic schemas for booking API responses."""

from datetime import date

from pydantic import BaseModel


class BookingResponse(BaseModel):
    """Summary response returned for individual booking lookups."""

    booking_id: int | None = None
    name: str | None = None
    email: str | None = None
    service_category: str | None = None
    service: str | None = None
    booking_status: str | None = None
    service_date: date | str | None = None
    location: str | None = None
    teams_assigned: str | None = None
    frequency: str | None = None
    postcode: str | None = None
    created_by: str | None = None

    model_config = {"from_attributes": True}


class BookingSearchResult(BaseModel):
    """Compact result item returned by booking search endpoints."""

    category: str | None = None
    name: str | None = None
    location: str | None = None
    booking_id: int | None = None
