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
from sqlalchemy import exc
from app.bookings.search import search_bookings, search_completed_bookings_by_service_date

def reject_booking(d):
    """
    reject any booking request where postcode==TBC.
    """
    return d['zip'] in ['TBC']


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
    
    if reject_booking(data):
        return 'OK'

    data["booking_status"] = 'NOT_COMPLETE'
    
    try:
        booking_dao.create_update_booking(data)
        customer_dao.create_or_update_customer(data['customer'])
    except exc.OperationalError as e:
        msg = {
            'status': 'fail',
            'reason': 'database is temporarily unavailable',
            'message': e
        }
        return jsonify(msg), 503
    
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
    
    if reject_booking(data):
        return 'OK'
    
    data["booking_status"] = 'NOT_COMPLETE'
    try:
        booking_dao.create_update_booking(data)
    except exc.OperationalError as e:
        msg = {
            'status': 'fail',
            'reason': 'database is temporarily unavailable',
            'message': e
        }
        return jsonify(msg), 503
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
    
    if reject_booking(data):
        return 'OK'
    
    data["booking_status"] = 'COMPLETED'
    try:
        booking_dao.create_update_booking(data)
        customer_dao.create_or_update_customer(data['customer'])
    except exc.OperationalError as e:
        msg = {
            'status': 'fail',
            'reason': 'database is temporarily unavailable',
            'message': e
        }
        return jsonify(msg), 503
    
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
    
    if reject_booking(data):
        return 'OK'
    
    # In the rare case where Launch27 does not send out the booking via Zapier, this code has
    # no row on which to work.  To fix this, we will accept the data here and create the entry.
    # There is no way to generate a notification, so we can skip that step.
    if not is_missing_booking(data):
        # Generate a notification when we get a cancellation of a completed booking.
        if is_completed(data):
            notify_cancelled_completed(data)

    data["booking_status"] = 'CANCELLED'
    data["_cancellation_datetime"] = UTC_now()
    
    print(f'{data["_cancellation_datetime"]=}')
    
    try:
        booking_dao.create_update_booking(data)
        customer_dao.create_or_update_customer(data['customer'])
    except exc.OperationalError as e:
        msg = {
            'status': 'fail',
            'reason': 'database is temporarily unavailable',
            'message': e
        }
        return jsonify(msg), 503
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
    
    if reject_booking(data):
        return 'OK'
    
    try:
        booking_dao.create_update_booking(data)
        customer_dao.create_or_update_customer(data['customer'])
    except exc.OperationalError as e:
        msg = {
            'status': 'fail',
            'reason': 'database is temporarily unavailable',
            'message': e
        }
        return jsonify(msg), 503
    
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
    
    if reject_booking(data):
        return 'OK'
    try:
        booking_dao.create_update_booking(data)
    except exc.OperationalError as e:
        msg = {
            'status': 'fail',
            'reason': 'database is temporarily unavailable',
            'message': e
        }
        return jsonify(msg), 503
    
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
    
    return search_bookings(service_category, start_created, end_created, booking_status)


@bookings_api.route('/booking/search', methods=['GET'])
@APIkey_required
def search_by_dates():
    '''
        search through bookings.
    '''
    if not current_app.testing:
        print('Search through bookings within date range')

    start_date_str = request.args.get('from')
    end_date_str = request.args.get('to')
    
    return search_completed_bookings_by_service_date(start_date_str, end_date_str)

