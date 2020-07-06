# app/api_1_0/decorators.py

from functools import wraps

from flask import request, current_app, abort
from threading import Thread


def APIkey_required(f):
    """ Access to the route requires the API_KEY. """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        #print(f'Authorization Header: {auth_header}')
        
        if auth_header:
            APIkey = auth_header.split(" ")[1]
        else:
            APIkey = ''
            
        if APIkey != current_app.config['API_KEY']:
            print(f"Received API_KEY = {APIkey} Actual key = {current_app.config['API_KEY']}")
            abort(401)
        return f(*args, **kwargs)
 
    return decorated_function
