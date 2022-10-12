# app/api_1_0/decorators.py

from functools import wraps
from sqlalchemy import exc

from flask import request, current_app, abort


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
            #print(f"Received API_KEY = {APIkey} Actual key = {current_app.config['API_KEY']}")
            abort(401, description="Invalid key provided")
        return f(*args, **kwargs)
 
    return decorated_function


def catch_operational_errors(f):
    """
    There are occassions when we get the following error message, with a HTTP status of 500:
    
    sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) terminating connection due to administrator command
    SSL connection has been closed unexpectedly
    
    This should capture those and make a cleaner entry in the logging.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except exc.OperationalError as e:
            abort(500, description="SSL connection closed unexpectedly")
    return decorated_function
        