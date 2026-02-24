# app/local_date_time.py

from datetime import datetime

import pytz

from config import get_settings


def local_to_utc(local_dt):
    settings = get_settings()
    local_tz = pytz.timezone(settings.TZ_LOCALTIME)
    local_dt = local_tz.localize(local_dt, is_dst=settings.TZ_ISDST)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt


def UTC_now():
    return datetime.utcnow()
