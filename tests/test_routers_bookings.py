"""Tests for app/routers/bookings.py — all booking webhook and query endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _post(client, path, data, headers):
    return client.post(path, json=data, headers=headers)


def _patch_update_table(return_value):
    return patch(
        "app.routers.bookings.update_table",
        new_callable=AsyncMock,
        return_value=return_value,
    )


def _patch_klaviyo():
    return patch("app.routers.bookings.process_with_klaviyo", new_callable=AsyncMock)


# ---------------------------------------------------------------------------
# POST /booking/new
# ---------------------------------------------------------------------------


class TestPostBookingNew:
    def test_returns_ok(self, client, auth_headers, booking_data):
        with _patch_update_table(booking_data), _patch_klaviyo():
            response = _post(client, "/booking/new", booking_data, auth_headers)
        assert response.status_code == 200
        assert response.json() == "OK"

    def test_internal_meeting_still_returns_ok(self, client, auth_headers):
        data = {"service_category": "Internal Meeting", "zip": "tbc"}
        with _patch_update_table("OK"), _patch_klaviyo():
            response = _post(client, "/booking/new", data, auth_headers)
        assert response.status_code == 200

    def test_update_table_called_with_not_complete_status(self, client, auth_headers, booking_data):
        with _patch_update_table(booking_data) as mock_update, _patch_klaviyo():
            _post(client, "/booking/new", booking_data, auth_headers)
        _, kwargs = mock_update.call_args
        assert kwargs.get("status") == "NOT_COMPLETE" or mock_update.call_args[1].get("status") == "NOT_COMPLETE"


# ---------------------------------------------------------------------------
# POST /booking/restored
# ---------------------------------------------------------------------------


class TestPostBookingRestored:
    def test_returns_ok(self, client, auth_headers, booking_data):
        with _patch_update_table(booking_data), _patch_klaviyo():
            response = _post(client, "/booking/restored", booking_data, auth_headers)
        assert response.status_code == 200
        assert response.json() == "OK"


# ---------------------------------------------------------------------------
# POST /booking/completed
# ---------------------------------------------------------------------------


class TestPostBookingCompleted:
    def test_returns_ok(self, client, auth_headers, booking_data):
        with _patch_update_table(booking_data), _patch_klaviyo():
            response = _post(client, "/booking/completed", booking_data, auth_headers)
        assert response.status_code == 200

    def test_update_table_called_with_completed_status(self, client, auth_headers, booking_data):
        with _patch_update_table(booking_data) as mock_update, _patch_klaviyo():
            _post(client, "/booking/completed", booking_data, auth_headers)
        called_kwargs = mock_update.call_args[1]
        assert called_kwargs.get("status") == "COMPLETED"


# ---------------------------------------------------------------------------
# POST /booking/cancellation
# ---------------------------------------------------------------------------


class TestPostBookingCancellation:
    def test_returns_ok(self, client, auth_headers, booking_data):
        with _patch_update_table(booking_data), _patch_klaviyo():
            response = _post(client, "/booking/cancellation", booking_data, auth_headers)
        assert response.status_code == 200

    def test_tbc_postcode_rejected_returns_ok(self, client, auth_headers):
        data = {"zip": "tbc", "service_category": "House Clean"}
        with _patch_update_table("OK"), _patch_klaviyo():
            response = _post(client, "/booking/cancellation", data, auth_headers)
        assert response.status_code == 200

    def test_cancellation_datetime_injected(self, client, auth_headers, booking_data):
        with _patch_update_table(booking_data) as mock_update, _patch_klaviyo():
            _post(client, "/booking/cancellation", booking_data, auth_headers)
        # update_table should have been called with _cancellation_datetime in data
        called_data = mock_update.call_args[0][0]
        assert "_cancellation_datetime" in called_data


# ---------------------------------------------------------------------------
# POST /booking/updated
# ---------------------------------------------------------------------------


class TestPostBookingUpdated:
    def test_returns_ok(self, client, auth_headers, booking_data):
        with _patch_update_table(booking_data), _patch_klaviyo():
            response = _post(client, "/booking/updated", booking_data, auth_headers)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# POST /booking/team_changed
# ---------------------------------------------------------------------------


class TestPostBookingTeamChanged:
    def test_returns_ok(self, client, auth_headers, booking_data):
        with _patch_update_table(booking_data), _patch_klaviyo():
            response = _post(client, "/booking/team_changed", booking_data, auth_headers)
        assert response.status_code == 200

    def test_is_restored_flag_set(self, client, auth_headers, booking_data):
        """team_changed must pass is_restored=True to skip customer upsert."""
        with _patch_update_table(booking_data) as mock_update, _patch_klaviyo():
            _post(client, "/booking/team_changed", booking_data, auth_headers)
        called_kwargs = mock_update.call_args[1]
        assert called_kwargs.get("is_restored") is True


# ---------------------------------------------------------------------------
# GET /booking (search)
# ---------------------------------------------------------------------------


class TestGetBookingSearch:
    def test_returns_list(self, client, auth_headers):
        with patch(
            "app.routers.bookings.search_bookings",
            new_callable=AsyncMock,
            return_value=[{"booking_id": 1, "name": "Jane", "location": "Melbourne", "category": "House Clean"}],
        ):
            response = client.get(
                "/booking",
                params={"category": "House Clean", "date": "2024-02-15", "booking_status": "NOT_COMPLETE"},
                headers=auth_headers,
            )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["booking_id"] == 1

    def test_missing_params_returns_422(self, client, auth_headers):
        response = client.get("/booking", headers=auth_headers)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /booking/{booking_id}
# ---------------------------------------------------------------------------


class TestGetBookingDetails:
    def test_returns_booking_when_found(self, client, auth_headers, mock_db_session):
        from app.models.booking import Booking

        booking = MagicMock(spec=Booking)
        booking.model_dump.return_value = {"booking_id": 12345, "name": "Jane"}
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = booking
        mock_db_session.execute.return_value = mock_result

        response = client.get("/booking/12345", headers=auth_headers)
        assert response.status_code == 200

    def test_returns_404_when_not_found(self, client, auth_headers, mock_db_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        response = client.get("/booking/99999", headers=auth_headers)
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /booking/was_new_customer/{booking_id}
# ---------------------------------------------------------------------------


class TestGetWasNewCustomer:
    def test_returns_was_new_customer_true(self, client, auth_headers, mock_db_session):
        from app.models.booking import Booking

        booking = MagicMock(spec=Booking)
        booking.was_new_customer = True
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = booking
        mock_db_session.execute.return_value = mock_result

        response = client.get("/booking/was_new_customer/12345", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["was_new_customer"] is True

    def test_returns_false_when_booking_not_found(self, client, auth_headers, mock_db_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result

        response = client.get("/booking/was_new_customer/99999", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["was_new_customer"] is False


# ---------------------------------------------------------------------------
# GET /booking/search/completed
# ---------------------------------------------------------------------------


class TestGetSearchCompleted:
    def test_returns_list(self, client, auth_headers):
        with patch(
            "app.routers.bookings.search_completed_bookings_by_service_date",
            new_callable=AsyncMock,
            return_value=[{"booking_id": 1}],
        ):
            response = client.get(
                "/booking/search/completed",
                params={"from": "2024-02-01", "to": "2024-02-28"},
                headers=auth_headers,
            )
        assert response.status_code == 200
        assert response.json()[0]["booking_id"] == 1

    def test_missing_params_returns_422(self, client, auth_headers):
        response = client.get("/booking/search/completed", headers=auth_headers)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /booking/service_date/search
# ---------------------------------------------------------------------------


class TestGetServiceDateSearch:
    def test_returns_result(self, client, auth_headers):
        with patch(
            "app.routers.bookings.get_booking_by_email_service_date",
            new_callable=AsyncMock,
            return_value={"data": {"booking_id": 1}, "status": "found"},
        ):
            response = client.get(
                "/booking/service_date/search",
                params={"service_date": "2024-02-15", "email": "jane@example.com"},
                headers=auth_headers,
            )
        assert response.status_code == 200
        assert response.json()["status"] == "found"

    def test_missing_params_returns_422(self, client, auth_headers):
        response = client.get("/booking/service_date/search", headers=auth_headers)
        assert response.status_code == 422
