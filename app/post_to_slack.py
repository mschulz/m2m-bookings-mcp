# /app/post_to_slack.py

import requests
import json


def block_item(name, location, url):
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*{name}*\n{location}\n{url}"
        }
    }

def build_blocks(message_list):
    ending = "" if len(message_list) == 1 else 's'
    block_list = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Today's listing of {len(message_list)} new bond clean booking{ending} can be found below for calls to agents:"
            }
        },
        {
            "type": "divider"
        }
    ]
    for item in message_list:
        m = block_item(item["name"], item["location"], item["booking_url"])
        block_list.append(m)
    return { "blocks": block_list}

def post_message_to_slack(blocks):
    headers = {
         "Authorization":  "Bearer REDACTED_SLACK_TOKEN",
         "Content-type": "application/json; charset=utf-8"
    }
    url = "REDACTED_SLACK_WEBHOOK"
    res = requests.post(url, headers=headers, json=blocks)
    
    print(res.text)
    return res

def slack_messages(data):
    blocks = build_blocks(data)
    
    print(json.dumps(blocks, indent=2))
    
    post_message_to_slack(blocks)


if __name__ == "__main__":
    example_data = {
      "result": [
        {
          "category": "Bond Clean",
          "name": "Andy Stevenson",
          "location": "Maid2Match Perth - Southern Suburbs",
          "booking_url": "https://maid2match.launch27.com/admin/bookings/79664/edit"
        },
        {
          "category": "Bond Clean",
          "name": "Tim Svenson",
          "location": "Maid2Match Sunshine Coast",
          "booking_url": "https://maid2match.launch27.com/admin/bookings/79672/edit"
        }
      ]
    }
    
    example_block = {
      "blocks": [
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": "*Andy Stevenson*\nMaid2Match Perth - Southern Suburbs\nhttps://maid2match.launch27.com/admin/bookings/79664/edit"
          }
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": "*Tim Svenson*\nMaid2Match Sunshine Coast\nhttps://maid2match.launch27.com/admin/bookings/79672/edit"
          }
        }
      ]
    }

    slack_messages(example_data["result"])
