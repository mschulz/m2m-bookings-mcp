# app/notify.py

import json
import requests
from flask import current_app, abort
from app.email import send_warning_email
from app.daos import booking_dao, customer_dao


def is_missing_booking(data):
    """ Check if this about to be cancelled booking is actually in the database. """
    booking_id = data['id'] if 'id' in data else None
    
    if not booking_id:
        # This is a malformed set of data (this test might be redundant)
        current_app.logger.error("booking has no booking_id - ignore this data")
        abort(422, description="booking has no booking_id - ignore this data")
    
    current_app.logger.info(f'Booking data received: {data}')
    
    # Check if we already have a booking under this id
    b = get_by_booking_id(booking_id)
    
    return b is None

def is_completed(data):
    """ Check if this about to be cancelled booking is already marked as completed. """
    booking_id = data['id'] if 'id' in data else None
    if not booking_id:
        return False
    # Check if we already have a booking under this id
    b = get_by_booking_id(booking_id)
    
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