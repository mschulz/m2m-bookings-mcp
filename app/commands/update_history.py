# /app/commands/update_history.py

"""
	A run-daily program to calculate historical data and store in a table in the database.
    This runs early on the day following, so we need to set the dates carefully.
		date, today gain, today loss, today nett, recurring count
"""

import json
from datetime import datetime, date
import pendulum as pdl

from flask import current_app
from app import db
from app.daos import booking_dao

from app.commands.model import History


def get_today_nett(today):
    start_created = today.start_of('day')
    end_created = today.end_of('day')
    today_gain, today_loss = booking_dao.gain_loss_in_range(start_created, end_created)
    nett = today_gain - today_loss
    
    print(f'{start_created = } {end_created = } {today_gain = } {today_loss = }')
    
    return nett
    
def do_daily(today):
    # Today figures
    #  This program runs in the early hours of the FOLLOWING day, so we need to correct for this
    recurring_customer_count = booking_dao.recurring_current()
    yesterday_start_created = today.start_of('day').subtract(days=1)
    yesterday_end_created = today.end_of('day').subtract(days=1)
    
    recurring_customer_count = booking_dao.recurring_current()
    print(f'Today {recurring_customer_count = }')
    
    yesterday_gain, yesterday_loss = booking_dao.gain_loss_in_range(yesterday_start_created, yesterday_end_created)
    nett_for_day = yesterday_gain - yesterday_loss
    
    todays_nett = get_today_nett(today)
    
    print(f'{todays_nett = }')
    
    print(yesterday_end_created.date(), yesterday_gain, yesterday_loss, nett_for_day, recurring_customer_count - todays_nett)
    return (yesterday_end_created.date(), yesterday_gain, yesterday_loss, recurring_customer_count - todays_nett)

def add_to_history(day_date, gain, loss, rec_cus_count):
    h = History()
    h.day_date = start_created.date()
    h.gain = gain
    h.loss = loss
    h.nett = gain - loss
    h.recurring = rec_cus_count
    db.session.add(h)
    db.session.commit()

if __name__ == '__main__':
    from app import create_app

    app = create_app()
    
    USE_DB = True
    
    with app.app_context():
        today = pdl.now('UTC').in_timezone(current_app.config['TZ_LOCALTIME'])
        day_date, gain, loss, rec_cus_count = do_daily(today)
        if USE_DB:
            add_to_history(day_date, gain, loss, rec_cus_count)
