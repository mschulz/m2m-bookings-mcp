# app/local_date_time.py

from datetime import datetime, timezone

import pytz

from config import get_settings


def utc_to_local(utc_dt):
    settings = get_settings()
    local_tz = pytz.timezone(settings.TZ_LOCALTIME)
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=local_tz)


def local_to_utc(local_dt):
    settings = get_settings()
    local_tz = pytz.timezone(settings.TZ_LOCALTIME)
    local_dt = local_tz.localize(local_dt, is_dst=settings.TZ_ISDST)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt


def local_time_now():
    settings = get_settings()
    local_tz = pytz.timezone(settings.TZ_LOCALTIME)
    utc_time = datetime.utcnow()
    return pytz.utc.localize(utc_time, is_dst=settings.TZ_ISDST).astimezone(local_tz)


def get_local_date_time_now():
    local_time = local_time_now()
    d = local_time.strftime("%d-%m-%Y")
    t = local_time.strftime("%H:%M")
    return (d, t)


def to_UTC(d):
    return d.astimezone(pytz.utc)


def UTC_now():
    return datetime.utcnow()


def string_to_datetime(s, *args):
    date_time_obj = datetime.strptime(s, "%Y-%m-%d")
    if len(args) > 0:
        return to_UTC(date_time_obj)
    return date_time_obj


def to_datetime(s):
    if "," in s:
        return datetime.strptime(s, "%a, %d %b %Y %H:%M:%S %Z")
    if " " in s:
        return datetime.strptime(s, "%d %b %Y")
    if "/" in s:
        return datetime.strptime(s, "%d/%m/%Y")
    if "-" in s:
        try:
            o = datetime.strptime(s, "%d-%m-%Y")
        except ValueError:
            o = datetime.strptime(s, "%Y-%m-%d")
        return o
    raise ValueError


def days_from_now(service_date):
    today = local_time_now()
    delta = today.replace(tzinfo=None) - service_date
    return delta.days
