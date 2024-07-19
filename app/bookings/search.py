# app/bookings/search.py

import json
from datetime import datetime
import pytz

from flask import current_app, jsonify
from app.daos.dao_booking import booking_dao
from app.daos.dao_reservation import reservation_dao
from sqlalchemy import exc


def search_bookings(service_category, start_created, end_created, booking_status):
    
    print(f'params: category={service_category} date={start_created},{end_created} booking_status={booking_status}')
    
    try:
        if service_category == current_app.config['RESERVATION_CATEGORY']:
            res = reservation_dao.get_by_date_range(service_category, booking_status, start_created, end_created)
        else:
            res = booking_dao.get_by_date_range(service_category, booking_status, start_created, end_created)
    except exc.OperationalError as e:
        msg = {
            'status': 'fail',
            'reason': 'database is temporarily unavailable',
            'message': e
        }
        return jsonify(msg), 503
    
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

def search_completed_bookings_by_service_date(from_date_str, to_date_str):
    start_date = datetime.strptime(from_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(to_date_str, "%Y-%m-%d").date()
    
    print(f'params: from={start_date}, to={end_date}')
    
    try:
        res = booking_dao.completed_bookings_by_service_date(start_date, end_date)
    except exc.OperationalError as e:
        msg = {
            'status': 'fail',
            'reason': 'database is temporarily unavailable',
            'message': e
        }
        return jsonify(msg), 503
    
    print(f'Found bookings: {len(res)} bookings')
    
    found = []
    for item in res:
        data = {
            "booking_id": item.booking_id,
            "date_received": item.service_date,
            "service_date": item.service_date,
            "full_name": item.name,
            "email": item.email,
            "postcode": item.postcode,
            "location_name": item.location,
            "team_assigned": item.teams_assigned,
            "created_by": item.created_by,
            "service_category": item.service_category,
            "service": item.service,
            "frequency": item.frequency
        }
        found.append(data.copy())
    
    return jsonify(found)


def get_booking_by_email_service_date(email, service_date):
    row = booking_dao.get_by_booking_email_service_date_range(email, service_date)
    if row:
        res = {
            'booking_id': row.booking_id,
            'date_received': None,
            'service_date': row.service_date,
            'full_name': f"{row.first_name} {row.last_name}",
            'email': row.email,
            'rating': None,
            'comment': '',
            'postcode': row.postcode,
            'location_name': row.location,
            'team_assigned': row.teams_assigned,
            'created_by': '',
            'service_category': row.service_category,
            'service': row.service,
            'frequency': row.frequency,
        }
        return {'data': res, 'status': 'found'}
    return {'data': {}, 'status': 'not found'}


if __name__ == "__main__":
    from app import create_app
    import json

    app = create_app()
    
    print('Fixing bookings in range of dates ...')
    
    with app.app_context():
        """from_date_str = '2022-05-03'
        to_date_str = '2022-05-13'
        res = search_completed_bookings_by_service_date(from_date_str, to_date_str)
        print(f'Found bookings: {res}')"""

        print(' Get booking details from email and service_date')
        email = 'jeromeadkins1954@icloud.com'
        service_date = '2024-03-13'
        res = get_booking_by_email_service_date(email, service_date)
        print(f"{res=}")