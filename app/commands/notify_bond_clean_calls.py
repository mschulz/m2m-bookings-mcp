# app/commands/notify_bond_clean_calls.py
import json
from app import create_app
import pendulum as pdl
from datetime import datetime


from app.daos import booking_dao
from sqlalchemy import exc, and_, func
from app.post_to_zapier import post_new_bond_agent_calls
from app.post_to_slack import slack_messages


def main():

    app = create_app()

    with app.app_context():
        
        service_category = 'Bond Clean'
        booking_status = 'NOT_COMPLETE'
        
        yesterday = pdl.now('UTC').in_timezone(app.config['TZ_LOCALTIME']).subtract(days=1)
        
        start_created = yesterday.start_of('day')
        end_created = yesterday.end_of('day')
        start_created = datetime.fromtimestamp(start_created.timestamp(), pdl.tz.UTC)
        end_created = datetime.fromtimestamp(end_created.timestamp(), pdl.tz.UTC)
        
        res = booking_dao.get_by_date_range(service_category, booking_status, start_created, end_created)
        
        slack_messages(res)

main()
