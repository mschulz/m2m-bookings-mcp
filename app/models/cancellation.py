"""Cancellation data import helper for updating existing booking records."""

from app.utils.validation import (
    check_postcode,
    truncate_field,
    parse_datetime,
    parse_date,
    dollar_string_to_int,
    string_to_boolean,
    safe_int,
)
from app.models.base import process_custom_fields


def apply_cancellation_data(d, b):
    """Apply cancellation-specific fields from webhook data *b* onto model *d*."""
    bid = b.get("booking_id")
    d.booking_id = safe_int(b["booking_id"])
    d.updated_at = parse_datetime(b.get("updated_at"))
    d.cancellation_type = truncate_field(b.get("cancellation_type"), 64, "cancellation_type", bid)
    d.cancelled_by = truncate_field(b.get("cancelled_by"), 64, "cancelled_by", bid)
    d.cancellation_date = parse_date(b.get("cancellation_date"))
    d.cancellation_datetime = b.get("_cancellation_datetime")
    d.cancellation_reason = b.get("cancellation_reason")
    if b.get("cancellation_fee") is not None and str(b.get("cancellation_fee")) != "":
        d.cancellation_fee = dollar_string_to_int(str(b["cancellation_fee"]))
    d.booking_status = truncate_field(b.get("booking_status"), 64, "booking_status", bid)
    d.is_first_recurring = string_to_boolean(b["is_first_recurring"]) if b.get("is_first_recurring") is not None else False
    if d.is_first_recurring:
        d.was_first_recurring = True
    d.is_new_customer = string_to_boolean(b["is_new_customer"]) if b.get("is_new_customer") is not None else False
    if d.is_new_customer:
        d.was_new_customer = True
    d.postcode = check_postcode(b, "booking_id", b["booking_id"])
    if b.get("location"):
        d.location = truncate_field(b["location"], 64, "location", bid)

    if "custom_fields" in b:
        process_custom_fields(d, b["custom_fields"], bid)
