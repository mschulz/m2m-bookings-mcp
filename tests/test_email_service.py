"""Tests for app/utils/email_service.py — Gmail email sending helpers."""

from unittest.mock import MagicMock, patch

import pytest

from app.utils.email_service import (
    _send_notification,
    send_completed_bookings_email,
    send_email,
    send_error_email,
    send_missing_location_email,
    send_updated_locations_email,
)


# ---------------------------------------------------------------------------
# send_email
# ---------------------------------------------------------------------------


class TestSendEmail:
    def test_suppressed_in_testing_mode(self):
        """In testing mode no Gmail call should be made."""
        with patch("app.utils.email_service._get_gmail_service") as mock_gmail:
            send_email(
                subject="Test",
                sender="noreply@example.com",
                recipients=["user@example.com"],
                html_body="<p>Hello</p>",
            )
        mock_gmail.assert_not_called()

    def test_suppressed_logs_message(self, caplog):
        import logging
        with caplog.at_level(logging.DEBUG, logger="app.utils.email_service"):
            send_email(
                subject="Test Subject",
                sender="noreply@example.com",
                recipients=["user@example.com"],
                html_body="<p>body</p>",
            )
        assert "suppressed" in caplog.text.lower() or "testing" in caplog.text.lower()


# ---------------------------------------------------------------------------
# _send_notification
# ---------------------------------------------------------------------------


class TestSendNotification:
    def test_accepts_string_recipient(self):
        with patch("app.utils.email_service.send_email") as mock_send:
            _send_notification("Subject", "Body", "user@example.com")
        mock_send.assert_called_once()
        _, kwargs = mock_send.call_args
        assert kwargs.get("recipients") == ["user@example.com"] or mock_send.call_args[0][2] == ["user@example.com"]

    def test_accepts_list_recipient(self):
        with patch("app.utils.email_service.send_email") as mock_send:
            _send_notification("Subject", "Body", ["a@x.com", "b@x.com"])
        mock_send.assert_called_once()


# ---------------------------------------------------------------------------
# Specialised email functions
# ---------------------------------------------------------------------------


class TestSendErrorEmail:
    def test_calls_send_notification(self):
        with patch("app.utils.email_service._send_notification") as mock_notify:
            send_error_email("support@example.com", "Something went wrong")
        mock_notify.assert_called_once()
        subject = mock_notify.call_args[0][0]
        assert "Error" in subject

    def test_body_contains_error_message(self):
        with patch("app.utils.email_service._send_notification") as mock_notify:
            send_error_email("support@example.com", "DB connection failed")
        body = mock_notify.call_args[0][1]
        assert "DB connection failed" in body


class TestSendMissingLocationEmail:
    def test_calls_send_notification(self):
        with patch("app.utils.email_service._send_notification") as mock_notify:
            send_missing_location_email("support@example.com", "['3000']", 5, 1)
        mock_notify.assert_called_once()

    def test_body_contains_counts(self):
        with patch("app.utils.email_service._send_notification") as mock_notify:
            send_missing_location_email("support@example.com", "['3000']", 5, 1)
        body = mock_notify.call_args[0][1]
        assert "5" in body
        assert "1" in body


class TestSendUpdatedLocationsEmail:
    def test_calls_send_notification(self):
        with patch("app.utils.email_service._send_notification") as mock_notify:
            send_updated_locations_email("support@example.com", 10, 8, 2, 3)
        mock_notify.assert_called_once()

    def test_body_contains_counts(self):
        with patch("app.utils.email_service._send_notification") as mock_notify:
            send_updated_locations_email("support@example.com", 10, 8, 2, 3)
        body = mock_notify.call_args[0][1]
        assert "10" in body
        assert "8" in body


class TestSendCompletedBookingsEmail:
    def test_calls_send_notification(self):
        with patch("app.utils.email_service._send_notification") as mock_notify:
            send_completed_bookings_email("support@example.com", 12, 15, "AEST")
        mock_notify.assert_called_once()

    def test_body_contains_timezone(self):
        with patch("app.utils.email_service._send_notification") as mock_notify:
            send_completed_bookings_email("support@example.com", 12, 15, "AEST")
        body = mock_notify.call_args[0][1]
        assert "AEST" in body

    def test_subject_contains_count(self):
        with patch("app.utils.email_service._send_notification") as mock_notify:
            send_completed_bookings_email("support@example.com", 12, 15, "AEST")
        subject = mock_notify.call_args[0][0]
        assert "12" in subject
