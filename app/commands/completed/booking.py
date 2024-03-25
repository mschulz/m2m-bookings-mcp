# app/launch27/booking.py

import datetime
import json
import requests

from flask import current_app, Response, jsonify


class Booking():
    def __init__(self):
        self.my_l27_url = current_app.config['L27_URL']
        self.my_l27_apikey = current_app.config['L27_API_KEY']
        self.headers = {
            "authorization": f"Bearer {self.my_l27_apikey}",
            "content_type": "application/json"
        }

    
    def get_all_in_tz(self, today_date_string, tz_name):
        url = f"{self.my_l27_url}/v1/bookings/tocomplete/{today_date_string}"
        
        print(f"{url=}")
        
        params = {
            "tzname": tz_name
        }
        r = requests.get(url, headers=self.headers, params=params)
        print(r)
        print(r.json())
        return r.json()


    def complete(self, id):
        if not current_app.config['TESTING']:
            url = f"{self.my_l27_url}/v1/staff/bookings/{id}/complete"

            r = requests.post(url, self.headers)
    
            if r.status_code == 422:
                current_app.logger.warning(f'IGNORED:: complete_booking:: booking already completed ({id}):')
                return 0    #Fail - don't count this
            elif r.status_code != 200:
                current_app.logger.error(f'complete_booking:: status_code({r.status_code}) attempting to mark booking ({id}) complete\n * Error: {r.text}')
                return 0    #Fail - don't count this

        return 1    #Success - count this

#################################################

if __name__ == "__main__":
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        date_string = '2024-03-22'
        tz_name = 'AEST'
        
        b = Booking()
        res = b.get_all_in_tz(date_string, tz_name)
        print(res)         
