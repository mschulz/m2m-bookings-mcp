# app/database/missing_locations.py

import os
import json

from app import create_app, db
from flask import  current_app
from app.models import Booking
from app.email import send_missing_location_email

missing = set()

def main():

    app = create_app()

    with app.app_context():
        
        res = db.session.query(Booking).filter(Booking.location == None).all()
        number_locations = len(res)
        
        print(f'Locations missing = {number_locations}')
        
        if res:

            for item in res:
                postcode = item.postcode
                
                missing.add(postcode)

            missing_list = list(missing)
            number_postcodes = len(missing_list)
            
            print(f'Postcodes missing = {number_postcodes}')
            
            missing_list.sort()

            to_addr = current_app.config["MISSING_LOCATION_EMAIL"]
            msg = str(missing_list)
            send_missing_location_email(to_addr, msg, number_locations, number_postcodes)


if __name__ == '__main__':
    main()