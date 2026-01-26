# app/models/model_cancel.py

from app.models.model_base import (
    check_postcode, 
    process_custom_fields
)
from app.locations import get_location


def import_cancel_dict(d, b):
    d.booking_id = b["booking_id"]
    d.updated_at = b.get("updated_at")
    d.cancellation_type = b.get("cancellation_type")
    d.cancelled_by = b.get("cancelled_by")
    d.cancellation_date = b.get("cancellation_date")
    d._cancellation_datetime = b.get("_cancellation_datetime")
    d.cancellation_reason = b.get("cancellation_reason")
    d.cancellation_fee = b.get("cancellation_fee")
    d.booking_status = b.get("booking_status")
    d.is_first_recurring = b.get("is_first_recurring")
    if d.is_first_recurring:
        d.was_first_recurring = True
    d.is_new_customer = b.get("is_new_customer")
    if d.is_new_customer:
        d.was_new_customer = True
    d.postcode = check_postcode(b, "booking_id", b["booking_id"])
    if d.postcode:
        d.location = b.get("location", get_location(d.postcode))

    # Custom field data
    if "custom_fields" in b:
        process_custom_fields(d, b["custom_fields"])
