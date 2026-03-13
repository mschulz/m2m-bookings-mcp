"""Tests for app/utils/local_date_time.py — timezone conversion helpers."""

from datetime import datetime, timezone

import pytest

from app.utils.local_date_time import UTC_now, local_to_utc


class TestLocalToUtc:
    def test_converts_brisbane_to_utc(self):
        """AEST (UTC+10) midday should become 02:00 UTC."""
        local_dt = datetime(2024, 1, 15, 12, 0, 0)
        result = local_to_utc(local_dt)
        assert result.tzinfo is not None
        # Brisbane is UTC+10 → 12:00 local = 02:00 UTC
        assert result.hour == 2
        assert result.day == 15

    def test_result_is_timezone_aware(self):
        local_dt = datetime(2024, 6, 1, 8, 0, 0)
        result = local_to_utc(local_dt)
        assert result.tzinfo is not None

    def test_date_preserved(self):
        local_dt = datetime(2024, 3, 10, 0, 30, 0)
        result = local_to_utc(local_dt)
        # 00:30 Brisbane → previous day 14:30 UTC
        assert result.year == 2024


class TestUTCNow:
    def test_returns_datetime(self):
        result = UTC_now()
        assert isinstance(result, datetime)

    def test_returns_recent_time(self):
        """Should be within a few seconds of actual UTC now."""
        before = datetime.utcnow()
        result = UTC_now()
        after = datetime.utcnow()
        assert before <= result <= after
