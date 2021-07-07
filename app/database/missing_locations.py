# app/database/missing_locations.py

import os
import json

from app import create_app, db
from flask import  current_app
from app.models import Booking

missing = set()

def main():

    app = create_app()

    with app.app_context():
        
        res = db.session.query(Booking).filter(Booking.location == None).all()
        
        print(f'Locations missing = {len(res)}')
        
        if res:

            for item in res:
                postcode = item.postcode
                
                missing.add(postcode)
        
            print(f'Postcodes with no Locations for {current_app.config["COMPANY_NAME"]}\n{missing}')
        


if __name__ == '__main__':
    main()