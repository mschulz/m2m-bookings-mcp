"""Cancellation data import helper for updating existing booking records."""

from app.utils.validation import check_postcode, truncate_field
from app.models.base import process_custom_fields


def import_cancel_dict(d, b):
    """Apply cancellation-specific fields from webhook data *b* onto model *d*."""
    bid = b.get("booking_id")
    d.booking_id = b["booking_id"]
    d.updated_at = b.get("updated_at")
    d.cancellation_type = truncate_field(b.get("cancellation_type"), 64, "cancellation_type", bid)
    d.cancelled_by = truncate_field(b.get("cancelled_by"), 64, "cancelled_by", bid)
    d.cancellation_date = b.get("cancellation_date")
    d._cancellation_datetime = b.get("_cancellation_datetime")
    d.cancellation_reason = b.get("cancellation_reason")
    d.cancellation_fee = b.get("cancellation_fee")
    d.booking_status = truncate_field(b.get("booking_status"), 64, "booking_status", bid)
    d.is_first_recurring = b.get("is_first_recurring")
    if d.is_first_recurring:
        d.was_first_recurring = True
    d.is_new_customer = b.get("is_new_customer")
    if d.is_new_customer:
        d.was_new_customer = True
    d.postcode = check_postcode(b, "booking_id", b["booking_id"])
    if d.postcode:
        from app.services.locations import get_location
        d.location = truncate_field(
            b.get("location", get_location(d.postcode)),
            64, "location", bid,
        )

    if "custom_fields" in b:
        process_custom_fields(d, b["custom_fields"], bid)
