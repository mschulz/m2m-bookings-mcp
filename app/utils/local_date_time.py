"""Timezone conversion utilities for local-to-UTC datetime handling."""

from datetime import datetime

import pytz

from app.core.config import get_settings


def local_to_utc(local_dt):
    """Convert a naive local datetime to UTC using the configured timezone."""
    settings = get_settings()
    local_tz = pytz.timezone(settings.TZ_LOCALTIME)
    local_dt = local_tz.localize(local_dt, is_dst=settings.TZ_ISDST)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt


def UTC_now():
    """Return the current UTC datetime."""
    return datetime.utcnow()
