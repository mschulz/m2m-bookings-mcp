# app/bookings/views.py

import json
from flask import request, current_app, abort
from app import db
from app.bookings import bookings_api
from app.decorators import APIkey_required
from app.email import send_success_email
from app.models import Booking, import_dict, Customer, import_customer
from sqlalchemy import exc
from psycopg2.errors import UniqueViolation
from app.email import send_error_email


def process_booking_data(data):
    booking_id = data['id'] if 'id' in data else None
    
    if not booking_id:
        # This is a malformed set of data (this test might be redundant)
        current_app.logger.error("booking has no booking_id - ignore this data")
        abort(422)
    
    current_app.logger.info(f'Booking data received: {data}')
    
    # Check if we already have a booking under this id
    b = db.session.query(Booking).filter(Booking.booking_id == booking_id).first()
    
    if b is None:
        # Haven't seen the original booking - ADD it now
        current_app.logger.info("haven't seen this booking - ADDING to database")
    
        # Load the database table
        b = Booking()
        import_dict(b, data)
        db.session.add(b)
    else:
        # Have seen the original booking - UPDATE it now
        current_app.logger.info("have seen this booking - UPDATING database")
    
        import_dict(b, data)
    
    current_app.logger.info(f'Loading ... Name: "{b.name}" team: "{b.teams_assigned}" booking_id: {b.booking_id}')
    
    try:
        db.session.commit()
        current_app.logger.info(f'Data loaded into database: {b.to_dict()}')
    except exc.DataError as e:
        db.session.rollback()
        current_app.logger.info(f'Data attempted to load into database: {b.to_dict()}')
        current_app.logger.info(f'({request.path}) Booking error in model data: {e}')
        m = current_app.config['SUPPORT_EMAIL'].split('@')
        send_error_email(f"{m[0]}+error@{m[1]}", e)
        abort(422)
    except exc.IntegrityError as e:
        db.session.rollback()
        
        # Check if this record is the same as the existing one.  `If so, ignore it
        updated_at = b.updated_at.replace(tzinfo=None)

        bb = db.session.query(Booking).filter(Booking.booking_id == b.booking_id).first()
        orig_updated_at = bb.updated_at
    
        if orig_updated_at == updated_at:
            current_app.logger.info(f'Data is a duplicated of database record.  This copy ignored.')
        else:
            # this new data is NOT the same as that in the database
            if isinstance(e.orig, UniqueViolation):
                #this often occurs when a team is assigned.  This generates two messages:
                #  One is the team assigment is changed; and
                #  one is the booking updated
                # if there is no prior booking, then both are 'new' rows in the table with the same 
                # booking_id.
                # We could try to fix this in the following way:
                #  the second one to attempt creating the new record ends up here iwth this exception.
                #  we have rolled back the attempt so noe we could try just ADDing the data
                #   if that fails, then abort the attempt.

                import_dict(b, data)
    
                try:
                    db.session.commit()
                    current_app.logger.info('Second attempt to load data loaded into database')
                    return
                except exc.IntegrityError as e:
                    db.session.rollback()
            
                current_app.logger.info(f'({request.path}) Possible timing error (retry via Zapier): {e.orig}')
                m = current_app.config['SUPPORT_EMAIL'].split('@')
                send_error_email(f"{m[0]}+error@{m[1]}", e)
                abort(500)
            # Capture all other errors
            db.session.rollback()
            current_app.logger.info(f'({request.path}) psycopg2 error (retry via Zapier): {e}')
            m = current_app.config['SUPPORT_EMAIL'].split('@')
            send_error_email(f"{m[0]}+error@{m[1]}", e)
            abort(500)
    return


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
        if stored_update_time == new_update_time:
            current_app.logger.info(f'No change to customer data')
            return
    try:
        db.session.commit()
        current_app.logger.info(f'({request.path}) Updated Customer data')
    except exc.DataError as e:
        db.session.rollback()
        current_app.logger.info(f'({request.path}) Customer error in model data: {e}')
        m = current_app.config['SUPPORT_EMAIL'].split('@')
        send_error_email(f"{m[0]}+error@{m[1]}", e)
        abort(422)


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
    
    b = Booking()
    import_dict(b, data)
    
    current_app.logger.info(f'Booking data received: {b.to_dict()}')
    
    # Load the database table
    db.session.add(b)
    try:
        db.session.commit()
    except exc.DataError as e:
        current_app.logger.error(f'({request.path}) Booking error in model data: {e}')
        m = current_app.config['SUPPORT_EMAIL'].split('@')
        send_error_email(f"{m[0]}+error@{m[1]}", e)
        abort(422)
    except exc.IntegrityError as e:
        db.session.rollback()
        
        # Check if this record is the same as the existing one.  `If so, ignore it
        updated_at = b.updated_at.replace(tzinfo=None)

        bb = db.session.query(Booking).filter(Booking.booking_id == b.booking_id).first()
        orig_updated_at = bb.updated_at
    
        if orig_updated_at == updated_at:
            current_app.logger.info(f'Data is a duplicated of database record.  This copy ignored.')
        else:
            # this new data is NOT the same as that in the database
            if isinstance(e.orig, UniqueViolation):
                # let's try just updating the database??
           
                import_dict(b, data)

                try:
                    db.session.commit()
                    current_app.logger.error('Second attempt to load data loaded into database')
                except exc.IntegrityError as e:
                    db.session.rollback()
                    current_app.logger.error(f'({request.path}) Possible timing error (retry via Zapier): {e.orig}')
                    m = current_app.config['SUPPORT_EMAIL'].split('@')
                    send_error_email(f"{m[0]}+error@{m[1]}", e)
                    abort(500)
            else:
                db.session.rollback()
                current_app.logger.error(f'({request.path}) Possible timing error (retry via Zapier): {e.orig}')
                m = current_app.config['SUPPORT_EMAIL'].split('@')
                send_error_email(f"{m[0]}+error@{m[1]}", e)
                abort(500)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'({request.path}) Unknown error: {e.orig}')
        m = current_app.config['SUPPORT_EMAIL'].split('@')
        send_error_email(f"{m[0]}+error@{m[1]}", e)
        abort(500)
        
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
    if not current_app.testing:
        print('Processing a completed booking')
    
    data = json.loads(request.data)
    data["booking_status"] = 'COMPLETED'
    
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
    if not current_app.testing:
        print('Processing a cancelled booking')
    
    data = json.loads(request.data)
    data["booking_status"] = 'CANCELLED'
    
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
    if not current_app.testing:
        print('Processing an updated booking')

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
    if not current_app.testing:
        print('Processing an team assignment changed')
    
    data = json.loads(request.data)
    
    # Extract the booking data and update appropriate row in booking table
    process_booking_data(data)
    
    ##  I think we should IGNORE this as it as triggered by a team assignment change only (that's what
    ##  one would assume by the name of the change)
    # Update the customer information table, if it has been updated since the last time it was stored
    #if 'customer' in data:
    #    process_customer_data(data['customer'])
    
    return 'OK'


