# app/locations.py

import requests
import json
from flask import current_app

from app.email import send_error_email

location_cache = {}

def get_location(postcode):
    """
        Given the postcode, return the location name.
    """
    # First check the cache to see if we have a location_name already
    if not (isinstance(postcode, str)):
        postcode = str(postcode)
        
    if postcode in location_cache:
        return location_cache[postcode]
        
    # Else go look it up
    res = requests.get(f'{current_app.config["ZIP2LOCATION_URL"]}?postcode={postcode}')
    
    if res.status_code != 200:
        error_msg = f'postcode {postcode} not recognized'
        print(error_msg)
        toaddr = current_app.config['SUPPORT_EMAIL']
        send_error_email(toaddr, error_msg)
        # Don't update cache.  We want to catch the mapping whenever the location DB is updated
        # Heroku restarts the server after periods of rest, and once a day.
        return None
    
    data = json.loads(res.text)
    
    # Update cache
    location_cache[postcode] = data['title']
    
    return data['title']
    