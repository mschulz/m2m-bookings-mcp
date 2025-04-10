# templates/missing_locations.py

import os
import json

from app import create_app, db
from flask import  current_app
from app.daos.dao_booking import booking_dao
from app.email import send_missing_location_email

missing = set()

def main():

    app = create_app()

    with app.app_context():
        
        res = booking_dao.get_bookings_missing_locations()
        number_locations = len(res)
        
        print(f'Locations missing = {number_locations}')
        
        if res:

            missing = {item.postcode for item in res if item.postcode is not None}
            missing_list = list(missing)
            number_postcodes = len(missing_list)
            
            print(f'Postcodes missing = {number_postcodes}')
            
            missing_list.sort()

            to_addr = current_app.config["MISSING_LOCATION_EMAIL"]
            msg = str(missing_list)
            send_missing_location_email(to_addr, msg, number_locations, number_postcodes)


if __name__ == '__main__':
    main()