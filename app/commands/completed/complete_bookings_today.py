# app/commands/completed/complete_bookings_today.py

import sys
import datetime
import logging

import pytz

from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.utils.email_service import send_completed_bookings_email
from app.commands.completed.booking import Booking

logger = logging.getLogger(__name__)


def main():
    if len(sys.argv) != 2:
        print("Missing argument for timezone name: AEST,ACST,AWST")
        sys.exit(1)

    tz_name = sys.argv[1]
    settings = get_settings()
    setup_logging()

    logger.info("%s startup", settings.APP_NAME)

    tz = pytz.timezone(settings.TZ_LOCALTIME)
    today_date_string = datetime.datetime.now(tz).date().strftime("%Y-%m-%d")

    completed_count = tz_count = 0
    b = Booking()
    booking_list = b.get_all_in_tz(today_date_string, tz_name)

    logger.info("get_all_booking_ids: %s", booking_list)

    tz_count = booking_list["count"]
    if tz_count > 0:
        for i in booking_list["id_list"]:
            res = b.complete(i)
            completed_count += res
            logger.info("completed: %s used: %s", i, res)

    msg = (
        f"complete_bookings_today:: {completed_count} bookings marked as "
        f"completed out of {tz_count}({tz_name})"
    )
    logger.info(msg)

    toaddr = settings.OVERRIDE_ADDR
    send_completed_bookings_email(toaddr, completed_count, tz_count, tz_name)


if __name__ == "__main__":
    main()
