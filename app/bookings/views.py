# app/bookings/views.py

import json
from flask import request, current_app, abort
from app.bookings import bookings_api
from app.decorators import APIkey_required
from app.email import send_success_email
from models import import_dict


@bookings_api.route('/booking/new', methods=['POST'])
@APIkey_required
def booking():
    ''' 
        return 'Hello World!' to check link.
    '''
    print('Processing a new booking ...')
    
    data = request.data
    d =  import_dict(data)
    
    current_app.logger.info(f'Data received: {d}')
    
    # Check which keys were sent and not processed by 'import_dict'
    print('Keys of data from zapier not processed from:')
    print(f'{data.keys() - d.keys()}')
    
    send_success_email(current_app.config['SUPPORT_EMAIL'])
    
    return 'OK'


@bookings_api.route('/booking/completed', methods=['POST'])
@APIkey_required
def booking():
    '''
        return 'Hello World!' to check link.
    '''
    print('Processing a completed booking')
    
    data = request.data
    d =  import_dict(data)
    
    current_app.logger.info(f'Data received: {d}')
    
    send_success_email(current_app.config['SUPPORT_EMAIL'])
    
    return 'OK'


@bookings_api.route('/booking/cancellation', methods=['POST'])
@APIkey_required
def booking():
    '''
        return 'Hello World!' to check link.
    '''
    print('Processing a cancelled booking')
    
    data = request.data
    d =  import_dict(data)
    
    current_app.logger.info(f'Data received: {d}')
    
    send_success_email(current_app.config['SUPPORT_EMAIL'])
    
    return 'OK'


@bookings_api.route('/booking/updated', methods=['POST'])
@APIkey_required
def booking():
    '''
        return 'Hello World!' to check link.
    '''
    print('Processing an updated booking')
    
    data = request.data
    d =  import_dict(data)
    
    current_app.logger.info(f'Data received: {d}')
    
    send_success_email(current_app.config['SUPPORT_EMAIL'])
    
    return 'OK'


@bookings_api.route('/booking/team_changed', methods=['POST'])
@APIkey_required
def booking():
    '''
        return 'Hello World!' to check link.
    '''
    print('Processing an team assignment changed')
    
    data = request.data
    d =  import_dict(data)
    
    current_app.logger.info(f'Data received: {d}')
    
    send_success_email(current_app.config['SUPPORT_EMAIL'])
    
    return 'OK'


