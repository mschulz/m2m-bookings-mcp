"""Gmail API email service for error alerts and operational notifications."""

import base64
import json
import logging
from email.mime.text import MIMEText

from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _get_gmail_service():
    """Build an authenticated Gmail API service client from service account credentials."""
    settings = get_settings()
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(settings.GMAIL_SERVICE_ACCOUNT_CREDENTIALS),
        scopes=["https://www.googleapis.com/auth/gmail.send"],
        subject=settings.FROM_ADDRESS,
    )
    return build("gmail", "v1", credentials=credentials)


def send_email(subject: str, sender: tuple | str, recipients: list[str], html_body: str):
    """Send email via Gmail API."""
    settings = get_settings()
    if settings.testing:
        logger.debug("Testing mode - email suppressed: %s to %s", subject, recipients)
        return

    try:
        service = _get_gmail_service()

        from_addr = sender[1] if isinstance(sender, tuple) else sender

        mime = MIMEText(html_body, "html")
        mime["to"] = ", ".join(recipients)
        mime["subject"] = subject
        mime["from"] = from_addr

        raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
        raw_msg = {"raw": raw}

        service.users().messages().send(userId="me", body=raw_msg).execute()
        logger.info("Email '%s' sent to %s", subject, recipients)
    except Exception as e:
        logger.error("Failed to send email to %s: %s", recipients, e)


def send_error_email(toaddr, error_msg):
    """Send developer email when an error has occurred."""
    settings = get_settings()
    body = f"<h1>{settings.APP_NAME}: Error</h1><p>{error_msg}</p>"

    send_email(
        subject=f"{settings.APP_NAME}: Error has occurred",
        sender=(settings.FROM_NAME, settings.FROM_ADDRESS),
        recipients=toaddr if isinstance(toaddr, list) else [toaddr],
        html_body=body,
    )


def send_missing_location_email(toaddr, error_msg, locations, postcodes):
    """Send an alert email about bookings with missing location data."""
    settings = get_settings()
    body = (
        f"<h1>{settings.COMPANY_NAME}: Missing Location Information</h1>"
        f"<p>{error_msg}</p>"
        f"<p>Locations: {locations}, Postcodes: {postcodes}</p>"
    )

    send_email(
        subject=f"{settings.COMPANY_NAME}: Missing Location information!!",
        sender=(settings.FROM_NAME, settings.FROM_ADDRESS),
        recipients=toaddr if isinstance(toaddr, list) else [toaddr],
        html_body=body,
    )


def send_updated_locations_email(toaddr, number_locations, updated, missing, postcodes):
    """Send a summary email after a bulk location update run."""
    settings = get_settings()
    body = (
        f"<h1>{settings.APP_NAME}: Updated Booking Locations</h1>"
        f"<p>Total: {number_locations}, Updated: {updated}, "
        f"Missing: {missing}, Postcodes: {postcodes}</p>"
    )

    send_email(
        subject=f"{settings.APP_NAME}: Updated booking locations information!!",
        sender=(settings.FROM_NAME, settings.FROM_ADDRESS),
        recipients=toaddr if isinstance(toaddr, list) else [toaddr],
        html_body=body,
    )


def send_completed_bookings_email(toaddr, bookings_count, n_active, tz_name):
    """Send a summary email after marking bookings as completed."""
    settings = get_settings()
    body = (
        f"<h1>{settings.APP_NAME}: Completed Bookings</h1>"
        f"<p>{bookings_count} bookings marked completed. "
        f"Active: {n_active}. Timezone: {tz_name}</p>"
    )

    send_email(
        subject=f"{settings.APP_NAME}: {bookings_count} bookings marked completed",
        sender=(settings.FROM_NAME, settings.FROM_ADDRESS),
        recipients=[toaddr],
        html_body=body,
    )
