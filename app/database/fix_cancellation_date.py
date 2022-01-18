# app/database/fix_cancellation_date.py

from app import create_app, db
from flask import  current_app
from app.daos import booking_dao

from datetime import datetime, timezone
import pytz


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
        
        res = booking_dao.get_cancellations()
        
        print(f'cancellations to sort out = {len(res)}')

        for idx,item in enumerate(res):
            item._cancellation_datetime = patch_cancel_datetime(item)
            db.session.commit()
 
if __name__ == '__main__':
    main()