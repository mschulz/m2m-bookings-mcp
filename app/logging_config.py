"""Logging configuration with optional Gmail error handler for production."""

import logging
import logging.config

from config import get_settings
from app.utils.gmail_handler import GmailOAuth2Handler


def setup_logging():
    """Configure root logger and attach a Gmail error handler in production."""
    settings = get_settings()

    log_level = "DEBUG" if settings.debug else "INFO"
    if settings.testing:
        log_level = "ERROR"

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": log_level,
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": log_level,
        },
        "loggers": {
            "uvicorn": {"level": "INFO"},
            "sqlalchemy.engine": {"level": "WARNING"},
        },
    }

    logging.config.dictConfig(config)

    # Add Gmail error handler in non-debug mode
    if not settings.debug and settings.GMAIL_SERVICE_ACCOUNT_CREDENTIALS:
        try:
            m = settings.SUPPORT_EMAIL.split("@")
            to_addr = f"{m[0]}+error@{m[1]}"
            subject = f"{settings.APP_NAME}: Error Detected"

            mail_handler = GmailOAuth2Handler(
                credentials_json=settings.GMAIL_SERVICE_ACCOUNT_CREDENTIALS,
                impersonate_user=settings.FROM_ADDRESS,
                recipient=to_addr,
                subject=subject,
            )
            mail_handler.setLevel(logging.ERROR)
            logging.getLogger().addHandler(mail_handler)
        except Exception as e:
            logging.getLogger(__name__).warning(
                "Failed to set up Gmail error handler: %s", e
            )
