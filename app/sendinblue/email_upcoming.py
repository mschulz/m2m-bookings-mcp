# app/sendinblue/email_upcoming.py

import os
import sys
import json

from datetime import datetime
from .. import create_app
from app import db
from app.models import Booking, Customer
from sqlalchemy import exc
from flask import current_app
from app.exceptions import SendInBlueError, InvalidTemplateIDError
import requests

"""
    Useage:
        % email_upcoming <days until service_date> <sendinblue template number>
"""


def send_transactional_email(template_id, first_name, name, email, service_date, service_time, 
                                service_category, service, pricing_parameters, extras, phone, address,
                                customer_notes, discount_amount, final_price):
    url = "https://api.sendinblue.com/v3/smtp/email"
    
    headers = {
        'accept': "application/json", 
        'content-type': "application/json", 
        'api-key': current_app.config['SIB_API_KEY']
    }
    
    payload = {
        "sender":{
            "name": "Mark Schulz", #current_app.config['FROM_NAME'],
            "email": "mark.f.schulz@gmail.com" #current_app.config['FROM_ADDRESS']
        },
        "to":[
            {
                "name": name,
                "email": email
            },

        ],
        "templateId":template_id,
        "params": {
            "first_name": first_name,
            "phone": current_app.config['PHONE'],
            "service_date": service_date,
            "service_time": service_time,
            "service_category": service_category,
            "service": service,
            "pricing_parameters": pricing_parameters,
            "extras": extras,
            "name": name,
            "phone": phone,
            "address": address,
            "customer_notes": customer_notes,
            "discount_amount": discount_amount,
            "final_price": discount_amount
        }
    }

    response = requests.request("POST", url, data=json.dumps(payload), headers=headers)

    if response.status_code != 201:
        current_app.logger.error(f"""{current_app.config["APP_NAME"]}/email_upcoming.py failed to send
        Details: Name='{name}' email='{email}'
        Error({response.status_code}): {response.text}""")
        if "Invalid template id" in response.text:
            raise InvalidTemplateIDError(template_id)
        raise SendInBlueError

def email_campaign(days_until_service, template_id):
    ''' Call up sendinblue to send a transactional email to each customer with an upcoming service. '''
    
    # Decode the arguments to this command
    
    app = create_app()

    with app.app_context():
        params = {
            'first_name': "Mark",
            'name': "Mark Schulz",
            'email': "mark.f.schulz@gmail.com",
            'service_date': '01/09/2020',
            'service_time': '',
            'service_category': '',
            'service': '',
            'pricing_parameters': '',
            'extras': '',
            'phone': '',
            'address': '',
            'customer_notes': '',
            'discount_amount': '$1.00',
            'final_price': '$99.00'
        }
        send_transactional_email(template_id, **params)


if __name__ == '__main__':

    if len(sys.argv) > 3:
        print('You have specified too many arguments')
        sys.exit()

    if len(sys.argv) < 3:
        print('You need to specify the path to be listed')
        sys.exit()

    days_until_service = int(sys.argv[1])
    template_id = int(sys.argv[2])
    
    print(f'days_until_service: {days_until_service}\ntemplate_id: {template_id}')
    
    try:
        email_campaign(days_until_service, template_id)
    except SendInBlueError:
        sys.exit(1)
    except InvalidTemplateIDError as e:
        print(f'Invalid teamplate id: {e}')
        sys.exit(2)

    sys.exit(0)