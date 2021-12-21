# /app/post_to_slack.py

import requests
import json


def post_message_to_slack(text, blocks = None):
    headers = {
         "Authorization":  "Bearer REDACTED_SLACK_TOKEN",
         "Content-type": "application/json"
    }
    data = {
        'channel': slack_channel,
        'text': text,
        'icon_emoji': slack_icon_emoji,
        'username': slack_user_name,
        'blocks': json.dumps(blocks) if blocks else None
    }
    url = 'https://slack.com/api/chat.postMessage'
    return requests.post(url, headers=deaders, data=data).json()

"""
    Given a JSON structure like:
    
        {
          "result": [
            {
              "category": "Bond Clean",
              "name": "Shelley Moore",
              "location": "Maid2Match Perth - Northern Suburbs",
              "booking_url": "https://maid2match.launch27.com/admin/bookings/79629/edit"
            }
          ]
        }
    
    Post a Slack message like:
    
    -- Shelly Moore --
    Maid2Match Perth - Northern Suburbs
    https://maid2match.launch27.com/admin/bookings/79629/edit
    
"""

def block_item(name, location, url):
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*{name}*\n{location}\n{url}"
        }
    }

def build_blocks(message_list):
    block_list = []
    for item in message_list:
        m = block_item(item["name"], item["location"], item["booking_url"])
        block_list.append(m)
    
    print(json.dumps({ "blocks": block_list }, indent=2))
    return json.dumps({ "blocks": block_list }) if block_list else None

"""channel
C02C0MC3DFX
ts
1639968814.000500
bot_id
B8976EP1T

m2m-stats-debug channelid: CAX29F0RG
"""

def slack_messages(blocks):

    """    token = 
        channel = "C02C0MC3DFX"
        text = ""
        user_name = "Zapier"
    """    

    bb = build_blocks(blocks)

    print(bb)