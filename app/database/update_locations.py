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
        
        print(f'booking ids to sort out = {len(res)}')
        
        if res:

            for item in res:
                postcode = item.postcode
                location = get_location(postcode)
                
                print(f"{postcode} => {location}")
                
                item.location = location
                db.session.commit()
 
if __name__ == '__main__':
    main()