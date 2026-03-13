"""Tests for app/utils/klaviyo.py — Klaviyo integration, phone normalisation, and routing."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.utils.klaviyo import (
    WebhookRoute,
    _clean_price,
    _normalize_phone,
    check_klaviyo_profile,
    notify_klaviyo,
    process_with_klaviyo,
)


# ---------------------------------------------------------------------------
# _normalize_phone
# ---------------------------------------------------------------------------


class TestNormalizePhone:
    def test_standard_australian_0x_format(self):
        assert _normalize_phone("0412345678") == "+61412345678"

    def test_61_prefix_format(self):
        assert _normalize_phone("61412345678") == "+61412345678"

    def test_0061_prefix_format(self):
        assert _normalize_phone("0061412345678") == "+61412345678"

    def test_nine_digit_without_leading_zero(self):
        """9-digit number starting with valid area code digit."""
        assert _normalize_phone("412345678") == "+61412345678"

    def test_none_returns_none(self):
        assert _normalize_phone(None) is None

    def test_empty_string_returned_unchanged(self):
        assert _normalize_phone("") == ""

    def test_strips_spaces_and_dashes(self):
        result = _normalize_phone("0412 345 678")
        assert result == "+61412345678"

    def test_unknown_format_returned_unchanged(self):
        result = _normalize_phone("12345")
        assert result == "12345"


# ---------------------------------------------------------------------------
# _clean_price
# ---------------------------------------------------------------------------


class TestCleanPrice:
    def test_dollar_string_to_float(self):
        assert _clean_price("$143.02") == 143.02

    def test_plain_float_string(self):
        assert _clean_price("143.02") == 143.02

    def test_none_returns_none(self):
        assert _clean_price(None) is None

    def test_empty_returns_empty(self):
        assert _clean_price("") == ""

    def test_zero(self):
        assert _clean_price("$0.00") == 0.0

    def test_invalid_returns_unchanged(self):
        assert _clean_price("not-a-price") == "not-a-price"


# ---------------------------------------------------------------------------
# WebhookRoute enum
# ---------------------------------------------------------------------------


class TestWebhookRoute:
    def test_all_routes_defined(self):
        routes = {r.value for r in WebhookRoute}
        assert "booking_new" in routes
        assert "booking_updated" in routes
        assert "booking_restored" in routes
        assert "booking_completed" in routes
        assert "booking_cancellation" in routes
        assert "booking_team_changed" in routes
        assert "customer_new" in routes
        assert "customer_updated" in routes

    def test_is_str_enum(self):
        assert WebhookRoute.BOOKING_NEW == "booking_new"


# ---------------------------------------------------------------------------
# notify_klaviyo
# ---------------------------------------------------------------------------


def _enabled_settings():
    """Mock settings with Klaviyo enabled."""
    return MagicMock(KLAVIYO_ENABLED=True)


class TestNotifyKlaviyo:
    async def test_house_clean_calls_post_home_data(self):
        data = {"email": "test@example.com", "service_category": "House Clean"}
        with (
            patch("app.utils.klaviyo.get_settings", return_value=_enabled_settings()),
            patch("app.utils.klaviyo.Klaviyo") as MockKlaviyo,
        ):
            instance = AsyncMock()
            MockKlaviyo.return_value = instance
            await notify_klaviyo("House Clean", data)
        instance.post_home_data.assert_called_once_with(data)

    async def test_bond_clean_calls_post_bond_data(self):
        data = {"email": "test@example.com", "service_category": "Bond Clean"}
        with (
            patch("app.utils.klaviyo.get_settings", return_value=_enabled_settings()),
            patch("app.utils.klaviyo.Klaviyo") as MockKlaviyo,
        ):
            instance = AsyncMock()
            MockKlaviyo.return_value = instance
            await notify_klaviyo("Bond Clean", data)
        instance.post_bond_data.assert_called_once_with(data)

    async def test_klaviyo_disabled_skips_call(self):
        with (
            patch(
                "app.utils.klaviyo.get_settings",
                return_value=MagicMock(KLAVIYO_ENABLED=False),
            ),
            patch("app.utils.klaviyo.Klaviyo") as MockKlaviyo,
        ):
            await notify_klaviyo("House Clean", {"email": "x@x.com"})
        MockKlaviyo.assert_not_called()


# ---------------------------------------------------------------------------
# process_with_klaviyo
# ---------------------------------------------------------------------------


class TestProcessWithKlaviyo:
    async def test_booking_new_house_clean_notifies(self):
        data = {
            "email": "test@example.com",
            "service_category": "House Clean",
            "is_new_customer": "true",
        }
        with patch("app.utils.klaviyo.notify_klaviyo", new_callable=AsyncMock) as mock_notify:
            await process_with_klaviyo(data, WebhookRoute.BOOKING_NEW)
        mock_notify.assert_called_once_with("House Clean", data)

    async def test_booking_new_bond_clean_notifies(self):
        data = {
            "email": "test@example.com",
            "service_category": "Bond Clean",
        }
        with patch("app.utils.klaviyo.notify_klaviyo", new_callable=AsyncMock) as mock_notify:
            await process_with_klaviyo(data, WebhookRoute.BOOKING_NEW)
        mock_notify.assert_called_once_with("Bond Clean", data)

    async def test_booking_new_other_category_no_notification(self):
        """Categories other than House/Bond Clean should NOT trigger Klaviyo."""
        data = {"email": "test@example.com", "service_category": "NDIS Clean"}
        with patch("app.utils.klaviyo.notify_klaviyo", new_callable=AsyncMock) as mock_notify:
            await process_with_klaviyo(data, WebhookRoute.BOOKING_NEW)
        mock_notify.assert_not_called()

    async def test_booking_team_changed_no_notification(self):
        data = {"email": "test@example.com", "service_category": "House Clean"}
        with patch("app.utils.klaviyo.notify_klaviyo", new_callable=AsyncMock) as mock_notify:
            await process_with_klaviyo(data, WebhookRoute.BOOKING_TEAM_CHANGED)
        mock_notify.assert_not_called()

    async def test_customer_new_creates_profile_when_not_exists(self):
        data = {"email": "new@example.com"}
        with (
            patch(
                "app.utils.klaviyo.check_klaviyo_profile",
                new_callable=AsyncMock,
                return_value={"exists": False, "profile_id": None},
            ),
            patch("app.utils.klaviyo.Klaviyo") as MockKlaviyo,
        ):
            instance = AsyncMock()
            MockKlaviyo.return_value = instance
            await process_with_klaviyo(data, WebhookRoute.CUSTOMER_NEW)
        instance.create_klaviyo_profile.assert_called_once_with(data)

    async def test_customer_new_skips_create_when_profile_exists(self):
        data = {"email": "existing@example.com"}
        with (
            patch(
                "app.utils.klaviyo.check_klaviyo_profile",
                new_callable=AsyncMock,
                return_value={"exists": True, "profile_id": "abc123"},
            ),
            patch("app.utils.klaviyo.Klaviyo") as MockKlaviyo,
        ):
            instance = AsyncMock()
            MockKlaviyo.return_value = instance
            await process_with_klaviyo(data, WebhookRoute.CUSTOMER_NEW)
        instance.create_klaviyo_profile.assert_not_called()

    async def test_customer_updated_patches_profile(self):
        data = {"email": "test@example.com"}
        with patch("app.utils.klaviyo.Klaviyo") as MockKlaviyo:
            instance = AsyncMock()
            MockKlaviyo.return_value = instance
            await process_with_klaviyo(data, WebhookRoute.CUSTOMER_UPDATED)
        instance.update_klaviyo_profile.assert_called_once_with(data)

    async def test_non_dict_data_returns_early(self):
        """process_with_klaviyo must not raise when data is not a dict."""
        with patch("app.utils.klaviyo.notify_klaviyo", new_callable=AsyncMock) as mock_notify:
            await process_with_klaviyo("OK", WebhookRoute.BOOKING_NEW)
        mock_notify.assert_not_called()

    async def test_customer_new_no_email_skips_all(self):
        data = {}  # no email key
        with (
            patch("app.utils.klaviyo.check_klaviyo_profile", new_callable=AsyncMock) as mock_check,
            patch("app.utils.klaviyo.Klaviyo") as MockKlaviyo,
        ):
            await process_with_klaviyo(data, WebhookRoute.CUSTOMER_NEW)
        mock_check.assert_not_called()


# ---------------------------------------------------------------------------
# check_klaviyo_profile
# ---------------------------------------------------------------------------


class TestCheckKlaviyoProfile:
    async def test_klaviyo_disabled_returns_not_exists(self):
        with patch(
            "app.utils.klaviyo.get_settings",
            return_value=MagicMock(KLAVIYO_ENABLED=False),
        ):
            result = await check_klaviyo_profile("test@example.com")
        assert result == {"exists": False, "profile_id": None}

    async def test_exception_returns_not_exists(self):
        with (
            patch(
                "app.utils.klaviyo.get_settings",
                return_value=MagicMock(KLAVIYO_ENABLED=True),
            ),
            patch("app.utils.klaviyo.Klaviyo") as MockKlaviyo,
        ):
            instance = AsyncMock()
            instance.check_profile.side_effect = Exception("network error")
            MockKlaviyo.return_value = instance
            result = await check_klaviyo_profile("test@example.com")
        assert result == {"exists": False, "profile_id": None}
