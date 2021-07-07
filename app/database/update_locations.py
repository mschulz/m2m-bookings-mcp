# app/database/update_locations.py

import os
import json
from datetime import datetime
from app import create_app, db
from flask import  current_app
from app.models import Booking
from app.locations import get_location
#from sqlalchemy import exc


def main():

    app = create_app()

    with app.app_context():
        
        res = db.session.query(Booking).filter(Booking.location == None).all()
        number_locations = len(res)
        
        print(f'Bookings with no locations to update = {number_locations}')
        
        missing = 0
        updated = 0
        postcodes_missing = set()
        
        if res:
            for item in res:
                postcode = item.postcode
                location = get_location(postcode)
                
                if location is None:
                    print(f"{postcode} => {location}")
                    if postcode not in postcodes_missing:
                        missing += 1
                        postcodes_missing.add(postcode)
                else:
                    updated += 1
                    item.location = location
                    db.session.commit()
                
        to_addr = current_app.config["MISSING_LOCATION_EMAIL"]
        msg = str(missing_list)
        to_addr = current_app.config["SUPPORT_EMAIL"]
        send_updated_locations_email(to_addr, update, missing, len(postcodes_missing))
 
if __name__ == '__main__':
    main()