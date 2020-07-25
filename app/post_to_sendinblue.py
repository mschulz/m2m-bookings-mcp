# app/post_to_sendinblue

import requests
import json
from datetime import datetime
from pprint import pformat

from flask import current_app
from app.email import send_error_email


def int_to_dollars(val):
    if val is None:
        return '$0.00'
    
    s = f'${int(val//100)}.{val%100}'
    return s

def build_payload(email, name, template_id, payload):

    data = {
        "sender":{
            "name": current_app.config['SENDINBLUE_FROM_NAME'],
            "email": current_app.config['SENDINBLUE_FROM_EMAIL']
        },
        "to":[
            {
                "name": name,
                "email": email
            }
        ],
        "templateId":template_id,

        "params": {
            "first_name": payload.first_name,
            "serviceDate": datetime.strftime(payload.service_date, "%Y-%m-%d"),
            "serviceTime": payload.service_time,
            "service_category": payload.service_category,
            "service": payload.service,
            "pricing_parameters": payload.pricing_parameters,
            "extras": payload.extras,
            "frequency": payload.frequency,
            "name": payload.name,
            "phone": payload.phone,
            "address": payload.address,
            "customer_notes": payload.customer_notes,
            "discount_amount": int_to_dollars(payload.discount_from_code),
            "final_price": int_to_dollars(payload.final_price),
            "m2m_phone": current_app.config['PHONE']
        }
    }
    
    #print(f'payload data: {data}')
    
    return data


def post_to_sendinblue(payload):

    API_KEY = current_app.config['SENDINBLUE_API_KEY']

    headers = {
        'accept': "application/json", 
        'content-type': "application/json", 
        'api-key': API_KEY
    }

    url = current_app.config['SENDINBLUE_URL']
    
    print(f'requests.request("POST", {url}, data={json.dumps(payload)}, headers={headers})')

    response = requests.request("POST", url, data=json.dumps(payload), headers=headers)
    
    if response.status_code != 201:
        p = payload["params"]
        msg = f"""Post_to_sendinblue failed. Status code: {response.status_code} message: {response.text}
        payload={pformat(payload)}"""
        current_app.logger.error(msg)
        m = current_app.config['SUPPORT_EMAIL'].split('@')
        send_error_email(f"{m[0]}+error@{m[1]}", msg)
