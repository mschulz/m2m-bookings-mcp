# /app/database/backfill.py

"""
	A run-once program to calculate historical data and store in a table in the database.
		date, today gain, today loss, today nett, recurring count
"""

import json
from datetime import datetime, date
import pendulum as pdl

from flask import current_app
from app import db
from app.daos import booking_dao
from sqlalchemy import exc

from app.commands.model import History


def is_end_of_month(today):
    days_in_month = today.days_in_month
    day_today = int(today.format('DD'))
    return days_in_month == day_today

def get_today_nett(today):
    start_created = today.start_of('day')
    end_created = today.end_of('day')
    today_gain, today_loss = booking_dao.gain_cancelled_in_range(start_created, end_created)
    nett = today_gain - today_loss
    return nett

def backfill_data(today, use_db=True):
    # Start of historical data
    local_timezone = pdl.timezone(current_app.config['TZ_LOCALTIME'])
    begin_datetime_local = pdl.datetime(2020,6,1,tz=local_timezone)
    begin_datetime_utc = begin_datetime_local.in_timezone('UTC').start_of('day')

    # Today figures
    #  This program runs in the early hours of the FOLLOWING day, so we need to correct for this
    start_created = today.start_of('day').subtract(days=1).in_timezone('utc')
    end_created = today.end_of('day').subtract(days=1).in_timezone('utc')
    
    # Reset recurring_customer_count to the recurring_customer_count now less the todays_nett from midnight last night
    # This SHOULD give us the recurring customer count at midnight yesterday.
    recurring_customer_count = booking_dao.recurring_current() # this include nett since midnight last night
    recurring_customer_count -= get_today_nett(today)
    
    while start_created >= begin_datetime_utc:
        today_gain, today_loss = booking_dao.gain_cancelled_in_range(start_created, end_created)
        nett_for_day = today_gain - today_loss
        
        is_saturday = start_created.day_of_week == 6
        is_eom = is_end_of_month(start_created)
        
    
        day_date = start_created.in_timezone(current_app.config['TZ_LOCALTIME']).date()

        
        if use_db:
            h = History()
            h.day_date = day_date
            h.gain = today_gain
            h.loss = today_loss
            h.nett = nett_for_day
            h.recurring = recurring_customer_count
            h.is_saturday = is_saturday
            h.is_eom = is_eom
            db.session.add(h)
        else:
            print(day_date, today_gain, today_loss, nett_for_day, recurring_customer_count, is_saturday, is_eom)

        # Move to previous day for next calculation
        start_created = start_created.subtract(days=1)
        end_created = end_created.subtract(days=1)
        recurring_customer_count -= nett_for_day
    if use_db:
        db.session.commit()
    

if __name__ == '__main__':
    from app import create_app
    import sys

    app = create_app()
    USE_DB = True
    
    with app.app_context():
        # Create a new History table
        if USE_DB:
            try:
                History.__table__.drop(db.engine)
                print('Dropped History table')
            except exc.ProgrammingError:
                    pass # No table to delete
            History.__table__.create(db.session.bind, checkfirst=True)
            try:
                db.session.query(History).delete()
                db.session.commit()
                print('All rows of History deleted')
            except:
                db.session.rollback()
                print('Failed to delete all rows of History -- exiting')
                sys.exit(1)
        today = pdl.now('UTC').in_timezone(current_app.config['TZ_LOCALTIME'])
        print(f'{today=}')
        backfill_data(today, use_db=USE_DB)
