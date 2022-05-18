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

"""def test_main():

    app = create_app()

    with app.app_context():
        
        service_category = 'Bond Clean'
        #booking_status = 'NOT_COMPLETE'
        #booking_status = 'COMPLETED'
        #booking_status = 'CANCELLED'
        
        #yesterday = pdl.now('UTC').in_timezone(app.config['TZ_LOCALTIME']).subtract(days=1)
        yesterday = pdl.datetime(2022,5,9, tz='Australia/Brisbane')
        
        start_created = yesterday.start_of('day')
        end_created = yesterday.end_of('day')
        
        print(f"\n{start_created=} {end_created=}")
        
        start_created = datetime.fromtimestamp(start_created.timestamp(), pdl.tz.UTC)
        end_created = datetime.fromtimestamp(end_created.timestamp(), pdl.tz.UTC)
        
        for booking_status in ['NOT_COMPLETE', 'COMPLETED', 'CANCELLED']:
            list_all(service_category, booking_status, start_created, end_created)

        check_it = booking_dao.get_by_booking_id(90988)
        print(f"\n{check_it.booking_id=} {check_it._created_at=} '{check_it.booking_status=}'")

def list_all(service_category, booking_status, start_created, end_created):
    print(f"\n{booking_status}")
    res = booking_dao.get_by_date_range(service_category, booking_status, start_created, end_created)
    
    for item in res:
        print(item.booking_id, item._created_at, item.booking_status, item._cancellation_datetime)
    

#test_main()"""
