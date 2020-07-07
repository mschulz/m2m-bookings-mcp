# app/bookings/views.py

import json
from flask import request, current_app, abort
from app import db
from app.bookings import bookings_api
from app.decorators import APIkey_required
from app.email import send_success_email
from app.models import Booking, import_dict


def process_booking_data(data):
    booking_id = data['id'] if 'id' in data else None
    
    if not booking_id:
        # This is a malformed set of data (this test might be redundant)
        current_app.logger.error("booking has no booking - ignore this data")
        abort(422)
    
    current_app.logger.info(f'Booking data received: {data}')
    
    # Check if we already have a booking under this id
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
    db.session.add(b)
    try:
        db.session.commit()
    except sqlalchemy.exc.DataError as e:
        current_app.logger.info(f'({request.path}) Booking error in model data: {e}')
        m = current_app.config['SUPPORT_EMAIL'].split('@')
        send_error_email(f"{m[0]}+error@{m[1]}", e)
        abort(422)
    

def process_customer_data(data):
    # Update the customer information table, if it has been updated since the last time it was stored
    current_app.logger.info(f'Customer data received: {data}')

    c = db.session.query(Customer).filter(Customer.customer_id == data['id']).first()
    if c is None:
        # Nothing stored about this customer, so create a new row in the table
        c = Customer()
        import_customer(c, data)
        db.session.add(c)
        current_app.logger.info(f'Create row for new customer data')
    else:
        # Check if there is updated data in the customer fields
        # First get the updated_at time from the stored data
        stored_update_time = c.updated_at
        import_customer(c, data)
        new_update_time = c.updated_at
        
        # Check if the data has been updated since the last time it was stored in the table
        if stored_update_time != new_update_time:
            try:
                db.session.commit()
                current_app.logger.info(f'({request.path}) Updated Customer data')
            except sqlalchemy.exc.DataError as e:
                current_app.logger.info(f'({request.path}) Customer error in model data: {e}')
                m = current_app.config['SUPPORT_EMAIL'].split('@')
                send_error_email(f"{m[0]}+error@{m[1]}", e)
                abort(422)
        else:
            current_app.logger.info(f'No change to customer data')


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
    
    current_app.logger.info(f'Booking data received: {b.to_dict()}')
    
    # Load the database table
    db.session.add(b)
    try:
        db.session.commit()
    except sqlalchemy.exc.DataError as e:
        current_app.logger.info(f'({request.path}) Booking error in model data: {e}')
        m = current_app.config['SUPPORT_EMAIL'].split('@')
        send_error_email(f"{m[0]}+error@{m[1]}", e)
        abort(422)
    
    # Update the customer information table, if it has been updated since the last time it was stored
    if 'customer' in data:
        process_customer_data(data['customer'])
    
    return 'OK'


@bookings_api.route('/booking/completed', methods=['POST'])
@APIkey_required
def completed():
    '''
        return 'Hello World!' to check link.
    '''
    print('Processing a completed booking')
    
    data = json.loads(request.data)
    
    # Extract the booking data and update appropriate row in booking table
    process_booking_data(data)
    
    # Update the customer information table, if it has been updated since the last time it was stored
    if 'customer' in data:
        process_customer_data(data['customer'])
     
    return 'OK'


@bookings_api.route('/booking/cancellation', methods=['POST'])
@APIkey_required
def cancellation():
    '''
        return 'Hello World!' to check link.
    '''
    print('Processing a cancelled booking')
    
    data = json.loads(request.data)
    
    # Extract the booking data and update appropriate row in booking table
    process_booking_data(data)
    
    # Update the customer information table, if it has been updated since the last time it was stored
    if 'customer' in data:
        process_customer_data(data['customer'])
    
    return 'OK'


@bookings_api.route('/booking/updated', methods=['POST'])
@APIkey_required
def updated():
    '''
        return 'Hello World!' to check link.
    '''
    data = json.loads(request.data)
    
    # Extract the booking data and update appropriate row in booking table
    process_booking_data(data)
    
    # Update the customer information table, if it has been updated since the last time it was stored
    if 'customer' in data:
        process_customer_data(data['customer'])
    
    return 'OK'


@bookings_api.route('/booking/team_changed', methods=['POST'])
@APIkey_required
def team_changed():
    '''
        return 'Hello World!' to check link.
    '''
    print('Processing an team assignment changed')
    
    data = json.loads(request.data)
    
    # Extract the booking data and update appropriate row in booking table
    process_booking_data(data)
    
    # Update the customer information table, if it has been updated since the last time it was stored
    if 'customer' in data:
        process_customer_data(data['customer'])
    
    return 'OK'


