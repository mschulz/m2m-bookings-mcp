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


class History(db.Model):
    __tablename__ = 'history'
    
    id = db.Column(db.Integer, primary_key=True)
    
    day_date = db.Column(db.Date, index=False, unique=False)
    gain = db.Column(db.Integer, index=False, unique=False)
    loss = db.Column(db.Integer, index=False, unique=False)
    nett = db.Column(db.Integer, index=False, unique=False)
    recurring = db.Column(db.Integer, index=False, unique=False)
    
    def __repr__(self):
        return f'<History {day_date} {nett} {recurring}>'
    
    def import_dict(self, d):
        self.day_date


def gain_loss_in_range(start_date, end_date):
    # Need to convert from Pendulum datetime to datetime.datetime format
    start_created = datetime.fromtimestamp(start_date.timestamp(), pdl.tz.UTC)
    end_created = datetime.fromtimestamp(end_date.timestamp(), pdl.tz.UTC)
    
    gain = booking_dao.get_gain_in_date_range(start_created, end_created)
    loss = booking_dao.get_loss_in_date_range(start_created, end_created)
    return gain, loss

def backfill_data():
    # Start of historical data
    local_timezone = pdl.timezone(current_app.config['TZ_LOCALTIME'])
    begin_datetime_local = pdl.datetime(2020,6,1,tz=local_timezone)
    begin_datetime_utc = begin_datetime_local.in_timezone('UTC').start_of('day')

    # Today figures
    #  This program runs in the early hours of the FOLLOWING day, so we need to correct for this
    recurring_customer_count = booking_dao.recurring_current()
    today = pdl.now('UTC').in_timezone(current_app.config['TZ_LOCALTIME'])
    start_created = today.start_of('day')
    end_created = today.end_of('day')

    while start_created >= begin_datetime_utc:
        today_gain, today_loss = gain_loss_in_range(start_created, end_created)
        nett_for_day = today_gain - today_loss
        print(start_created.date(), today_gain, today_loss, nett_for_day, recurring_customer_count)
        h = History()
        h.day_date = start_created.date()
        h.gain = today_gain
        h.loss = today_loss
        h.nett = nett_for_day
        h.recurring = recurring_customer_count
        db.session.add(h)

        # Move to previous day for next calculation
        start_created = start_created.subtract(days=1)
        end_created = end_created.subtract(days=1)
        recurring_customer_count -= nett_for_day
    db.session.commit()
    

if __name__ == '__main__':
    from app import create_app

    app = create_app()
    
    with app.app_context():
        # Create a new History table
        try:
            History.__table__.drop(db.engine)
        except exc.ProgrammingError:
                pass # No table to delete
        History.__table__.create(db.session.bind)
        
        backfill_data()
