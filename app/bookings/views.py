# app/bookings/views.py

import json
from datetime import datetime
import pytz

from flask import request, current_app, jsonify, abort
from app.bookings import bookings_api
from app.decorators import APIkey_required, catch_operational_errors
from psycopg2.errors import UniqueViolation
from app.notify import is_completed, notify_cancelled_completed, is_missing_booking
from app.daos import booking_dao, customer_dao, reservation_dao
from app.local_date_time import UTC_now
from sqlalchemy import exc
from app.bookings.search import search_bookings, search_completed_bookings_by_service_date, get_booking_by_email_service_date


def internal_meeting_booking(d):
    """
    reject outright any booking request for a meeting
    """
    if ('service_category' in d) and (d['service_category'] == 'Internal Meeting'):
        return True
    """
    reject any booking request where postcode==TBC, or TBA, with mixed cases.
    """
    postcode = d['zip'] if 'zip' in d else None
    if postcode is None or postcode.isnumeric():
        return False
    return postcode.lower() in ["tbc", "tba"]


def update_table(data, status=None, check_ndis_reservation=False, is_restored=False):
    if status:
        data["booking_status"] = status
    if data['service_category'] == current_app.config['RESERVATION_CATEGORY']:
        # Update Reservation table
        print("Update Reservation table")
        reservation_dao.create_update_booking(data)
    else:
        # Update Booking table
        print("Update Booking table")
        booking_id = data['id']
        """
        If this is an UPDATE (check_ndis_reservation is True)
        and there is an entry in the reservation table (isa_ndis_reservation(booking_id)) 
        """
        if check_ndis_reservation and reservation_dao.get_by_booking_id(booking_id):
            reservation_dao.mark_converted(booking_id)
        booking_dao.create_update_booking(data)
        if not is_restored:
            customer_dao.create_or_update_customer(data['customer'])
    return 'OK'

@bookings_api.route('/', methods=['GET'])
@APIkey_required
def hello():
    return '<h1>M2M Booking System</h1>'


@bookings_api.route('/booking/new', methods=['POST'])
@APIkey_required
@catch_operational_errors
def new():
    if not current_app.testing:
        print('Processing a new booking ...')
    
    data = json.loads(request.data)
    if internal_meeting_booking(data):
        return 'OK'
    
    return update_table(data, status='NOT_COMPLETE')


@bookings_api.route('/booking/restored', methods=['POST'])
@APIkey_required
@catch_operational_errors
def restored():
    ''' 
        Should only restore a cancelled booking, therefore booking data alrerady
        in the database.
    '''
    if not current_app.testing:
        print('Processing a RESTORED booking ...')
    
    data = json.loads(request.data)
    if internal_meeting_booking(data):
        return 'OK'
    
    return update_table(data, status='NOT_COMPLETE', is_restored=True)


@bookings_api.route('/booking/completed', methods=['POST'])
@APIkey_required
@catch_operational_errors
def completed():
    '''
        return 'Hello World!' to check link.
    '''
    if not current_app.testing:
        print('Processing a completed booking')
    
    data = json.loads(request.data)
    if internal_meeting_booking(data):
        return 'OK'
    
    #print(f"team_details:: {data['team_details']}")
    #print(data)
    
    return update_table(data, status='COMPLETED')


@bookings_api.route('/booking/cancellation', methods=['POST'])
@APIkey_required
@catch_operational_errors
def cancellation():
    '''
        return 'Hello World!' to check link.
    '''
    if not current_app.testing:
        print('Processing a cancelled booking')
    
    data = json.loads(request.data)
    if internal_meeting_booking(data):
        return 'OK'
    
    #print(f"team_details:: {data['team_details']}")
    #Customer data received:print(data)
    
    # In the rare case where Launch27 does not send out the booking via Zapier, this code has
    # no row on which to work.  To fix this, we will accept the data here and create the entry.
    # There is no way to generate a notification, so we can skip that step.
    if not is_missing_booking(data):
        # Generate a notification when we get a cancellation of a completed booking.
        if is_completed(data):
            notify_cancelled_completed(data)

    data["_cancellation_datetime"] = UTC_now()
    return update_table(data, status='CANCELLED')


@bookings_api.route('/booking/updated', methods=['POST'])
@APIkey_required
@catch_operational_errors
def updated():
    '''
        return 'Hello World!' to check link.
    '''
    if not current_app.testing:
        print('Processing an updated booking')

    data = json.loads(request.data)
    if internal_meeting_booking(data):
        return 'OK'
    
    #print(f"team_details:: {data['team_details']}")
    #print(data)

    return update_table(data, check_ndis_reservation=True)


@bookings_api.route('/booking/team_changed', methods=['POST'])
@APIkey_required
@catch_operational_errors
def team_changed():
    '''
        return 'Hello World!' to check link.
    '''
    if not current_app.testing:
        print('Processing an team assignment changed')
    
    data = json.loads(request.data)
    if internal_meeting_booking(data):
        return 'OK'
    
    #print(f"team_details:: {data['team_details']}")
    #print(data)

    return update_table(data, is_restored=True)


@bookings_api.route('/booking', methods=['GET'])
@APIkey_required
@catch_operational_errors
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


@bookings_api.route('/booking/<int:booking_id>', methods=['GET'])
@APIkey_required
@catch_operational_errors
def get_booking_details(booking_id):
    '''
        search through bookings.
    '''
    if not current_app.testing:
        print('Select one booking')

    res = booking_dao.get_by_booking_id(booking_id)
    return res.to_json()


@bookings_api.route('/booking/was_new_customer/<int:booking_id>', methods=['GET'])
@APIkey_required
@catch_operational_errors
def get_a_booking(booking_id):
    '''
        search through bookings.
    '''
    if not current_app.testing:
        print('Select one booking')

    res = booking_dao.get_by_booking_id(booking_id)
    if not res:
        # If the customer is not in this table they are probably a reservation.
        # Just drop the was_new_customer as False
        val = {"was_new_customer": False }
    else:
        val = {"was_new_customer": res.was_new_customer if hasattr(res, "was_new_customer") else False }
    return jsonify(val)


@bookings_api.route('/booking/search', methods=['GET'])
@APIkey_required
@catch_operational_errors
def search_by_dates():
    '''
        search through bookings.
    '''
    if not current_app.testing:
        print('Search through bookings within date range')

    start_date_str = request.args.get('from')
    end_date_str = request.args.get('to')
    
    return search_completed_bookings_by_service_date(start_date_str, end_date_str)


@bookings_api.route('/booking/service_date', methods=['GET'])
@APIkey_required
@catch_operational_errors
def search_by_service_date_and_email():
    '''
        search through bookings.
    '''
    if not current_app.testing:
        print('Search through bookings within date range')

    service_date = request.args.get('service_date')
    email = request.args.get('email')
    
    res = get_booking_by_email_service_date(email, service_date)
    return jsonify(res)


