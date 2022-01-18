# app/bookings/views.py

import json
from datetime import datetime
import pytz

from flask import request, current_app, jsonify
from app.bookings import bookings_api
from app.decorators import APIkey_required
from psycopg2.errors import UniqueViolation
from app.notify import is_completed, notify_cancelled_completed, is_missing_booking
from app.daos import booking_dao, customer_dao
from app.local_date_time import UTC_now


@bookings_api.route('/', methods=['GET'])
@APIkey_required
def hello():
    return '<h1>M2M Booking System</h1>'


@bookings_api.route('/booking/new', methods=['POST'])
@APIkey_required
def new():
    ''' 
        return 'Hello World!' to check link.
    '''
    if not current_app.testing:
        print('Processing a new booking ...')
    
    data = json.loads(request.data)
    data["booking_status"] = 'NOT_COMPLETE'
    booking_dao.create_update_booking(data)
        
    customer_dao.create_or_update_customer(data['customer'])
    
    return 'OK'


@bookings_api.route('/booking/restored', methods=['POST'])
@APIkey_required
def restored():
    ''' 
        Should only restore a cancelled booking, therefore booking data alrerady
        in the database.
    '''
    if not current_app.testing:
        print('Processing a RESTORED booking ...')
    
    data = json.loads(request.data)
    data["booking_status"] = 'NOT_COMPLETE'
    booking_dao.create_update_booking(data)
    return 'OK'


@bookings_api.route('/booking/completed', methods=['POST'])
@APIkey_required
def completed():
    '''
        return 'Hello World!' to check link.
    '''
    if not current_app.testing:
        print('Processing a completed booking')
    
    data = json.loads(request.data)
    data["booking_status"] = 'COMPLETED'
    booking_dao.create_update_booking(data)
    
    customer_dao.create_or_update_customer(data['customer'])
     
    return 'OK'


@bookings_api.route('/booking/cancellation', methods=['POST'])
@APIkey_required
def cancellation():
    '''
        return 'Hello World!' to check link.
    '''
    if not current_app.testing:
        print('Processing a cancelled booking')
    
    data = json.loads(request.data)
    
    # In the rare case where Launch27 does not send out the booking via Zapier, this code has
    # no row on which to work.  To fix this, we will accept the data here and create the entry.
    # There is no way to generate a notification, so we can skip that step.
    if not is_missing_booking(data):
        # Generate a notification when we get a cancellation of a completed booking.
        if is_completed(data):
            notify_cancelled_completed(data)

    data["booking_status"] = 'CANCELLED'
    data["_cancellation_datetime"] = UTC_now()
    booking_dao.create_update_booking(data)
    
    customer_dao.create_or_update_customer(data['customer'])
    
    return 'OK'


@bookings_api.route('/booking/updated', methods=['POST'])
@APIkey_required
def updated():
    '''
        return 'Hello World!' to check link.
    '''
    if not current_app.testing:
        print('Processing an updated booking')

    data = json.loads(request.data)
    booking_dao.create_update_booking(data)
    
    customer_dao.create_or_update_customer(data['customer'])
    
    return 'OK'


@bookings_api.route('/booking/team_changed', methods=['POST'])
@APIkey_required
def team_changed():
    '''
        return 'Hello World!' to check link.
    '''
    if not current_app.testing:
        print('Processing an team assignment changed')
    
    data = json.loads(request.data)
    booking_dao.create_update_booking(data)
    
    ##  I think we should IGNORE this as it as triggered by a team assignment change only (that's what
    ##  one would assume by the name of the change)
    # Update the customer information table, if it has been updated since the last time it was stored
    #if 'customer' in data:
    #        customer_dao.create_or_update_customer(data['customer'])

    
    return 'OK'


@bookings_api.route('/booking', methods=['GET'])
@APIkey_required
def search():
    '''
        search through bookings.
    '''
    if not current_app.testing:
        print('Search through bookings')

    service_category = request.args.get('category')
    created_at_str = request.args.get('date')
    booking_status = request.args.get('booking_status').upper()

    created_at = datetime.strptime(created_at_str, "%Y-%m-%d")
    start_created = local_to_UTC(created_at.replace(hour=0, minute=0, second=0, microsecond=0))
    end_created = local_to_UTC(created_at.replace(hour=23, minute=59, second=59, microsecond=0))
    
    #return search_bookings(service_category, start_created, end_created, booking_status)
    
    print(f'params: category={service_category} date={start_created},{end_created} booking_status={booking_status}')
    
    res = booking_dao.search(self, service_category, booking_status, start_created, end_created)

    print(res)
    
    found = []
    for item in res:
        data = {
            "category": item.service_category,
            "name": item.name,
            "location": item.location
        }
        found.append(data.copy())
    
    return jsonify(found)

def search_bookings(service_category, start_created, end_created, booking_status):
    
    print(f'params: category={service_category} date={start_created},{end_created} booking_status={booking_status}')
    
    res = booking_dao.search(self, service_category, booking_status, start_created, end_created)
    
    print(res)
    
    found = []
    for item in res:
        data = {
            "category": item.service_category,
            "name": item.name,
            "location": item.location,
            "booking_id": item.booking_id
        }
        found.append(data.copy())
    
    return jsonify(found)
    

def local_to_UTC(d):
    local = pytz.timezone(current_app.config['TZ_LOCALTIME'])
    local_dt = local.localize(d, is_dst=current_app.config['TZ_ISDST'])
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt
