"""Tests for app/models/booking.py — Booking webhook import logic."""

from unittest.mock import patch

import pytest

from app.models.booking import (
    Booking,
    _parse_dollar_field,
    process_custom_fields,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _base_webhook(**overrides):
    """Return a minimal valid booking webhook payload."""
    data = {
        "id": "12345",
        "created_at": "2024-01-15T10:00:00+10:00",
        "updated_at": "2024-01-15T10:00:00+10:00",
        "service_date": "2024-02-15",
        "service_time": "09:00 AM",
        "duration": "3 hours",
        "final_price": "$143.00",
        "booking_status": "NOT_COMPLETE",
        "service_category": "House Clean",
        "is_first_recurring": "false",
        "is_new_customer": "false",
        "first_name": "Jane",
        "last_name": "Smith",
        "name": "Jane Smith",
        "email": "jane@example.com",
        "phone": "0412345678",
        "zip": "3000",
        "address": "123 Test St",
        "city": "Melbourne",
        "state": "VIC",
        "customer": {"id": "67890"},
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# from_webhook
# ---------------------------------------------------------------------------


class TestFromWebhook:
    def test_sets_booking_id(self):
        b = Booking.from_webhook(_base_webhook())
        assert b.booking_id == 12345

    def test_converts_final_price_to_cents(self):
        b = Booking.from_webhook(_base_webhook(final_price="$143.00"))
        assert b.final_price == 14300

    def test_converts_subtotal_to_cents(self):
        b = Booking.from_webhook(_base_webhook(subtotal="$120.00"))
        assert b.subtotal == 12000

    def test_none_price_stored_as_none(self):
        data = _base_webhook()
        data.pop("final_price", None)
        b = Booking.from_webhook(data)
        assert b.final_price is None

    def test_sets_service_category(self):
        b = Booking.from_webhook(_base_webhook(service_category="Bond Clean"))
        assert b.service_category == "Bond Clean"

    def test_default_service_category_applied(self):
        data = _base_webhook()
        data.pop("service_category", None)
        b = Booking.from_webhook(data)
        # Falls back to settings.SERVICE_CATEGORY_DEFAULT ("House Clean")
        assert b.service_category == "House Clean"

    def test_sets_customer_id_from_nested_dict(self):
        b = Booking.from_webhook(_base_webhook())
        assert b.customer_id == 67890

    def test_valid_postcode_stored(self):
        b = Booking.from_webhook(_base_webhook(zip="3000"))
        assert b.postcode == "3000"

    def test_non_numeric_postcode_rejected(self):
        b = Booking.from_webhook(_base_webhook(zip="TBC"))
        assert b.postcode is None

    def test_location_set_when_provided(self):
        b = Booking.from_webhook(_base_webhook(location="Melbourne"))
        assert b.location == "Melbourne"

    def test_location_not_set_when_absent(self):
        data = _base_webhook()
        data.pop("location", None)
        b = Booking.from_webhook(data)
        assert b.location is None

    def test_is_new_customer_true(self):
        b = Booking.from_webhook(_base_webhook(is_new_customer="true"))
        assert b.is_new_customer is True
        assert b.was_new_customer is True

    def test_is_new_customer_false_does_not_set_was(self):
        b = Booking.from_webhook(_base_webhook(is_new_customer="false"))
        assert b.is_new_customer is False
        assert b.was_new_customer is False

    def test_is_first_recurring_sets_was(self):
        b = Booking.from_webhook(_base_webhook(is_first_recurring="true"))
        assert b.is_first_recurring is True
        assert b.was_first_recurring is True

    def test_pricing_parameters_br_tag_replaced(self):
        b = Booking.from_webhook(_base_webhook(pricing_parameters="2 bed<br/>3 bath"))
        assert "<br/>" not in b.pricing_parameters
        assert "2 bed, 3 bath" == b.pricing_parameters

    def test_team_details_parsed(self):
        data = _base_webhook(
            team_details="[{'title': 'Alice', 'id': '1'}, {'title': 'Bob', 'id': '2'}]"
        )
        b = Booking.from_webhook(data)
        assert b.teams_assigned == "Alice,Bob"
        assert b.teams_assigned_ids == "1,2"


# ---------------------------------------------------------------------------
# update_from_webhook
# ---------------------------------------------------------------------------


class TestUpdateFromWebhook:
    def test_updates_booking_status(self):
        b = Booking.from_webhook(_base_webhook())
        b.update_from_webhook(_base_webhook(booking_status="COMPLETED"))
        assert b.booking_status == "COMPLETED"

    def test_updates_final_price(self):
        b = Booking.from_webhook(_base_webhook())
        b.update_from_webhook(_base_webhook(final_price="$200.00"))
        assert b.final_price == 20000

    def test_updates_email(self):
        b = Booking.from_webhook(_base_webhook())
        b.update_from_webhook(_base_webhook(email="new@example.com"))
        assert b.email == "new@example.com"


# ---------------------------------------------------------------------------
# update_from_cancellation
# ---------------------------------------------------------------------------


class TestUpdateFromCancellation:
    def _cancel_data(self, **overrides):
        data = {
            "booking_id": "12345",
            "updated_at": "2024-03-01T12:00:00+10:00",
            "cancellation_type": "Customer Cancelled",
            "cancelled_by": "customer",
            "cancellation_date": "2024-03-01",
            "cancellation_fee": "$0.00",
            "booking_status": "CANCELLED",
            "is_first_recurring": "false",
            "is_new_customer": "false",
            "zip": "3000",
        }
        data.update(overrides)
        return data

    def test_sets_booking_id(self):
        b = Booking.from_webhook(_base_webhook())
        b.update_from_cancellation(self._cancel_data())
        assert b.booking_id == 12345

    def test_sets_booking_status(self):
        b = Booking.from_webhook(_base_webhook())
        b.update_from_cancellation(self._cancel_data(booking_status="CANCELLED"))
        assert b.booking_status == "CANCELLED"

    def test_sets_cancellation_type(self):
        b = Booking.from_webhook(_base_webhook())
        b.update_from_cancellation(self._cancel_data(cancellation_type="Late Cancel"))
        assert b.cancellation_type == "Late Cancel"

    def test_was_new_customer_set_when_true(self):
        b = Booking.from_webhook(_base_webhook())
        b.update_from_cancellation(self._cancel_data(is_new_customer="true"))
        assert b.was_new_customer is True


# ---------------------------------------------------------------------------
# _parse_dollar_field
# ---------------------------------------------------------------------------


class TestParseDollarField:
    def test_dollar_string(self):
        assert _parse_dollar_field("$50.00") == 5000

    def test_none_returns_none(self):
        assert _parse_dollar_field(None) is None

    def test_empty_string_returns_none(self):
        assert _parse_dollar_field("") is None

    def test_integer_input(self):
        assert _parse_dollar_field(100) == 100

    def test_invalid_string_returns_none(self):
        # "abc" can't be converted — should log error and return None
        result = _parse_dollar_field("abc.xyz")
        assert result is None


# ---------------------------------------------------------------------------
# process_custom_fields
# ---------------------------------------------------------------------------


class TestProcessCustomFields:
    def test_maps_custom_source_field(self):
        b = Booking()
        with patch(
            "app.models.booking.get_settings",
            return_value=type(
                "S",
                (),
                {
                    "CUSTOM_SOURCE": "cf_source",
                    "CUSTOM_BOOKED_BY": None,
                    "CUSTOM_EMAIL_INVOICE": None,
                    "CUSTOM_INVOICE_NAME": None,
                    "CUSTOM_WHO_PAYS": None,
                    "CUSTOM_INVOICE_EMAIL_ADDRESS": None,
                    "CUSTOM_LAST_SERVICE": None,
                    "CUSTOM_INVOICE_REFERENCE": None,
                    "CUSTOM_INVOICE_REFERENCE_EXTRA": None,
                    "CUSTOM_NDIS_NUMBER": None,
                    "CUSTOM_FLEXIBLE": None,
                    "CUSTOM_HOURLY_NOTES": None,
                },
            )(),
        ):
            process_custom_fields(b, {"cf_source": "Google"})
        assert b.lead_source == "Google"

    def test_missing_custom_field_key_is_ignored(self):
        b = Booking()
        with patch(
            "app.models.booking.get_settings",
            return_value=type(
                "S",
                (),
                {
                    "CUSTOM_SOURCE": "cf_source",
                    "CUSTOM_BOOKED_BY": None,
                    "CUSTOM_EMAIL_INVOICE": None,
                    "CUSTOM_INVOICE_NAME": None,
                    "CUSTOM_WHO_PAYS": None,
                    "CUSTOM_INVOICE_EMAIL_ADDRESS": None,
                    "CUSTOM_LAST_SERVICE": None,
                    "CUSTOM_INVOICE_REFERENCE": None,
                    "CUSTOM_INVOICE_REFERENCE_EXTRA": None,
                    "CUSTOM_NDIS_NUMBER": None,
                    "CUSTOM_FLEXIBLE": None,
                    "CUSTOM_HOURLY_NOTES": None,
                },
            )(),
        ):
            process_custom_fields(b, {})  # key absent
        assert b.lead_source is None
