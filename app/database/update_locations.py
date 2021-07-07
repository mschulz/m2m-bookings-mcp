# app/database/update_locations.py

import os
import json
from datetime import datetime
from app import create_app, db
from flask import  current_app
from app.models import Booking
from app.locations import get_location
from app.email import send_updated_locations_email


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
                    missing += 1
                    if postcode not in postcodes_missing:
                        postcodes_missing.add(postcode)
                else:
                    updated += 1
                    item.location = location
                    db.session.commit()
        print(f'Locations to update:{number_locations} Missing locations={missing} Updated={updated}')
        to_addr = current_app.config["MISSING_LOCATION_EMAIL"]
        send_updated_locations_email(to_addr, number_locations, updated, missing, len(postcodes_missing))
 
if __name__ == '__main__':
    main()