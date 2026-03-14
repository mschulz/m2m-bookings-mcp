"""
Tests for app/commands/completed/booking.py and complete_bookings_today.py.

Covers:
* Booking.get_all_in_tz  — proxy HTTP call, response parsing
* Booking.complete        — testing-mode short-circuit; success/failure mapping
* main()                  — orchestration: tz_count from booking_ids length,
                            completion gating, email args
"""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_httpx_client(method: str, response_data: dict) -> MagicMock:
    """Return a mock async context manager whose inner client returns response_data."""
    mock_response = MagicMock()
    mock_response.json.return_value = response_data
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    setattr(mock_client, method, AsyncMock(return_value=mock_response))

    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_ctx.__aexit__ = AsyncMock(return_value=None)
    return mock_ctx


# ---------------------------------------------------------------------------
# Booking.get_all_in_tz
# ---------------------------------------------------------------------------


class TestBookingGetAllInTz:
    async def test_returns_proxy_response(self):
        """get_all_in_tz parses and returns the JSON from the proxy."""
        expected = {"count": 10, "booking_ids": [1, 2, 3]}
        mock_ctx = _make_httpx_client("get", expected)

        with patch("app.commands.completed.booking.httpx.AsyncClient", return_value=mock_ctx):
            from app.commands.completed.booking import Booking

            b = Booking()
            result = await b.get_all_in_tz("2026-03-13", "AEST")

        assert result == expected

    async def test_builds_correct_url_and_params(self):
        """get_all_in_tz calls the proxy with the right URL and tz_name param."""
        mock_ctx = _make_httpx_client("get", {"count": 0, "booking_ids": []})

        with patch("app.commands.completed.booking.httpx.AsyncClient", return_value=mock_ctx):
            from app.commands.completed.booking import Booking

            b = Booking()
            await b.get_all_in_tz("2026-03-13", "AWST")

        call_kwargs = mock_ctx.__aenter__.return_value.get.call_args
        assert "tocomplete/2026-03-13" in call_kwargs[0][0]
        assert call_kwargs[1]["params"] == {"tz_name": "AWST"}

    async def test_empty_booking_ids_returned(self):
        """get_all_in_tz handles an empty booking_ids list correctly."""
        mock_ctx = _make_httpx_client("get", {"count": 0, "booking_ids": []})

        with patch("app.commands.completed.booking.httpx.AsyncClient", return_value=mock_ctx):
            from app.commands.completed.booking import Booking

            b = Booking()
            result = await b.get_all_in_tz("2026-03-13", "ACST")

        assert result["booking_ids"] == []
        assert result["count"] == 0


# ---------------------------------------------------------------------------
# Booking.complete
# ---------------------------------------------------------------------------


class TestBookingComplete:
    async def test_returns_zero_in_testing_mode(self):
        """complete() short-circuits to 0 in testing mode without an HTTP call."""
        with patch("app.commands.completed.booking.httpx.AsyncClient") as mock_client_cls:
            from app.commands.completed.booking import Booking

            b = Booking()
            result = await b.complete(12345)

        assert result == 0
        mock_client_cls.assert_not_called()

    async def test_returns_one_on_proxy_success(self):
        """complete() returns 1 when the proxy responds with success=True."""
        mock_ctx = _make_httpx_client("post", {"success": True})

        with (
            patch(
                "app.commands.completed.booking.get_settings",
                return_value=MagicMock(
                    testing=False,
                    PROXY_URL="https://proxy.example.com",
                    PROXY_API_KEY="key",
                ),
            ),
            patch("app.commands.completed.booking.httpx.AsyncClient", return_value=mock_ctx),
        ):
            from app.commands.completed.booking import Booking

            b = Booking()
            result = await b.complete(99)

        assert result == 1

    async def test_returns_zero_on_proxy_failure(self):
        """complete() returns 0 when the proxy responds with success=False."""
        mock_ctx = _make_httpx_client("post", {"success": False})

        with (
            patch(
                "app.commands.completed.booking.get_settings",
                return_value=MagicMock(
                    testing=False,
                    PROXY_URL="https://proxy.example.com",
                    PROXY_API_KEY="key",
                ),
            ),
            patch("app.commands.completed.booking.httpx.AsyncClient", return_value=mock_ctx),
        ):
            from app.commands.completed.booking import Booking

            b = Booking()
            result = await b.complete(99)

        assert result == 0

    async def test_returns_zero_when_success_key_missing(self):
        """complete() returns 0 if the proxy response lacks a success key."""
        mock_ctx = _make_httpx_client("post", {})

        with (
            patch(
                "app.commands.completed.booking.get_settings",
                return_value=MagicMock(
                    testing=False,
                    PROXY_URL="https://proxy.example.com",
                    PROXY_API_KEY="key",
                ),
            ),
            patch("app.commands.completed.booking.httpx.AsyncClient", return_value=mock_ctx),
        ):
            from app.commands.completed.booking import Booking

            b = Booking()
            result = await b.complete(99)

        assert result == 0


# ---------------------------------------------------------------------------
# complete_bookings_today.main()
# ---------------------------------------------------------------------------


class TestCompleteBookingsToday:
    """Tests for the main() orchestration function."""

    def _make_booking_mock(self, booking_list: dict, complete_return: int = 0) -> MagicMock:
        """Return a mock Booking instance."""
        mock_b = MagicMock()
        mock_b.get_all_in_tz = AsyncMock(return_value=booking_list)
        mock_b.complete = AsyncMock(return_value=complete_return)
        return mock_b

    async def test_no_bookings_sends_email_with_zeros(self):
        """When booking_ids is empty the email reports 0 completed out of 0."""
        mock_b = self._make_booking_mock({"count": 50, "booking_ids": []})

        with (
            patch("sys.argv", ["cmd", "AEST"]),
            patch("app.commands.completed.complete_bookings_today.setup_logging"),
            patch(
                "app.commands.completed.complete_bookings_today.Booking", return_value=mock_b
            ),
            patch(
                "app.commands.completed.complete_bookings_today.get_settings",
                return_value=MagicMock(
                    APP_NAME="TestApp",
                    TZ_LOCALTIME="Australia/Sydney",
                    SUPPORT_EMAIL="support@example.com",
                ),
            ),
            patch(
                "app.commands.completed.complete_bookings_today.asyncio.to_thread",
                new_callable=AsyncMock,
            ) as mock_to_thread,
        ):
            from app.commands.completed.complete_bookings_today import main

            await main()

        mock_b.complete.assert_not_called()
        call_args = mock_to_thread.call_args[0]
        _fn, _toaddr, completed_count, tz_count, _tz = call_args
        assert completed_count == 0
        assert tz_count == 0

    async def test_tz_count_uses_booking_ids_length_not_count_field(self):
        """tz_count must equal len(booking_ids), not the proxy's count field."""
        # proxy returns count=204 but only 3 booking_ids for this timezone
        mock_b = self._make_booking_mock(
            {"count": 204, "booking_ids": [1, 2, 3]}, complete_return=1
        )

        with (
            patch("sys.argv", ["cmd", "AEST"]),
            patch("app.commands.completed.complete_bookings_today.setup_logging"),
            patch(
                "app.commands.completed.complete_bookings_today.Booking", return_value=mock_b
            ),
            patch(
                "app.commands.completed.complete_bookings_today.get_settings",
                return_value=MagicMock(
                    APP_NAME="TestApp",
                    TZ_LOCALTIME="Australia/Sydney",
                    SUPPORT_EMAIL="support@example.com",
                ),
            ),
            patch(
                "app.commands.completed.complete_bookings_today.asyncio.to_thread",
                new_callable=AsyncMock,
            ) as mock_to_thread,
        ):
            from app.commands.completed.complete_bookings_today import main

            await main()

        call_args = mock_to_thread.call_args[0]
        _fn, _toaddr, completed_count, tz_count, _tz = call_args
        assert tz_count == 3   # len(booking_ids), NOT 204
        assert completed_count == 3

    async def test_all_bookings_completed_successfully(self):
        """completed_count equals tz_count when all complete() calls return 1."""
        booking_ids = [10, 20, 30, 40]
        mock_b = self._make_booking_mock(
            {"count": 100, "booking_ids": booking_ids}, complete_return=1
        )

        with (
            patch("sys.argv", ["cmd", "AEST"]),
            patch("app.commands.completed.complete_bookings_today.setup_logging"),
            patch(
                "app.commands.completed.complete_bookings_today.Booking", return_value=mock_b
            ),
            patch(
                "app.commands.completed.complete_bookings_today.get_settings",
                return_value=MagicMock(
                    APP_NAME="TestApp",
                    TZ_LOCALTIME="Australia/Sydney",
                    SUPPORT_EMAIL="support@example.com",
                ),
            ),
            patch(
                "app.commands.completed.complete_bookings_today.asyncio.to_thread",
                new_callable=AsyncMock,
            ) as mock_to_thread,
        ):
            from app.commands.completed.complete_bookings_today import main

            await main()

        assert mock_b.complete.call_count == 4
        call_args = mock_to_thread.call_args[0]
        _fn, _toaddr, completed_count, tz_count, _tz = call_args
        assert completed_count == 4
        assert tz_count == 4

    async def test_partial_completion_reported_correctly(self):
        """completed_count reflects partial success when some complete() calls return 0."""
        booking_ids = [1, 2, 3]
        mock_b = MagicMock()
        mock_b.get_all_in_tz = AsyncMock(return_value={"count": 50, "booking_ids": booking_ids})
        # first two succeed, third fails
        mock_b.complete = AsyncMock(side_effect=[1, 1, 0])

        with (
            patch("sys.argv", ["cmd", "ACST"]),
            patch("app.commands.completed.complete_bookings_today.setup_logging"),
            patch(
                "app.commands.completed.complete_bookings_today.Booking", return_value=mock_b
            ),
            patch(
                "app.commands.completed.complete_bookings_today.get_settings",
                return_value=MagicMock(
                    APP_NAME="TestApp",
                    TZ_LOCALTIME="Australia/Sydney",
                    SUPPORT_EMAIL="support@example.com",
                ),
            ),
            patch(
                "app.commands.completed.complete_bookings_today.asyncio.to_thread",
                new_callable=AsyncMock,
            ) as mock_to_thread,
        ):
            from app.commands.completed.complete_bookings_today import main

            await main()

        call_args = mock_to_thread.call_args[0]
        _fn, _toaddr, completed_count, tz_count, tz_name = call_args
        assert completed_count == 2
        assert tz_count == 3
        assert tz_name == "ACST"

    async def test_email_sent_to_support_address(self):
        """main() sends the completion email to SUPPORT_EMAIL."""
        mock_b = self._make_booking_mock({"count": 1, "booking_ids": [42]}, complete_return=1)

        with (
            patch("sys.argv", ["cmd", "AWST"]),
            patch("app.commands.completed.complete_bookings_today.setup_logging"),
            patch(
                "app.commands.completed.complete_bookings_today.Booking", return_value=mock_b
            ),
            patch(
                "app.commands.completed.complete_bookings_today.get_settings",
                return_value=MagicMock(
                    APP_NAME="TestApp",
                    TZ_LOCALTIME="Australia/Sydney",
                    SUPPORT_EMAIL="support@example.com",
                ),
            ),
            patch(
                "app.commands.completed.complete_bookings_today.asyncio.to_thread",
                new_callable=AsyncMock,
            ) as mock_to_thread,
        ):
            from app.commands.completed.complete_bookings_today import main

            await main()

        call_args = mock_to_thread.call_args[0]
        _fn, toaddr = call_args[0], call_args[1]
        assert toaddr == "support@example.com"

    async def test_complete_called_for_each_booking_id(self):
        """main() calls complete() once for every booking_id returned."""
        booking_ids = [101, 102, 103, 104, 105]
        mock_b = self._make_booking_mock(
            {"count": 200, "booking_ids": booking_ids}, complete_return=1
        )

        with (
            patch("sys.argv", ["cmd", "AEST"]),
            patch("app.commands.completed.complete_bookings_today.setup_logging"),
            patch(
                "app.commands.completed.complete_bookings_today.Booking", return_value=mock_b
            ),
            patch(
                "app.commands.completed.complete_bookings_today.get_settings",
                return_value=MagicMock(
                    APP_NAME="TestApp",
                    TZ_LOCALTIME="Australia/Sydney",
                    SUPPORT_EMAIL="support@example.com",
                ),
            ),
            patch(
                "app.commands.completed.complete_bookings_today.asyncio.to_thread",
                new_callable=AsyncMock,
            ),
        ):
            from app.commands.completed.complete_bookings_today import main

            await main()

        called_ids = {call[0][0] for call in mock_b.complete.call_args_list}
        assert called_ids == set(booking_ids)
