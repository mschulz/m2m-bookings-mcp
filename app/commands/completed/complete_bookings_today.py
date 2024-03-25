# complete_bookings_today.py

import os
import requests
import datetime
import pytz
import sys

from flask import Flask, current_app
from flask_mail import Mail
from app.logger import setup_logging
from app.email import send_completed_bookings_email
from app.commands.completed.booking import Booking


def create_app():
    app = Flask(__name__)
    app.config.from_object(os.environ['APP_SETTINGS'])    

    #initialise the logger
    setup_logging(app)
    app.logger.info(f'{app.config["APP_NAME"]} startup')

    # Set up mail
    mail.init_app(app)

    return app
    
#
#   Here is the operating code
#
if len(sys.argv) != 2:
    print('Missing argument for timezone name: AEST,ACST,AWST')
    sys.exit(1)
tz_name = sys.argv[1]
#print(f'tz_name={tz_name}')

mail = Mail()
app = create_app()

with app.app_context():

    setup_logging(app)

    tz = pytz.timezone(app.config['TZ_LOCALTIME'])
    today_date_string =  datetime.datetime.now(tz).date().strftime("%Y-%m-%d")
    
    completed_count = tz_count = 0
    b = Booking()
    booking_id_list = b.get_all_in_tz(today_date_string, tz_name)
    
    #print(f"get_all_booking_ids: {booking_id_list}")
    
    if booking_id_list is not None:
        tz_count = len(booking_id_list)
        
        # Complete each booking and increment completed_count, unless already completed
        for i in booking_id_list:
            completed_count += b.complete(i)
            print(f'completed: {i}')
            
    msg = f'complete_bookings_today:: {completed_count} bookings marked as completed out of {tz_count}({tz_name})'
    app.logger.info(msg)
    # Notify staff of how many bookings were actually marked complete
    toaddr = app.config['OVERRIDE_ADDR']
    send_completed_bookings_email(toaddr, completed_count, tz_count, tz_name)
        