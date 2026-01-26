# app/post_to_zapier.py

import json
import requests
from flask import current_app
from app.email import send_error_email


def post_to_zapier(url, d):
    headers = {"content-type": "application/json"}
    try:
        r = requests.post(url, headers=headers, data=d, timeout=10)
        r.raise_for_status()
        current_app.logger.info(f"Posted to Zapier: {d}")
        return r
    except requests.exceptions.HTTPError as errh:
        error_msg = f"Failed to post to Zapier: {d}\nHttp Error:: {errh}"
    except requests.exceptions.ConnectionError as errc:
        error_msg = f"Failed to post to Zapier: {d}\nError Connecting: {errc}"
    except requests.exceptions.Timeout as errt:
        error_msg = f"Failed to post to Zapier: {d}\nTimeout Error: {errt}"
    except requests.exceptions.RequestException as err:
        error_msg = f"Failed to post to Zapier: {d}\nOOps: Something Else: {err}"
    else:
        error_msg = f"Failed to post to Zapier: {d}\nOOps: Something totally unexpected"
    current_app.logger.error(error_msg)
    send_error_email(current_app.config["SUPPORT_EMAIL"], error_msg)
    return None


def post_new_bond_agent_calls(d):
    url = current_app.config["NEW_BOND_AGENT_CALLS"]
    data = json.dumps({"result": d}, indent=2)
    res = post_to_zapier(url, data)
    return res
