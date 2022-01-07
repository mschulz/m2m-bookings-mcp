# app/notify.py

import json
import requests
from flask import current_app, abort
from app import db
from app.models import Booking
from app.email import send_warning_email


def is_missing_booking(data):
    """ Check if this about to be cancelled booking is actually in the database. """
    booking_id = data['id'] if 'id' in data else None
    
    if not booking_id:
        # This is a malformed set of data (this test might be redundant)
        current_app.logger.error("booking has no booking_id - ignore this data")
        abort(422, "booking has no booking_id - ignore this data")
    
    current_app.logger.info(f'Booking data received: {data}')
    
    # Check if we already have a booking under this id
    b = db.session.query(Booking).filter(Booking.booking_id == booking_id).first()
    
    return b is None

def is_completed(data):
    """ Check if this about to be cancelled booking is already marked as completed. """
    booking_id = data['id'] if 'id' in data else None
    
    # Check if we already have a booking under this id
    b = db.session.query(Booking).filter(Booking.booking_id == booking_id).first()
    
    return b.booking_status == "COMPLETED"

def notify_cancelled_completed(data):
    """ send this data to the notification webhook. """
    url = current_app.config['NOTIFICATION_URL']
    data['APP_NAME'] = current_app.config['APP_NAME']
    headers = {
        'content-type': "application/json"
    }
    
    response = requests.post(url, data=json.dumps(data), headers=headers)
    
    if response.status_code != 200:
        toaddr = current_app.config['SUPPORT_EMAIL']
        error_msg = f'Notification returned status_code={response.status_code}\n{data}'
        send_warning_email(toaddr, error_msg)