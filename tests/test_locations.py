"""Tests for app/utils/locations.py — postcode-to-location lookup with TTL cache."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import app.utils.locations as loc_module
from app.utils.locations import get_location


@pytest.fixture(autouse=True)
def clear_location_cache():
    """Ensure each test starts with a fresh cache."""
    loc_module.location_cache.clear()
    yield
    loc_module.location_cache.clear()


class TestGetLocation:
    async def test_none_postcode_returns_none(self):
        result = await get_location(None)
        assert result is None

    async def test_integer_postcode_converted_to_string(self):
        with patch(
            "app.utils.locations._fetch_location",
            new_callable=AsyncMock,
            return_value="Melbourne",
        ):
            result = await get_location(3000)
        assert result == "Melbourne"

    async def test_cache_hit_skips_fetch(self):
        loc_module.location_cache["3000"] = "Melbourne"
        with patch(
            "app.utils.locations._fetch_location",
            new_callable=AsyncMock,
        ) as mock_fetch:
            result = await get_location("3000")
        mock_fetch.assert_not_called()
        assert result == "Melbourne"

    async def test_cache_miss_fetches_and_caches(self):
        with patch(
            "app.utils.locations._fetch_location",
            new_callable=AsyncMock,
            return_value="Brisbane",
        ) as mock_fetch:
            result = await get_location("4000")
        assert result == "Brisbane"
        mock_fetch.assert_called_once_with("4000")
        assert loc_module.location_cache["4000"] == "Brisbane"

    async def test_fetch_returns_none_not_cached(self):
        """A None result from the API should NOT be stored in the cache."""
        with patch(
            "app.utils.locations._fetch_location",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await get_location("9999")
        assert result is None
        assert "9999" not in loc_module.location_cache

    async def test_fetch_exception_returns_none(self):
        with patch(
            "app.utils.locations._fetch_location",
            new_callable=AsyncMock,
            side_effect=Exception("network failure"),
        ):
            result = await get_location("3000")
        assert result is None

    async def test_second_call_uses_cache(self):
        """Only one HTTP call should be made even with two lookups of the same postcode."""
        with patch(
            "app.utils.locations._fetch_location",
            new_callable=AsyncMock,
            return_value="Sydney",
        ) as mock_fetch:
            await get_location("2000")
            await get_location("2000")
        mock_fetch.assert_called_once()
