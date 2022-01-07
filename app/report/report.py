# app/report/report.py

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
from datetime import datetime, date
import pendulum as pdl

from flask import current_app
from app.daos import booking_dao


def gain_loss_in_range(start_date, end_date):
    # Need to convert from Pendulum datetime to datetime.datetime format
    start_created = datetime.fromtimestamp(start_date.timestamp(), pdl.tz.UTC)
    end_created = datetime.fromtimestamp(end_date.timestamp(), pdl.tz.UTC)
    
    gain = booking_dao.get_gain_in_date_range(start_created, end_created)
    loss = booking_dao.get_cancelled_in_date_range(start_created, end_created)
    return gain, loss
    
def create_report():
    # Today figures
    today = pdl.now('UTC').in_timezone(current_app.config['TZ_LOCALTIME'])
    start_created = today.start_of('day')
    end_created = today.end_of('day')
    
    today_gain, today_loss = gain_loss_in_range(start_created, end_created)

    # Yesterday Figures
    yesterday = pdl.yesterday('UTC').in_timezone(current_app.config['TZ_LOCALTIME'])
    start_created = yesterday.start_of('day')
    end_created = yesterday.end_of('day')
    yesterday_gain, yesterday_loss = gain_loss_in_range(start_created, end_created)
    
    # This week (to date) figures
    today = pdl.now('UTC').in_timezone(current_app.config['TZ_LOCALTIME'])
    start_created = today.start_of('week').subtract(days=1)
    end_created = start_created.add(days=7)
    week_gain, week_loss = gain_loss_in_range(start_created, end_created)
    
    #this month (to date) figures
    date_today = date.today()
    current_year = date_today.strftime("%Y")
    current_month = date_today.strftime("%m")
    month_gain = booking_dao.get_gain_by_month(current_month, current_year)
    month_loss = booking_dao.get_cancelled_by_month(current_month, current_year)
    
    #print(f'gain_this_month={booking_dao.get_gain_by_month_list(current_month, current_year)}')
    
    # Current recurring customer count
    recurring_customer_count = booking_dao.recurring_current()
    
    res = {
        "today": {
            "gain": today_gain,
            "loss": today_loss,
            "nett": today_gain - today_loss
        },
        "yesterday": {
            "gain": yesterday_gain,
            "loss": yesterday_loss,
            "nett": yesterday_gain - yesterday_loss
        },
        "week_to_date": {
            "gain": week_gain,
            "loss": week_loss,
            "nett": week_gain - week_loss
        },
        "month_to_date": {
            "gain": month_gain,
            "loss": month_loss,
            "nett": month_gain - month_loss
        },
        "recurring_customer_count": recurring_customer_count
    }
    return res
    
    
if __name__ == '__main__':
    from app import create_app

    app = create_app()
    
    with app.app_context():
        res = create_report()
        print(json.dumps(res, indent=2))
