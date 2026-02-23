# app/services/slack.py

import logging

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from config import get_settings

logger = logging.getLogger(__name__)


def block_item(name, location, url):
    return {
        "type": "section",
        "text": {"type": "mrkdwn", "text": f"<{url}|{name}> {location}"},
    }


def build_blocks(message_list):
    if len(message_list) == 0:
        block_list = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "There are no new bond clean bookings for today",
                },
            },
            {"type": "divider"},
        ]
    else:
        ending = "" if len(message_list) == 1 else "s"
        block_list = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Today's listing of {len(message_list)} new bond clean booking{ending} can be found below for calls to agents:",
                },
            },
            {"type": "divider"},
        ]
        for item in message_list:
            url = f"https://maid2match.launch27.com/admin/bookings/{item.booking_id}/edit"
            m = block_item(item.name, item.location, url)
            block_list.append(m)
    return {"blocks": block_list}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=10),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def post_message_to_slack(blocks):
    settings = get_settings()
    headers = {
        "Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}",
        "Content-type": "application/json; charset=utf-8",
    }
    with httpx.Client(timeout=10) as client:
        res = client.post(settings.SLACK_WEBHOOK_URL, headers=headers, json=blocks)
    logger.debug("Slack response: %s", res.text)
    return res


def slack_messages(data):
    blocks = build_blocks(data)
    post_message_to_slack(blocks)
