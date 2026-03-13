"""Tests for app/utils/validation.py — field coercion and parsing helpers."""

import pytest

from app.utils.validation import (
    check_postcode,
    dollar_string_to_int,
    parse_date,
    parse_datetime,
    parse_team_list,
    parse_team_share,
    safe_int,
    string_to_boolean,
    truncate_field,
)


# ---------------------------------------------------------------------------
# truncate_field
# ---------------------------------------------------------------------------


class TestTruncateField:
    def test_returns_none_when_value_is_none(self):
        assert truncate_field(None, 10, "field") is None

    def test_returns_value_unchanged_when_within_limit(self):
        assert truncate_field("hello", 10, "field") == "hello"

    def test_truncates_to_max_length(self):
        result = truncate_field("hello world", 5, "field")
        assert result == "hello"
        assert len(result) == 5

    def test_exact_length_not_truncated(self):
        result = truncate_field("hello", 5, "field")
        assert result == "hello"

    def test_logs_warning_on_truncation(self, caplog):
        import logging
        with caplog.at_level(logging.WARNING, logger="app.utils.validation"):
            truncate_field("this is too long", 5, "myfield", record_id=99)
        assert "myfield" in caplog.text


# ---------------------------------------------------------------------------
# string_to_boolean
# ---------------------------------------------------------------------------


class TestStringToBoolean:
    def test_true_string(self):
        assert string_to_boolean("true") is True

    def test_yes_string(self):
        assert string_to_boolean("yes") is True

    def test_one_string(self):
        assert string_to_boolean("1") is True

    def test_false_string(self):
        assert string_to_boolean("false") is False

    def test_no_string(self):
        assert string_to_boolean("no") is False

    def test_zero_string(self):
        assert string_to_boolean("0") is False

    def test_bool_true_passthrough(self):
        assert string_to_boolean(True) is True

    def test_bool_false_passthrough(self):
        assert string_to_boolean(False) is False

    def test_uppercase_true(self):
        assert string_to_boolean("TRUE") is True


# ---------------------------------------------------------------------------
# dollar_string_to_int
# ---------------------------------------------------------------------------


class TestDollarStringToInt:
    def test_dollar_string(self):
        assert dollar_string_to_int("$67.64") == 6764

    def test_string_without_dollar(self):
        assert dollar_string_to_int("67.64") == 6764

    def test_zero(self):
        assert dollar_string_to_int("$0.00") == 0

    def test_none_returns_zero(self):
        assert dollar_string_to_int(None) == 0

    def test_none_string_returns_zero(self):
        assert dollar_string_to_int("None") == 0

    def test_integer_input(self):
        assert dollar_string_to_int(100) == 100

    def test_float_string(self):
        assert dollar_string_to_int("$143.00") == 14300


# ---------------------------------------------------------------------------
# parse_datetime
# ---------------------------------------------------------------------------


class TestParseDatetime:
    def test_none_returns_none(self):
        assert parse_datetime(None) is None

    def test_empty_string_returns_none(self):
        assert parse_datetime("") is None

    def test_iso_with_z(self):
        result = parse_datetime("2024-01-15T10:00:00Z")
        assert result is not None
        assert result.year == 2024

    def test_with_timezone_offset(self):
        result = parse_datetime("2024-01-15T10:00:00+10:00")
        assert result is not None
        assert result.year == 2024

    def test_dd_mm_yyyy_ampm(self):
        # The code checks `"am" in val` (case-sensitive), so input must use lowercase
        result = parse_datetime("15/01/2024 10:00am")
        assert result is not None
        assert result.day == 15
        assert result.month == 1

    def test_dd_mm_yyyy_24h(self):
        result = parse_datetime("15/01/2024 10:00")
        assert result is not None
        assert result.day == 15

    def test_dd_slash_mm_slash_yyyy(self):
        result = parse_datetime("15/01/2024")
        assert result is not None
        assert result.day == 15

    def test_yyyy_mm_dd(self):
        result = parse_datetime("2024-01-15")
        assert result is not None
        assert result.year == 2024

    def test_invalid_returns_none(self):
        result = parse_datetime("not-a-date")
        assert result is None


# ---------------------------------------------------------------------------
# parse_date
# ---------------------------------------------------------------------------


class TestParseDate:
    def test_none_returns_none(self):
        assert parse_date(None) is None

    def test_empty_string_returns_none(self):
        assert parse_date("") is None

    def test_slash_format(self):
        result = parse_date("15/01/2024")
        assert result is not None
        assert result.day == 15
        assert result.month == 1
        assert result.year == 2024

    def test_dash_format(self):
        result = parse_date("2024-01-15")
        assert result is not None
        assert result.year == 2024

    def test_datetime_string_extracts_date(self):
        result = parse_date("15/01/2024 10:00")
        assert result is not None
        assert result.day == 15


# ---------------------------------------------------------------------------
# parse_team_list
# ---------------------------------------------------------------------------


class TestParseTeamList:
    def test_empty_string_returns_empty(self):
        assert parse_team_list("", "title") == ""

    def test_none_returns_empty(self):
        assert parse_team_list(None, "title") == ""

    def test_extracts_titles(self):
        val = "[{'title': 'Alice', 'id': '1'}, {'title': 'Bob', 'id': '2'}]"
        result = parse_team_list(val, "title")
        assert result == "Alice,Bob"

    def test_extracts_ids(self):
        val = "[{'title': 'Alice', 'id': '1'}, {'title': 'Bob', 'id': '2'}]"
        result = parse_team_list(val, "id")
        assert result == "1,2"

    def test_single_item(self):
        val = "[{'title': 'Alice', 'id': '1'}]"
        result = parse_team_list(val, "title")
        assert result == "Alice"

    def test_double_quoted_dict(self):
        val = '[{"title": "Alice", "id": "1"}]'
        result = parse_team_list(val, "title")
        assert result == "Alice"

    def test_invalid_raises_value_error(self):
        with pytest.raises(ValueError, match="Failed to sanitize"):
            parse_team_list("{bad json {{", "title")


# ---------------------------------------------------------------------------
# parse_team_share
# ---------------------------------------------------------------------------


class TestParseTeamShare:
    def test_name_dash_amount(self):
        assert parse_team_share("Alice - $67.00") == 6700

    def test_plain_amount(self):
        assert parse_team_share("$50.00") == 5000

    def test_none_returns_none(self):
        assert parse_team_share(None) is None

    def test_comma_multiple_returns_none(self):
        """Multiple entries (comma-separated) cannot be parsed to a single value."""
        assert parse_team_share("Alice - $50.00, Bob - $50.00") is None

    def test_empty_string_returns_none(self):
        assert parse_team_share("") is None


# ---------------------------------------------------------------------------
# safe_int
# ---------------------------------------------------------------------------


class TestSafeInt:
    def test_none_returns_none(self):
        assert safe_int(None) is None

    def test_int_passthrough(self):
        assert safe_int(42) == 42

    def test_string_converts(self):
        assert safe_int("12345") == 12345

    def test_empty_string_returns_none(self):
        assert safe_int("") is None

    def test_float_converts(self):
        assert safe_int(3.7) == 3


# ---------------------------------------------------------------------------
# check_postcode
# ---------------------------------------------------------------------------


class TestCheckPostcode:
    def test_valid_numeric_postcode(self):
        data = {"zip": "3000"}
        assert check_postcode(data, "booking_id", 1) == "3000"

    def test_non_numeric_returns_none(self):
        data = {"zip": "TBC"}
        assert check_postcode(data, "booking_id", 1) is None

    def test_tba_returns_none(self):
        data = {"zip": "tba"}
        assert check_postcode(data, "booking_id", 1) is None

    def test_missing_zip_returns_none(self):
        data = {}
        assert check_postcode(data, "booking_id", 1) is None

    def test_none_zip_returns_none(self):
        data = {"zip": None}
        assert check_postcode(data, "booking_id", 1) is None
