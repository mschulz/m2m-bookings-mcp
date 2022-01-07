# /app/commands/update_history.py

"""
	A run-daily program to calculate historical data and store in a table in the database.
    This runs early on the day following, so we need to set the dates carefully.
		date, today gain, today loss, today nett, recurring count
"""

import json
from datetime import datetime, date
import pendulum as pdl
import calendar

from flask import current_app
from app import db
from app.daos import booking_dao

from app.commands.model import History


def get_today_nett(today):
    start_created = today.start_of('day')
    end_created = today.end_of('day')
    today_gain, today_loss = booking_dao.gain_cancelled_in_range(start_created, end_created)
    nett = today_gain - today_loss
    return nett
    
def do_daily(today):
    # Today figures
    #  This program runs in the early hours of the FOLLOWING day, so we need to correct for this
    recurring_customer_count = booking_dao.recurring_current()
    yesterday_start_created = today.start_of('day').subtract(days=1)
    yesterday_end_created = today.end_of('day').subtract(days=1)
    
    recurring_customer_count = booking_dao.recurring_current()
    todays_nett = get_today_nett(today)
    print(f'Recurring since midnight today={todays_nett}')
    
    yesterday_gain, yesterday_loss = booking_dao.gain_cancelled_in_range(yesterday_start_created, yesterday_end_created)
    nett_for_day = yesterday_gain - yesterday_loss
    
    return (yesterday_end_created.date(), yesterday_gain, yesterday_loss, recurring_customer_count - todays_nett)

def add_to_history(day_date, gain, loss, rec_cus_count, use_db=True):
    is_saturday = day_date.day_of_week == 6
    is_eom = is_end_of_month(day_date)
    
    h = History()
    h.day_date = day_date
    h.gain = gain
    h.loss = loss
    h.nett = gain - loss
    h.recurring = rec_cus_count
    h.is_saturday = is_saturday
    h.is_eom = is_eom

    print(json.dumps(h.to_json(), indent=2))
    
    if use_db:
        try:
            db.session.add(h)
            db.session.commit()
        except:
            print('Failed to add to History table')
            db.session.rollback()
    

def is_end_of_month(today):
    days_in_month = today.days_in_month
    day_today = int(today.format('DD'))
    return days_in_month == day_today
    
if __name__ == '__main__':
    from app import create_app

    app = create_app()
    
    print('Update sales history ...')
    
    with app.app_context():
        today = pdl.now('UTC').in_timezone(current_app.config['TZ_LOCALTIME'])
        
        print(f'Today is {today}')
        
        day_date, gain, loss, rec_cus_count = do_daily(today)
        add_to_history(day_date, gain, loss, rec_cus_count, use_db=True)
