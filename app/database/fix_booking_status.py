# app/database/fix_booking_status.py

import os
import json
import csv

from app import create_app, db
from flask import  current_app
from app.models import Booking


def fix_status(s):
    return s.upper().replace(' ', '_')

def main():

    app = create_app()

    with app.app_context():
        # Read in the CSV file and convert it to a dictionary
        reader = csv.reader(open('/Users/markschulz/Projects/maid2match/m2m-booking-system/app/database/ids_to_status2.csv', 'r'))
        headers = next(reader)
        
        d = {}
        for row in reader:
            key = int(row[0])
            val = fix_status(row[1])
            d[key] = val
            #print(f"{key}: {val}")
            
        res = db.session.query(Booking).filter(Booking.booking_status == None).all()
        
        print(f'booking ids to sort out = {len(res)}')
        
        if res:
            for item in res:
                print(f'id: {item.booking_id} status: {d[item.booking_id]}')
                item.booking_status = d[item.booking_id]
            
            db.session.commit()
 
if __name__ == '__main__':
    main()