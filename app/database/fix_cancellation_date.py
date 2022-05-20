# app/database/fix_cancellation_date.py
from datetime import datetime, timezone
import dateutil.parser
import requests

from app import create_app, db
from flask import  current_app
from app.daos import booking_dao
from app.local_date_time import utc_to_local

"""
Some rows of the m2m-booking-system bookings table are missing cancellation date.  Need to reinsert these.

Scan the table, finding rows with the problem.  Lookup L27 using the booking_id and find the cancellation date.
Update the table.

"""

def get_l27_data(booking_id):
    url = f'https://m2m-launch27.herokuapp.com/v1/bookings/{booking_id}'
    #url = f'http://localhost:5000/v1/bookings/{booking_id}'
    headers = {
        'Authorization': 'Bearer 30cb3ab689ffbb0f0fb4fd6a146e68ba',
        'Content-Type': 'application/json'
    }
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print(f"no booking with id {booking_id}")
        return None
    return res.json()

def unmangle_datetime(val):
    try:
        if 'Z' in val:
            return dateutil.parser.isoparse(val)
        elif 'am' in val or 'pm' in val:
            return datetime.strptime(val, "%d/%m/%Y %I:%M%p")
        elif 'T' in val:
            # "2018-10-25T11:06:33+10:00"
            return datetime.strptime(val, "%Y-%m-%dT%H:%M:%S%z")
        elif ' ' in val:
            # '17/07/2020 21:01'
            return datetime.strptime(val, "%d/%m/%Y %H:%M")
        elif '/' in val:
            return datetime.strptime(val, "%d/%m/%Y")
        else:
            return datetime.strptime(val, "%Y-%m-%d")
    except (ValueError, TypeError) as e:
        print(f'unmangle_datetime error:: ({val}): {e}')

def patch_cancel_datetime(item):
    cancel_date = item._cancellation_date
    update_datetime = item._updated_at
    
    same_day = cancel_date == update_datetime.date()
    if not same_day:
        cancel_datetime = datetime(cancel_date.year, cancel_date.month, cancel_date.day, 1, 0, 0, 0, pytz.UTC)
    else:
        cancel_datetime = update_datetime.replace(tzinfo=pytz.UTC)
        
    print(f"{item.booking_id} {cancel_date=} {cancel_datetime=} update_datetime={update_datetime} {same_day=}\n")
    return cancel_datetime

def main():

    app = create_app()

    with app.app_context():
        
        res = booking_dao.get_missing_cancellations()
        
        print(f'cancellations to sort out = {len(res)}')

        for idx,item in enumerate(res):
            data = get_l27_data(item.booking_id)
            print(f'l27_cancel_date={data["cancellation"]["date"]}')
            cancellation_date_UTC = unmangle_datetime(data["cancellation"]["date"])
            cancellation_date = utc_to_local(cancellation_date_UTC).date()
            print(f"{idx:6}: {item.booking_id:6} {cancellation_date}({type(cancellation_date)})")
            
            # Update the booking table
            item.cancellation_date = cancellation_date.strftime("%Y-%m-%d")
            #db.session.commit()
 
if __name__ == '__main__':
    main()