# app/bookings/search.py

import json
from datetime import datetime
import pytz

from flask import current_app, jsonify
from app.daos import booking_dao, reservation_dao
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


if __name__ == "__main__":
    from app import create_app
    import json

    app = create_app()
    
    print('Fixing bookings in range of dates ...')
    
    with app.app_context():
        from_date_str = '2022-05-03'
        to_date_str = '2022-05-13'
        res = search_completed_bookings_by_service_date(from_date_str, to_date_str)
        print(f'Found bookings: {res}')