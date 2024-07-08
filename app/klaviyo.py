# app/klaviyo.py
"""
    Send data to the appropriate Klaviyo lists
"""

import json

import requests
from flask import current_app


class Klaviyo(object):
    def __init__(self):
        self.url = current_app.config['MY_KLAVIYO_URL']
        self.headers = {
            "Authorization": f"Bearer {current_app.config['MY_KLAVIYO_API_KEY']}",
            "Content-Type": "application/json"
        }

    def _get_payload(self, data):
        """
            Post the data to the Klaviyo Customer List.
        """
        print(f"zip = {data['zip']}")
        
        payload = {
            "email": data["email"],
            "first_name": data["first_name"],
            "phone": data["phone"],
            "postcode": data["postcode"] if "postcode" in data else data["zip"],
            "quote": data["final_price"]
        }
        return payload

    def post_home_data(self, data):
        """
            Post the data to the Klaviyo Customer List.
        """
        url = f"{self.url}/house/new"
        payload = self._get_payload(data)
        
        print(f"{url=} {payload=}")
        
        res = requests.post(url, headers=self.headers, json=payload)

        if res.status_code != 201:
            error_msg = f"Failed ({res.status_code}) to update house customer list for {payload['email']}"
            print(error_msg)
            print(res.text)
            return

    def post_bond_data(self, payload):
        """
            Post the data to the Klaviyo Bond Customer List.
        """
        payload = self._get_payload(payload)
        res = requests.post(f"{self.url}/bond/new", headers=self.headers, json=payload)

        if res.status_code != 201:
            error_msg = f"Failed ({res.status_code}) to update bond customer list for {payload['email']}"
            print(error_msg)
            print(res.text)
            return

def notify_klaviyo(service_category, data):
    k = Klaviyo()
    if service_category == 'House Clean':
        k.post_home_data(data)
    else:
        k.post_bond_data(data)
        
    
    