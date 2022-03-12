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
    if len(message_list) == 0:
        block_list = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "There are no new bond clean bookings for today"
                }
            },
            {
                "type": "divider"
            }
        ]
    else:
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

    """
    https://app.slack.com/block-kit-builder/T2TL2CGS2#%7B%22blocks%22:%5B%7B%22type%22:%22section%22,%22text%22:%7B%22type%22:%22mrkdwn%22,%22text%22:%22Hello,%20Assistant%20to%20the%20Regional%20Manager%20Dwight!%20*Michael%20Scott*%20wants%20to%20know%20where%20you'd%20like%20to%20take%20the%20Paper%20Company%20investors%20to%20dinner%20tonight.%5Cn%5Cn%20*Please%20select%20a%20restaurant:*%22%7D%7D,%7B%22type%22:%22divider%22%7D,%7B%22type%22:%22actions%22,%22elements%22:%5B%7B%22type%22:%22checkboxes%22,%22options%22:%5B%7B%22text%22:%7B%22type%22:%22plain_text%22,%22text%22:%22*this%20is%20plain_text%20text*%22,%22emoji%22:true%7D,%22description%22:%7B%22type%22:%22plain_text%22,%22text%22:%22*this%20is%20plain_text%20text*%22,%22emoji%22:true%7D,%22value%22:%22value-0%22%7D,%7B%22text%22:%7B%22type%22:%22plain_text%22,%22text%22:%22*this%20is%20plain_text%20text*%22,%22emoji%22:true%7D,%22description%22:%7B%22type%22:%22plain_text%22,%22text%22:%22*this%20is%20plain_text%20text*%22,%22emoji%22:true%7D,%22value%22:%22value-1%22%7D,%7B%22text%22:%7B%22type%22:%22plain_text%22,%22text%22:%22*this%20is%20plain_text%20text*%22,%22emoji%22:true%7D,%22description%22:%7B%22type%22:%22plain_text%22,%22text%22:%22*this%20is%20plain_text%20text*%22,%22emoji%22:true%7D,%22value%22:%22value-2%22%7D%5D,%22action_id%22:%22actionId-0%22%7D,%7B%22type%22:%22checkboxes%22,%22options%22:%5B%7B%22text%22:%7B%22type%22:%22mrkdwn%22,%22text%22:%22*this%20is%20mrkdwn%20text*%22%7D,%22description%22:%7B%22type%22:%22mrkdwn%22,%22text%22:%22*this%20is%20mrkdwn%20text*%22%7D,%22value%22:%22value-0%22%7D,%7B%22text%22:%7B%22type%22:%22mrkdwn%22,%22text%22:%22*this%20is%20mrkdwn%20text*%22%7D,%22description%22:%7B%22type%22:%22mrkdwn%22,%22text%22:%22*this%20is%20mrkdwn%20text*%22%7D,%22value%22:%22value-1%22%7D,%7B%22text%22:%7B%22type%22:%22mrkdwn%22,%22text%22:%22*this%20is%20mrkdwn%20text*%22%7D,%22description%22:%7B%22type%22:%22mrkdwn%22,%22text%22:%22*this%20is%20mrkdwn%20text*%22%7D,%22value%22:%22value-2%22%7D%5D,%22action_id%22:%22actionId-1%22%7D%5D%7D%5D%7D
    {
    	"type": "actions",
    	"elements": [{
    			"type": "checkboxes",
    			"options": [{
    					"text": {
    						"type": "plain_text",
    						"text": "*this is plain_text text*",
    						"emoji": true
    					},
    					"description": {
    						"type": "plain_text",
    						"text": "*this is plain_text text*",
    						"emoji": true
    					},
    					"value": "value-0"
    				},
    				{
    					"text": {
    						"type": "plain_text",
    						"text": "*this is plain_text text*",
    						"emoji": true
    					},
    					"description": {
    						"type": "plain_text",
    						"text": "*this is plain_text text*",
    						"emoji": true
    					},
    					"value": "value-1"
    				},
    				{
    					"text": {
    						"type": "plain_text",
    						"text": "*this is plain_text text*",
    						"emoji": true
    					},
    					"description": {
    						"type": "plain_text",
    						"text": "*this is plain_text text*",
    						"emoji": true
    					},
    					"value": "value-2"
    				}
    			],
    			"action_id": "actionId-0"
    		},
    		{
    			"type": "checkboxes",
    			"options": [{
    					"text": {
    						"type": "mrkdwn",
    						"text": "*this is mrkdwn text*"
    					},
    					"description": {
    						"type": "mrkdwn",
    						"text": "*this is mrkdwn text*"
    					},
    					"value": "value-0"
    				},
    				{
    					"text": {
    						"type": "mrkdwn",
    						"text": "*this is mrkdwn text*"
    					},
    					"description": {
    						"type": "mrkdwn",
    						"text": "*this is mrkdwn text*"
    					},
    					"value": "value-1"
    				},
    				{
    					"text": {
    						"type": "mrkdwn",
    						"text": "*this is mrkdwn text*"
    					},
    					"description": {
    						"type": "mrkdwn",
    						"text": "*this is mrkdwn text*"
    					},
    					"value": "value-2"
    				}
    			],
    			"action_id": "actionId-1"
    		}
    	]
    }
    """