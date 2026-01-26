# app/report/report_new.py

"""
Return customer summary data:
    for all - Net, Gain, Loss
        Today
        Yesterday
        This Week (to date)
        This Month (to date)

    Recurring customer count
"""

import json
import pendulum as pdl

from flask import current_app
from app.daos.dao_booking import booking_dao


def create_report():
    # Today figures
    today = pdl.now("UTC").in_timezone(current_app.config["TZ_LOCALTIME"])
    start_created = today.start_of("day").in_timezone("utc")
    end_created = today.end_of("day").in_timezone("utc")

    print(f"Today is {today}")

    today_gain, today_loss = booking_dao.gain_cancelled_in_range(
        start_created, end_created
    )

    # Yesterday Figures
    yesterday = (
        pdl.now("UTC").in_timezone(current_app.config["TZ_LOCALTIME"]).subtract(days=1)
    )
    start_created = yesterday.start_of("day").in_timezone("utc")
    end_created = yesterday.end_of("day").in_timezone("utc")
    yesterday_gain, yesterday_loss = booking_dao.gain_cancelled_in_range_new(
        start_created, end_created
    )

    print(f"Yesterday is {yesterday} {start_created=} {end_created=}")
    print(
        f"yesterday gains = {booking_dao.get_gain_in_date_range_list(start_created, end_created)}"
    )
    print(
        f"yesterday cancels = {booking_dao.get_cancelled_in_date_range_list_new(start_created, end_created)}"
    )

    print(f"yesterday is {yesterday}")

    # This week (to date) figures
    start_created = today.start_of("week").subtract(days=1).in_timezone("utc")
    end_created = start_created.add(days=7)
    week_gain, week_loss = booking_dao.gain_cancelled_in_range_new(
        start_created, end_created
    )

    # this month (to date) figures
    # date_today = date.today()
    # current_year = date_today.strftime("%Y")
    # current_month = date_today.strftime("%m")
    current_year = today.format("YYYY")
    current_month = today.format("MM")
    month_gain = booking_dao.get_gain_by_month(current_month, current_year)
    month_loss = booking_dao.get_cancelled_by_month_new(current_month, current_year)

    # print(f'gain_this_month={booking_dao.get_gain_by_month_list(current_month, current_year)}')

    # Current recurring customer count
    recurring_customer_count = booking_dao.recurring_current()

    res = {
        "today": {
            "gain": today_gain,
            "loss": today_loss,
            "nett": today_gain - today_loss,
        },
        "yesterday": {
            "gain": yesterday_gain,
            "loss": yesterday_loss,
            "nett": yesterday_gain - yesterday_loss,
        },
        "week_to_date": {
            "gain": week_gain,
            "loss": week_loss,
            "nett": week_gain - week_loss,
        },
        "month_to_date": {
            "gain": month_gain,
            "loss": month_loss,
            "nett": month_gain - month_loss,
        },
        "recurring_customer_count": recurring_customer_count,
    }
    return res


if __name__ == "__main__":
    from app import create_app

    app = create_app()

    with app.app_context():
        res = create_report()
        print(json.dumps(res, indent=2))
