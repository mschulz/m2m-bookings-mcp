# local_date_time.py

from datetime import datetime, timezone
import pytz
from flask import current_app


def utc_to_local(utc_dt):
    local_tz = pytz.timezone(current_app.config["TZ_LOCALTIME"])
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=local_tz)


def local_to_utc(local):
    local_dt = local.localize(local, is_dst=current_app.config["TZ_ISDST"])
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt


def local_time_now(localTZ, isDST):
    local_tz = pytz.timezone(current_app.config["TZ_LOCALTIME"])
    utc_time = datetime.utcnow()
    return pytz.utc.localize(utc_time, is_dst=isDST).astimezone(local_tz)


def get_local_date_time_now(localTZ, isDST):
    local_time = local_time_now(localTZ, isDST)
    date = local_time.strftime("%d-%m-%Y")
    time = local_time.strftime("%H:%M")
    return (date, time)


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


def days_from_now(service_date, localTZ, isDST):
    today = local_time_now(localTZ, isDST)
    delta = today.replace(tzinfo=None) - service_date

    # print(f'days_from_now:: service_date={service_date} today={today.replace(tzinfo=None)}')
    # print(f' types: service_date={type(service_date)} today={type(today.replace(tzinfo=None))}')

    return delta.days


if __name__ == "__main__":
    """localTZ = 'Australia/Brisbane'
    isDST = None

    ltn = local_time_now(localTZ, isDST)
    print(f'local_time_now: {ltn} of type {type(ltn)}')

    gltn = get_local_date_time_now(localTZ, isDST)
    print(f'get_local_time_now: {gltn} of type {type(gltn)}')

    to_utc = to_UTC(ltn)
    print(f'to_UTC: {to_utc} of type {type(to_utc)}')

    utc_now = UTC_now()
    print(f'UTC_now: {utc_now} of type {type(utc_now)}')

    s = '2019-05-01'
    s2dt = string_to_datetime(s)
    print(f'string_to_datetime: {s2dt} of type {type(s2dt)}')
    s2dt = string_to_datetime(s, localTZ, isDST)
    print(f'string_to_datetime(localized): {s2dt} of type {type(s2dt)}')

    service_date = datetime.strptime('2019-05-30', '%Y-%m-%d')
    dfn = days_from_now(service_date, localTZ, isDST)
    print(f'days_from_now: {dfn} of type {type(dfn)}')"""

    from app import create_app

    app = create_app()

    with app.app_context():
        print(utc_to_local(UTC_now()))
