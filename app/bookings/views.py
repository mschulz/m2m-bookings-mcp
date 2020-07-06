# app/bookings/views.py

import json
from flask import request, current_app, abort
from app import db
from app.bookings import bookings_api
from app.decorators import APIkey_required
from app.email import send_success_email
from app.models import Booking, import_dict


@bookings_api.route('/booking/new', methods=['POST'])
@APIkey_required
def new():
    ''' 
        return 'Hello World!' to check link.
    '''
    print('Processing a new booking ...')
    
    data = json.loads(request.data)
    
    b = Booking()
    import_dict(b, data)
    
    current_app.logger.info(f'Data received: {b.to_dict()}')
    
    # Load the database table
    db.session.add(b)
    db.session.commit()
    
    # Check which keys were sent and not processed by 'import_dict'
    # print('Keys of data from zapier not processed from:')
    # print(f'{json.loads(data).keys() - d.keys()}')
    
    send_success_email(current_app.config['SUPPORT_EMAIL'])
    
    return 'OK'


@bookings_api.route('/booking/completed', methods=['POST'])
@APIkey_required
def completed():
    '''
        return 'Hello World!' to check link.
    '''
    print('Processing a completed booking')
    
    data = json.loads(request.data)
    
    booking_id = data['id'] if 'id' in data.keys() else None
    
    if not booking_id:
        # Haven't seen the original booking - add it now
        current_app.logger.error("booking has no booking - ignore this data")
        abort(422)
    
    b = db.session.query(Booking).filter(Booking.booking_id == booking_id).first()
    
    if b is None:
        # Haven't seen the original booking - add it now
        current_app.logger.error("haven't seen this booking - adding to database")
    
        # Load the database table
        b = Booking()
        import_dict(b, data)
        db.session.add(b)
    else:
    
        import_dict(b, data)
    
    current_app.logger.info(f'Data loaded into database: {b.to_dict()}')
    
    # Load the database table
    db.session.commit()
    
    send_success_email(current_app.config['SUPPORT_EMAIL'])
    
    return 'OK'


@bookings_api.route('/booking/cancellation', methods=['POST'])
@APIkey_required
def cancellation():
    '''
        return 'Hello World!' to check link.
    '''
    print('Processing a cancelled booking')
    
    data = json.loads(request.data)
    
    booking_id = data['id'] if 'id' in data.keys() else None
    
    if not booking_id:
        # Haven't seen the original booking - add it now
        current_app.logger.error("booking has no booking - ignore this data")
        abort(422)
    
    b = db.session.query(Booking).filter(Booking.booking_id == booking_id).first()
    
    if b is None:
        # Haven't seen the original booking - add it now
        current_app.logger.error("haven't seen this booking - adding to database")
    
        # Load the database table
        b = Booking()
        import_dict(b, data)
        db.session.add(b)
    else:
    
        import_dict(b, data)
    
    current_app.logger.info(f'Data loaded into database: {b.to_dict()}')
    
    # Load the database table
    db.session.commit()
    
    send_success_email(current_app.config['SUPPORT_EMAIL'])
    
    return 'OK'


@bookings_api.route('/booking/updated', methods=['POST'])
@APIkey_required
def updated():
    '''
        return 'Hello World!' to check link.
    '''
    print('Processing an updated booking')
    
    data = json.loads(request.data)
    
    booking_id = data['id'] if 'id' in data.keys() else None
    
    if not booking_id:
        current_app.logger.error("booking has no booking - ignore this data")
        abort(422)
    
    b = db.session.query(Booking).filter(Booking.booking_id == booking_id).first()
    
    import_dict(b, data)
    
    current_app.logger.info(f'Data received: {b.to_dict()}')
    
    # Load the database table
    db.session.commit()
   
    send_success_email(current_app.config['SUPPORT_EMAIL'])
    
    return 'OK'


@bookings_api.route('/booking/team_changed', methods=['POST'])
@APIkey_required
def team_changed():
    '''
        return 'Hello World!' to check link.
    '''
    print('Processing an team assignment changed')
    
    data = json.loads(request.data)
    
    booking_id = data['id'] if 'id' in data.keys() else None
    
    if not booking_id:
        # Haven't seen the original booking - add it now
        current_app.logger.error("booking has no booking - ignore this data")
        abort(422)
    
    b = db.session.query(Booking).filter(Booking.booking_id == booking_id).first()
    
    if b is None:
        # Haven't seen the original booking - add it now
        current_app.logger.error("haven't seen this booking - adding to database")
    
        # Load the database table
        b = Booking()
        import_dict(b, data)
        db.session.add(b)
    else:
    
        import_dict(b, data)
    
    current_app.logger.info(f'Data loaded into database: {b.to_dict()}')
    
    # Load the database table
    db.session.commit()
    
    send_success_email(current_app.config['SUPPORT_EMAIL'])
    
    return 'OK'


