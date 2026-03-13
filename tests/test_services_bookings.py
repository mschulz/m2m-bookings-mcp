"""Tests for app/services/bookings.py — reject_booking, update_table, and search helpers."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy import exc as sa_exc

from app.services.bookings import (
    get_booking_by_email_service_date,
    reject_booking,
    search_bookings,
    search_completed_bookings_by_service_date,
    update_table,
)


# ---------------------------------------------------------------------------
# reject_booking
# ---------------------------------------------------------------------------


class TestRejectBooking:
    def test_internal_meeting_is_rejected(self):
        assert reject_booking({"service_category": "Internal Meeting"}) is True

    def test_tbc_postcode_rejected(self):
        assert reject_booking({"zip": "tbc"}) is True

    def test_tba_postcode_rejected(self):
        assert reject_booking({"zip": "TBA"}) is True

    def test_valid_numeric_postcode_not_rejected(self):
        assert reject_booking({"zip": "3000"}) is False

    def test_none_postcode_not_rejected(self):
        assert reject_booking({}) is False

    def test_house_clean_not_rejected(self):
        assert reject_booking({"service_category": "House Clean", "zip": "3000"}) is False

    def test_bond_clean_not_rejected(self):
        assert reject_booking({"service_category": "Bond Clean", "zip": "4000"}) is False


# ---------------------------------------------------------------------------
# update_table
# ---------------------------------------------------------------------------


class TestUpdateTable:
    async def test_rejected_booking_returns_ok(self):
        db = AsyncMock()
        result = await update_table({"service_category": "Internal Meeting"}, db)
        assert result == "OK"

    async def test_status_set_in_data_before_dao(self):
        db = AsyncMock()
        data = {
            "id": "12345",
            "is_first_recurring": "false",
            "is_new_customer": "false",
            "zip": "3000",
            "customer": {"id": "1", "zip": "3000"},
        }
        with (
            patch(
                "app.services.bookings.booking_dao.create_update_booking",
                new_callable=AsyncMock,
            ) as mock_booking,
            patch(
                "app.services.bookings.customer_dao.create_or_update_customer",
                new_callable=AsyncMock,
            ),
        ):
            await update_table(data, db, status="COMPLETED")

        called_data = mock_booking.call_args[0][1]
        assert called_data["booking_status"] == "COMPLETED"

    async def test_customer_updated_when_not_restored(self):
        db = AsyncMock()
        data = {
            "id": "12345",
            "is_first_recurring": "false",
            "is_new_customer": "false",
            "zip": "3000",
            "customer": {"id": "1", "zip": "3000"},
        }
        with (
            patch(
                "app.services.bookings.booking_dao.create_update_booking",
                new_callable=AsyncMock,
            ),
            patch(
                "app.services.bookings.customer_dao.create_or_update_customer",
                new_callable=AsyncMock,
            ) as mock_customer,
        ):
            await update_table(data, db, is_restored=False)

        mock_customer.assert_called_once()

    async def test_customer_skipped_when_restored(self):
        db = AsyncMock()
        data = {
            "id": "12345",
            "is_first_recurring": "false",
            "is_new_customer": "false",
            "zip": "3000",
            "customer": {"id": "1", "zip": "3000"},
        }
        with (
            patch(
                "app.services.bookings.booking_dao.create_update_booking",
                new_callable=AsyncMock,
            ),
            patch(
                "app.services.bookings.customer_dao.create_or_update_customer",
                new_callable=AsyncMock,
            ) as mock_customer,
        ):
            await update_table(data, db, is_restored=True)

        mock_customer.assert_not_called()

    async def test_returns_data_dict_for_klaviyo(self):
        db = AsyncMock()
        data = {
            "id": "12345",
            "is_first_recurring": "false",
            "is_new_customer": "false",
            "zip": "3000",
            "customer": {"id": "1", "zip": "3000"},
        }
        with (
            patch(
                "app.services.bookings.booking_dao.create_update_booking",
                new_callable=AsyncMock,
            ),
            patch(
                "app.services.bookings.customer_dao.create_or_update_customer",
                new_callable=AsyncMock,
            ),
        ):
            result = await update_table(data, db)

        assert result is data


# ---------------------------------------------------------------------------
# search_bookings
# ---------------------------------------------------------------------------


class TestSearchBookings:
    async def test_returns_formatted_list(self):
        booking = MagicMock()
        booking.service_category = "House Clean"
        booking.name = "Jane Smith"
        booking.location = "Melbourne"
        booking.booking_id = 12345

        db = AsyncMock()
        with patch(
            "app.services.bookings.booking_dao.get_by_date_range",
            new_callable=AsyncMock,
            return_value=[booking],
        ):
            results = await search_bookings(db, "House Clean", "2024-01-01", "2024-01-31", "NOT_COMPLETE")

        assert len(results) == 1
        assert results[0]["booking_id"] == 12345
        assert results[0]["name"] == "Jane Smith"
        assert results[0]["location"] == "Melbourne"
        assert results[0]["category"] == "House Clean"

    async def test_operational_error_raises_503(self):
        db = AsyncMock()
        with patch(
            "app.services.bookings.booking_dao.get_by_date_range",
            new_callable=AsyncMock,
            side_effect=sa_exc.OperationalError("stmt", {}, Exception("conn")),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await search_bookings(db, "House Clean", "2024-01-01", "2024-01-31", "NOT_COMPLETE")

        assert exc_info.value.status_code == 503

    async def test_empty_result_returns_empty_list(self):
        db = AsyncMock()
        with patch(
            "app.services.bookings.booking_dao.get_by_date_range",
            new_callable=AsyncMock,
            return_value=[],
        ):
            results = await search_bookings(db, "House Clean", "2024-01-01", "2024-01-31", "NOT_COMPLETE")

        assert results == []


# ---------------------------------------------------------------------------
# search_completed_bookings_by_service_date
# ---------------------------------------------------------------------------


class TestSearchCompletedBookingsByServiceDate:
    async def test_returns_formatted_booking_dicts(self):
        booking = MagicMock()
        booking.booking_id = 99
        booking.service_date = date(2024, 2, 15)
        booking.name = "Jane Smith"
        booking.email = "jane@example.com"
        booking.postcode = "3000"
        booking.location = "Melbourne"
        booking.teams_assigned = "Alice"
        booking.created_by = "admin"
        booking.service_category = "House Clean"
        booking.service = "Standard Clean"
        booking.frequency = "Weekly"

        db = AsyncMock()
        with patch(
            "app.services.bookings.booking_dao.completed_bookings_by_service_date",
            new_callable=AsyncMock,
            return_value=[booking],
        ):
            results = await search_completed_bookings_by_service_date(
                db, "2024-02-01", "2024-02-28"
            )

        assert len(results) == 1
        assert results[0]["booking_id"] == 99
        assert results[0]["email"] == "jane@example.com"

    async def test_operational_error_raises_503(self):
        db = AsyncMock()
        with patch(
            "app.services.bookings.booking_dao.completed_bookings_by_service_date",
            new_callable=AsyncMock,
            side_effect=sa_exc.OperationalError("stmt", {}, Exception("conn")),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await search_completed_bookings_by_service_date(db, "2024-02-01", "2024-02-28")

        assert exc_info.value.status_code == 503


# ---------------------------------------------------------------------------
# get_booking_by_email_service_date
# ---------------------------------------------------------------------------


class TestGetBookingByEmailServiceDate:
    async def test_returns_data_and_found_status_when_booking_exists(self):
        booking = MagicMock()
        booking.booking_id = 12345
        booking.service_date = date(2024, 2, 15)
        booking.first_name = "Jane"
        booking.last_name = "Smith"
        booking.email = "jane@example.com"
        booking.postcode = "3000"
        booking.location = "Melbourne"
        booking.teams_assigned = "Alice"
        booking.service_category = "House Clean"
        booking.service = "Standard"
        booking.frequency = "Weekly"

        db = AsyncMock()
        with patch(
            "app.services.bookings.booking_dao.get_by_booking_email_service_date_range",
            new_callable=AsyncMock,
            return_value=booking,
        ):
            result = await get_booking_by_email_service_date(db, "jane@example.com", "2024-02-15")

        assert result["status"] == "found"
        assert result["data"]["booking_id"] == 12345

    async def test_returns_not_found_when_no_booking(self):
        db = AsyncMock()
        with patch(
            "app.services.bookings.booking_dao.get_by_booking_email_service_date_range",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await get_booking_by_email_service_date(db, "nobody@example.com", "2024-02-15")

        assert result["status"] == "not found"
        assert result["data"] == {}
