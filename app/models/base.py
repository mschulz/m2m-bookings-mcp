"""Base booking model with all shared columns and webhook import logic."""

import logging
from datetime import datetime, date

from sqlalchemy import Text, DateTime
from sqlmodel import SQLModel, Field

from app.utils.validation import (
    string_to_boolean,
    dollar_string_to_int,
    check_postcode,
    truncate_field,
    parse_datetime,
    parse_date,
    parse_team_list,
    parse_team_share,
    safe_int,
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class BookingBase(SQLModel):
    """BookingBase defines all shared columns for the bookings table."""

    booking_id: int | None = Field(default=None, sa_column_kwargs={"index": True, "unique": True})

    # Underscore DB columns mapped to clean field names
    created_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True), sa_column_kwargs={"name": "_created_at"})
    updated_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True), sa_column_kwargs={"name": "_updated_at"})
    service_date: date | None = Field(default=None, sa_column_kwargs={"name": "_service_date"})
    final_price: int | None = Field(default=None, sa_column_kwargs={"name": "_final_price"})
    extras_price: int | None = Field(default=None, sa_column_kwargs={"name": "_extras_price"})
    subtotal: int | None = Field(default=None, sa_column_kwargs={"name": "_subtotal"})
    tip: int | None = Field(default=None, sa_column_kwargs={"name": "_tip"})
    rating_value: int | None = Field(default=None, sa_column_kwargs={"name": "_rating_value"})
    rating_comment_presence: bool | None = Field(default=None, sa_column_kwargs={"name": "_rating_comment_presence"})
    discount_from_code: int | None = Field(default=None, sa_column_kwargs={"name": "_discount_from_code"})
    giftcard_amount: int | None = Field(default=None, sa_column_kwargs={"name": "_giftcard_amount"})
    teams_assigned: str | None = Field(default=None, max_length=80, sa_column_kwargs={"name": "_teams_assigned"})
    teams_assigned_ids: str | None = Field(default=None, max_length=80, sa_column_kwargs={"name": "_teams_assigned_ids"})
    team_share: int | None = Field(default=None, sa_column_kwargs={"name": "_team_share"})
    next_booking_date: datetime | None = Field(default=None, sa_type=DateTime(timezone=True), sa_column_kwargs={"name": "_next_booking_date"})
    customer_id: int | None = Field(default=None, sa_column_kwargs={"name": "_customer_id"})
    cancellation_date: date | None = Field(default=None, sa_column_kwargs={"name": "_cancellation_date", "nullable": True})
    cancellation_fee: int | None = Field(default=None, sa_column_kwargs={"name": "_cancellation_fee"})
    cancellation_datetime: datetime | None = Field(default=None, sa_type=DateTime(timezone=True), sa_column_kwargs={"name": "_cancellation_datetime"})
    price_adjustment: int | None = Field(default=None, sa_column_kwargs={"name": "_price_adjustment"})
    is_first_recurring: bool | None = Field(default=None, sa_column_kwargs={"name": "_is_first_recurring"})
    is_new_customer: bool | None = Field(default=None, sa_column_kwargs={"name": "_is_new_customer"})
    sms_notifications_enabled: bool | None = Field(default=None, sa_column_kwargs={"name": "_sms_notifications_enabled"})
    pricing_parameters_price: int | None = Field(default=None, sa_column_kwargs={"name": "_pricing_parameters_price"})
    invoice_tobe_emailed: bool | None = Field(default=None, sa_column_kwargs={"name": "_invoice_tobe_emailed"})

    # Regular columns
    service_time: str | None = Field(default=None, max_length=64)
    duration: str | None = Field(default=None, max_length=32)
    payment_method: str | None = Field(default=None, max_length=64)
    rating_text: str | None = Field(default=None, sa_type=Text)
    rating_comment: str | None = Field(default=None, sa_type=Text)
    rating_created_by: str | None = Field(default=None, max_length=64)
    rating_received: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    rating_modified: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    rating_modified_by: str | None = Field(default=None, max_length=64)
    frequency: str | None = Field(default=None, max_length=64)
    discount_code: str | None = Field(default=None, max_length=64)
    team_share_summary: str | None = Field(default=None, max_length=128)
    team_has_key: str | None = Field(default=None, max_length=64)
    team_requested: str | None = Field(default=None, max_length=80)
    created_by: str | None = Field(default=None, max_length=64)
    service_category: str | None = Field(default=None, max_length=64)
    service: str | None = Field(default=None, max_length=128)
    customer_notes: str | None = Field(default=None, sa_type=Text)
    staff_notes: str | None = Field(default=None, sa_type=Text)
    cancellation_type: str | None = Field(default=None, max_length=64)
    cancelled_by: str | None = Field(default=None, max_length=64)
    cancellation_reason: str | None = Field(default=None, sa_type=Text)
    price_adjustment_comment: str | None = Field(default=None, sa_type=Text)
    booking_status: str | None = Field(default=None, max_length=64)
    was_first_recurring: bool | None = Field(default=False)
    was_new_customer: bool | None = Field(default=False)
    extras: str | None = Field(default=None, sa_type=Text)
    source: str | None = Field(default=None, max_length=64)
    pricing_parameters: str | None = Field(default=None, max_length=64)

    # Customer data
    address: str | None = Field(default=None, max_length=128)
    last_name: str | None = Field(default=None, max_length=64)
    city: str | None = Field(default=None, max_length=64)
    state: str | None = Field(default=None, max_length=32)
    first_name: str | None = Field(default=None, max_length=64)
    company_name: str | None = Field(default=None, max_length=64)
    email: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, max_length=128)
    phone: str | None = Field(default=None, max_length=64)
    postcode: str | None = Field(default=None, max_length=16)
    location: str | None = Field(default=None, max_length=64)

    # Custom field data
    lead_source: str | None = Field(default=None, max_length=64)
    booked_by: str | None = Field(default=None, max_length=64)
    invoice_name: str | None = Field(default=None, max_length=128)
    NDIS_who_pays: str | None = Field(default=None, max_length=64)
    invoice_email: str | None = Field(default=None, max_length=64)
    last_service: str | None = Field(default=None, max_length=80)
    invoice_reference: str | None = Field(default=None, max_length=80)
    invoice_reference_extra: str | None = Field(default=None, max_length=80)
    NDIS_reference: str | None = Field(default=None, max_length=64)
    flexible_date_time: str | None = Field(default=None, max_length=64)
    hourly_notes: str | None = Field(default=None, sa_type=Text)

    def __repr__(self):
        return f"<Booking {self.id}>"

    @classmethod
    def from_webhook(cls, data: dict):
        """Create a new instance from webhook data dict."""
        instance = cls()
        _apply_webhook_data(instance, data)
        return instance

    def update_from_webhook(self, data: dict):
        """Update this instance from webhook data dict."""
        _apply_webhook_data(self, data)


def _apply_webhook_data(d, b: dict) -> None:
    """Apply webhook dict to a model instance with explicit coercion."""
    settings = get_settings()
    bid = b.get("id")

    if "id" in b:
        d.booking_id = safe_int(b["id"])
    d.created_at = parse_datetime(b.get("created_at"))
    d.updated_at = parse_datetime(b.get("updated_at"))
    d.service_time = truncate_field(b.get("service_time"), 64, "service_time", bid)
    d.service_date = parse_date(b.get("service_date"))
    d.duration = truncate_field(b.get("duration"), 32, "duration", bid)
    d.final_price = dollar_string_to_int(b.get("final_price")) if b.get("final_price") is not None else None
    d.extras_price = dollar_string_to_int(b.get("extras_price")) if b.get("extras_price") is not None else None
    d.subtotal = dollar_string_to_int(b.get("subtotal")) if b.get("subtotal") is not None else None
    d.tip = dollar_string_to_int(b.get("tip")) if b.get("tip") is not None else None
    d.payment_method = truncate_field(b.get("payment_method"), 64, "payment_method", bid)
    d.frequency = truncate_field(b.get("frequency"), 64, "frequency", bid)
    if "discount_code" in b:
        d.discount_code = truncate_field(b["discount_code"], 64, "discount_code", bid)
    d.discount_from_code = dollar_string_to_int(b.get("discount_amount")) if b.get("discount_amount") is not None else None
    d.giftcard_amount = dollar_string_to_int(b.get("giftcard_amount")) if b.get("giftcard_amount") is not None else None
    if "team_details" in b:
        d.teams_assigned = parse_team_list(b["team_details"], "title")
        d.teams_assigned_ids = parse_team_list(b["team_details"], "id")
    if "team_share_amount" in b:
        d.team_share = parse_team_share(b["team_share_amount"])
    if "team_share_total" in b:
        d.team_share_summary = truncate_field(b["team_share_total"], 128, "team_share_summary", bid)
    d.team_has_key = truncate_field(b.get("team_has_key"), 64, "team_has_key", bid)
    d.team_requested = truncate_field(b.get("team_requested"), 80, "team_requested", bid)
    d.created_by = truncate_field(b.get("created_by"), 64, "created_by", bid)
    if "next_booking_date" in b:
        d.next_booking_date = parse_datetime(b["next_booking_date"])
    d.service_category = truncate_field(
        b.get("service_category", settings.SERVICE_CATEGORY_DEFAULT),
        64, "service_category", bid,
    )
    if "service" in b:
        d.service = truncate_field(b["service"], 128, "service", bid)
    d.customer_notes = b.get("customer_notes")
    d.staff_notes = b.get("staff_notes")
    d.customer_id = safe_int(b.get("customer", {}).get("id"))
    d.cancellation_type = truncate_field(b.get("cancellation_type"), 64, "cancellation_type", bid)
    d.cancelled_by = truncate_field(b.get("cancelled_by"), 64, "cancelled_by", bid)
    d.cancellation_date = parse_date(b.get("cancellation_date"))
    d.cancellation_datetime = b.get("_cancellation_datetime")
    d.cancellation_reason = b.get("cancellation_reason")
    d.cancellation_fee = _parse_dollar_field(b.get("cancellation_fee"))
    d.price_adjustment = _parse_dollar_field(b.get("price_adjustment"))
    d.price_adjustment_comment = b.get("price_adjustment_comment")
    d.booking_status = truncate_field(b.get("booking_status"), 64, "booking_status", bid)
    d.is_first_recurring = string_to_boolean(b["is_first_recurring"]) if b.get("is_first_recurring") is not None else False
    if d.is_first_recurring:
        d.was_first_recurring = True
    d.is_new_customer = string_to_boolean(b["is_new_customer"]) if b.get("is_new_customer") is not None else False
    if d.is_new_customer:
        d.was_new_customer = True
    d.extras = b.get("extras")
    d.source = truncate_field(b.get("source"), 64, "source", bid)
    d.state = truncate_field(b.get("state"), 32, "state", bid)
    d.sms_notifications_enabled = string_to_boolean(b["sms_notifications_enabled"]) if b.get("sms_notifications_enabled") is not None else None
    d.pricing_parameters = truncate_field(b.get("pricing_parameters"), 64, "pricing_parameters", bid)
    if d.pricing_parameters:
        d.pricing_parameters = d.pricing_parameters.replace("<br/>", ", ")
    d.pricing_parameters_price = _parse_dollar_field(b.get("pricing_parameters_price"))

    # Customer data
    d.address = truncate_field(b.get("address"), 128, "address", bid)
    d.last_name = truncate_field(b.get("last_name"), 64, "last_name", bid)
    d.city = truncate_field(b.get("city"), 64, "city", bid)
    d.first_name = truncate_field(b.get("first_name"), 64, "first_name", bid)
    d.name = truncate_field(b.get("name"), 128, "name", bid)
    d.company_name = truncate_field(b.get("company_name"), 64, "company_name", bid)
    d.email = truncate_field(b.get("email"), 64, "email", bid)
    d.phone = truncate_field(b.get("phone"), 64, "phone", bid)
    d.postcode = check_postcode(b, "booking_id", b.get("id"))
    if b.get("location"):
        d.location = truncate_field(b["location"], 64, "location", bid)

    # Custom field data
    if "custom_fields" in b:
        process_custom_fields(d, b["custom_fields"], bid)


def _parse_dollar_field(val) -> int | None:
    """Parse a dollar/price value to cents, handling str/int/None."""
    if val is None:
        return None
    val_str = str(val)
    if len(val_str) == 0:
        return None
    try:
        return dollar_string_to_int(val_str)
    except ValueError as e:
        logger.error("price parse error (%s): %s", val, e)
        return None


def process_custom_fields(d, b_cf, record_id=None):
    """Map webhook custom_fields dict onto model custom-field columns."""
    settings = get_settings()

    if settings.CUSTOM_SOURCE and settings.CUSTOM_SOURCE in b_cf:
        d.lead_source = truncate_field(b_cf[settings.CUSTOM_SOURCE], 64, "lead_source", record_id)

    if settings.CUSTOM_BOOKED_BY and settings.CUSTOM_BOOKED_BY in b_cf:
        d.booked_by = truncate_field(b_cf[settings.CUSTOM_BOOKED_BY], 64, "booked_by", record_id)

    if settings.CUSTOM_EMAIL_INVOICE and settings.CUSTOM_EMAIL_INVOICE in b_cf:
        d.invoice_tobe_emailed = string_to_boolean(b_cf[settings.CUSTOM_EMAIL_INVOICE]) if b_cf.get(settings.CUSTOM_EMAIL_INVOICE) is not None else None

    if settings.CUSTOM_INVOICE_NAME and settings.CUSTOM_INVOICE_NAME in b_cf:
        d.invoice_name = truncate_field(b_cf.get(settings.CUSTOM_INVOICE_NAME), 128, "invoice_name", record_id)

    if settings.CUSTOM_WHO_PAYS and settings.CUSTOM_WHO_PAYS in b_cf:
        d.NDIS_who_pays = truncate_field(b_cf.get(settings.CUSTOM_WHO_PAYS), 64, "NDIS_who_pays", record_id)

    if settings.CUSTOM_INVOICE_EMAIL_ADDRESS and settings.CUSTOM_INVOICE_EMAIL_ADDRESS in b_cf:
        d.invoice_email = truncate_field(b_cf[settings.CUSTOM_INVOICE_EMAIL_ADDRESS], 64, "invoice_email", record_id)

    if settings.CUSTOM_LAST_SERVICE and settings.CUSTOM_LAST_SERVICE in b_cf:
        d.last_service = truncate_field(b_cf.get(settings.CUSTOM_LAST_SERVICE), 80, "last_service", record_id)

    if settings.CUSTOM_INVOICE_REFERENCE and settings.CUSTOM_INVOICE_REFERENCE in b_cf:
        d.invoice_reference = truncate_field(b_cf.get(settings.CUSTOM_INVOICE_REFERENCE), 80, "invoice_reference", record_id)

    if settings.CUSTOM_INVOICE_REFERENCE_EXTRA and settings.CUSTOM_INVOICE_REFERENCE_EXTRA in b_cf:
        d.invoice_reference_extra = truncate_field(b_cf.get(settings.CUSTOM_INVOICE_REFERENCE_EXTRA), 80, "invoice_reference_extra", record_id)

    if settings.CUSTOM_NDIS_NUMBER and settings.CUSTOM_NDIS_NUMBER in b_cf:
        d.NDIS_reference = truncate_field(b_cf.get(settings.CUSTOM_NDIS_NUMBER), 64, "NDIS_reference", record_id)

    if settings.CUSTOM_FLEXIBLE and settings.CUSTOM_FLEXIBLE in b_cf:
        d.flexible_date_time = truncate_field(b_cf.get(settings.CUSTOM_FLEXIBLE), 64, "flexible_date_time", record_id)

    if settings.CUSTOM_HOURLY_NOTES and settings.CUSTOM_HOURLY_NOTES in b_cf:
        d.hourly_notes = b_cf.get(settings.CUSTOM_HOURLY_NOTES)

    return d
