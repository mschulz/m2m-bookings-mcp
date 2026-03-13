"""
Tests for app/database/missing_locations.py.

Covers:
* ``find_missing_locations()`` — DB query + deduplication logic
* ``main()``                   — orchestration: email gating, thread dispatch

The database and email service are fully mocked so no live connections are
required.  ``pytest-asyncio`` is used for async test support.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_booking(postcode: str | None) -> MagicMock:
    """Return a mock Booking instance with the given postcode."""
    b = MagicMock()
    b.postcode = postcode
    return b


# ---------------------------------------------------------------------------
# find_missing_locations()
# ---------------------------------------------------------------------------


class TestFindMissingLocations:
    """Unit tests for the DB query and result processing."""

    @pytest.mark.asyncio
    async def test_no_missing_bookings_returns_empty_summary(self):
        """When no bookings are missing locations, totals are zero."""
        with (
            patch(
                "app.database.missing_locations.async_session",
            ) as mock_session_factory,
            patch(
                "app.database.missing_locations.booking_dao.get_bookings_missing_locations",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            # async_session() used as async context manager
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = MagicMock()
            mock_session_factory.return_value = mock_ctx

            from app.database.missing_locations import find_missing_locations

            result = await find_missing_locations()

        assert result["total"] == 0
        assert result["postcodes"] == []

    @pytest.mark.asyncio
    async def test_deduplicates_postcodes_and_sorts(self):
        """Duplicate postcodes are collapsed and the result list is sorted."""
        bookings = [
            _make_booking("3000"),
            _make_booking("2000"),
            _make_booking("3000"),  # duplicate
            _make_booking("4000"),
        ]

        with (
            patch("app.database.missing_locations.async_session") as mock_session_factory,
            patch(
                "app.database.missing_locations.booking_dao.get_bookings_missing_locations",
                new_callable=AsyncMock,
                return_value=bookings,
            ),
        ):
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = MagicMock()
            mock_session_factory.return_value = mock_ctx

            from app.database.missing_locations import find_missing_locations

            result = await find_missing_locations()

        assert result["total"] == 4
        assert result["postcodes"] == ["2000", "3000", "4000"]

    @pytest.mark.asyncio
    async def test_null_postcodes_excluded_from_list(self):
        """Bookings with NULL postcode are counted but excluded from the postcode list."""
        bookings = [
            _make_booking(None),
            _make_booking("3000"),
            _make_booking(None),
        ]

        with (
            patch("app.database.missing_locations.async_session") as mock_session_factory,
            patch(
                "app.database.missing_locations.booking_dao.get_bookings_missing_locations",
                new_callable=AsyncMock,
                return_value=bookings,
            ),
        ):
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = MagicMock()
            mock_session_factory.return_value = mock_ctx

            from app.database.missing_locations import find_missing_locations

            result = await find_missing_locations()

        assert result["total"] == 3
        assert result["postcodes"] == ["3000"]

    @pytest.mark.asyncio
    async def test_all_null_postcodes_returns_empty_postcode_list(self):
        """When every affected booking has a NULL postcode the list is empty."""
        bookings = [_make_booking(None), _make_booking(None)]

        with (
            patch("app.database.missing_locations.async_session") as mock_session_factory,
            patch(
                "app.database.missing_locations.booking_dao.get_bookings_missing_locations",
                new_callable=AsyncMock,
                return_value=bookings,
            ),
        ):
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = MagicMock()
            mock_session_factory.return_value = mock_ctx

            from app.database.missing_locations import find_missing_locations

            result = await find_missing_locations()

        assert result["total"] == 2
        assert result["postcodes"] == []


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


class TestMain:
    """Integration-style tests for the main() orchestration function."""

    @pytest.mark.asyncio
    async def test_no_missing_locations_skips_email(self):
        """main() must NOT send an email when there are no missing bookings."""
        with (
            patch("app.database.missing_locations.setup_logging"),
            patch(
                "app.database.missing_locations.find_missing_locations",
                new_callable=AsyncMock,
                return_value={"total": 0, "postcodes": []},
            ),
            patch(
                "app.database.missing_locations.asyncio.to_thread",
                new_callable=AsyncMock,
            ) as mock_to_thread,
        ):
            from app.database.missing_locations import main

            await main()

        mock_to_thread.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_locations_sends_email_with_correct_args(self):
        """main() dispatches send_missing_location_email with the right parameters."""
        postcodes = ["2000", "3000"]
        with (
            patch("app.database.missing_locations.setup_logging"),
            patch(
                "app.database.missing_locations.find_missing_locations",
                new_callable=AsyncMock,
                return_value={"total": 5, "postcodes": postcodes},
            ),
            patch(
                "app.database.missing_locations.asyncio.to_thread",
                new_callable=AsyncMock,
            ) as mock_to_thread,
            patch(
                "app.database.missing_locations.get_settings",
                return_value=MagicMock(
                    APP_NAME="TestApp",
                    SUPPORT_EMAIL="support@example.com",
                ),
            ),
        ):
            from app.database.missing_locations import main

            await main()

        # asyncio.to_thread(fn, *args) — assert correct positional args
        mock_to_thread.assert_called_once()
        call_args = mock_to_thread.call_args[0]  # positional args tuple

        _fn, toaddr, msg, total, n_postcodes = call_args
        assert toaddr == "support@example.com"
        assert msg == str(postcodes)
        assert total == 5
        assert n_postcodes == 2

    @pytest.mark.asyncio
    async def test_email_sent_when_all_postcodes_are_null(self):
        """An email is still sent even if every affected booking has a NULL postcode."""
        with (
            patch("app.database.missing_locations.setup_logging"),
            patch(
                "app.database.missing_locations.find_missing_locations",
                new_callable=AsyncMock,
                return_value={"total": 3, "postcodes": []},
            ),
            patch(
                "app.database.missing_locations.asyncio.to_thread",
                new_callable=AsyncMock,
            ) as mock_to_thread,
            patch(
                "app.database.missing_locations.get_settings",
                return_value=MagicMock(
                    APP_NAME="TestApp",
                    SUPPORT_EMAIL="support@example.com",
                ),
            ),
        ):
            from app.database.missing_locations import main

            await main()

        mock_to_thread.assert_called_once()
        call_args = mock_to_thread.call_args[0]
        _fn, _toaddr, _msg, total, n_postcodes = call_args
        assert total == 3
        assert n_postcodes == 0
