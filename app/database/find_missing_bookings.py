# /app/database/find_missing_bookings.py


"""
    Find any booking_ids missing in the database:
    
        1: 
            scan database for all bookings.
                save the booking_id in a set
        2: 
            Find the maximum and minimum booking_id, and generate a set containing this randge
        3:
            subtract the booking_ids in the database from the full range of possible booking_ids

        3: report all booking_ids still in the list (should be none)
"""


import os
import json

from app import create_app, db
from flask import  current_app
from app.models import Booking
import requests
import pendulum as pdl
from datetime import datetime

class AllBookings(object):
    
    def __init__(self):
        self.base_url = 'https://maid2match.launch27.com'
        self.headers = {
            "authority": "maid2match.launch27.com",
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "authorization": f"Bearer {self._get_api_key()}",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "referrer": f"{self.base_url}/admin/bookings",
            "referrerPolicy": "no-referrer-when-downgrade",
            "body": None,
            "method": "GET",
            "mode": "cors",
            "credentials": "include"
            
        }
        
    def _get_api_key(self):
        login_url = f'{self.base_url}/v1/login'
        referrer_url = f'{self.base_url}/login'
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json;charset=UTF-8",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "referrer": referrer_url,
            "referrerPolicy": "no-referrer-when-downgrade",
            "body": None,
            "method": "GET",
            "mode": "cors",
            "credentials": "include"
        }
        

        payload = {'email': current_app.config['L27_USERNAME'], 'password': current_app.config['L27_PASSWORD']}

        r = requests.post(login_url, headers=headers, data=json.dumps(payload))
        d = r.json()
    
        my_id = d['id']
        single_access_token = d['single_access_token']
        api_key = d['bearer']
    
        return api_key

    def get_booking_data(self, booking_id, filter=None):
        """
        https://maid2match.launch27.com/v1/staff/bookings/76499
        """
        url_base = f'{self.base_url}/v1/staff/bookings/{booking_id}'
        if filter:
            params = {
                'filter': filter,
                'from': '2020-01-01',
                'limit': limit,
                'offset': offset,
                'options': 'completed%2Cexclude_forecasted',
                'query': '',
                'sort': 'asc',
                'to': '2020-06-01'
            }
        else:
            params = {
                'from': '2020-01-01',
                'limit': limit,
                'offset': offset,
                'options': 'completed%2Cexclude_forecasted',
                'query': '',
                'sort': 'asc',
                'to': '2020-06-01'
            }
        r = requests.get(url=url_base, headers=self.headers, params=params)
    
        if r.status_code != 200:
            print(f'get_booking_data:: Status_code: {r.status_code} text: {r.text}')
            raise L27RequestError(f'get_booking_data:: Status_code: {r.status_code} text: {r.text}')

        r_json = r.json()
        #print(f'get_completed_bookings[0]: {r_json[0]["id"]}')
        return r_json

def created_after(datetime_str):
    start_created_at = pdl.datetime(2020,1,1)
    created_at_datetime = pdl.parse(datetime_str)
    return created_at_datetime >= start_created_at

def main():

    app = create_app()

    with app.app_context():
        b = AllBookings()
        
        created_at_datetime = datetime(2019, 12, 31, 14, 0, 0, 0)
        res = db.session.query(Booking.booking_id).filter(Booking._created_at >= created_at_datetime).all()
        
        res_list = [item[0] for item in res]
        
        print(f'number = {len(res_list)}')
        
        start_range = min(res_list)
        end_range = max(res_list)
        booking_ids_db_= set(res_list)
        
        print(f'{start_range = } {end_range = } number of booking ids = {len(res)}')
        
        full_range = set(range(int(start_range), int(end_range)+1))
        
        print(f'number in full range = {len(full_range)}')
        
        check_ids = list(full_range.difference(booking_ids_db_))
        check_ids.sort()
        
        print(f'number of booking_ids to check on = {len(check_ids)}')
        
        missing_count = 0
        for idx, booking_id in enumerate(check_ids):
            d = b.get_booking_data(booking_id)
            print(f'Looking up booking_id = {booking_id} {d["created_at"]}')
            if created_after(d['created_at']):
                missing_count += 1
                #print(json.dumps(d, indent=2))
                print(f"{d['id']}: {d['name']} {d['created_at']} {d['completed']}")
        print(f'{missing_count = }')
        
if __name__ == '__main__':
    main()
