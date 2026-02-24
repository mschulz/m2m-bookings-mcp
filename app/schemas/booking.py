"""Pydantic schemas for booking webhook payloads and API responses."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class CustomerData(BaseModel):
    id: str | int
    first_name: str | None = None
    last_name: str | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    company_name: str | None = None
    zip: str | None = None
    postcode: str | None = None
    location: str | None = None
    notes: str | None = None
    tags: str | None = None
    title: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    profile_url: str | None = None

    model_config = {"extra": "allow"}


class BookingWebhookPayload(BaseModel):
    """Validates incoming webhook POST body from Zapier/proxy."""
    id: str | int
    created_at: str | None = None
    updated_at: str | None = None
    service_time: str | None = None
    service_date: str | None = None
    duration: str | int | None = None
    final_price: str | int | None = None
    extras_price: str | int | None = None
    subtotal: str | int | None = None
    tip: str | int | None = None
    payment_method: str | None = None
    frequency: str | None = None
    discount_code: str | None = None
    discount_amount: str | int | None = None
    giftcard_amount: str | int | None = None
    team_details: str | None = None
    team_share_amount: str | None = None
    team_share_total: str | None = None
    team_has_key: str | None = None
    team_requested: str | None = None
    created_by: str | None = None
    next_booking_date: str | None = None
    service_category: str | None = None
    service: str | None = None
    customer_notes: str | None = None
    staff_notes: str | None = None
    customer: CustomerData
    cancellation_type: str | None = None
    cancelled_by: str | None = None
    cancellation_date: str | None = None
    cancellation_reason: str | None = None
    cancellation_fee: str | int | None = None
    price_adjustment: str | int | None = None
    price_adjustment_comment: str | None = None
    booking_status: str | None = None
    is_first_recurring: str | bool | None = None
    is_new_customer: str | bool | None = None
    extras: str | None = None
    source: str | None = None
    state: str | None = None
    sms_notifications_enabled: str | bool | None = None
    pricing_parameters: str | None = None
    pricing_parameters_price: str | int | None = None

    # Customer fields at booking level
    address: str | None = None
    last_name: str | None = None
    city: str | None = None
    first_name: str | None = None
    name: str | None = None
    company_name: str | None = None
    email: str | None = None
    phone: str | None = None
    zip: str | None = None
    postcode: str | None = None
    location: str | None = None

    # Custom fields
    custom_fields: dict[str, Any] | None = None

    # Internal fields that may be added during processing
    _cancellation_datetime: datetime | None = None
    booking_id: str | int | None = None
    APP_NAME: str | None = None

    # Rating fields
    rating_value: str | int | None = None
    rating_text: str | None = None
    rating_comment: str | None = None

    model_config = {"extra": "allow"}


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
