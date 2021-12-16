# app/bookings/search.py
import json
from app import create_app
import pendulum as pdl
from datetime import datetime


from app import db
from app.models import Booking
from sqlalchemy import exc, and_, func
from app.post_to_zapier import post_new_bond_agent_calls

def search_bookings(service_category, start_created, end_created, booking_status):
    
    print(f'params: category={service_category} date={start_created},{end_created} booking_status={booking_status}')
    
    res = db.session.query(Booking) \
        .filter_by(service_category=service_category, booking_status=booking_status).filter(and_(Booking._created_at >= start_created, Booking._created_at <= end_created)) \
        .all()
    
    print(res)
    
    found = []
    for item in res:
        data = {
            "category": item.service_category,
            "name": item.name,
            "location": item.location,
            "booking_url": f"https://maid2match.launch27.com/admin/bookings/{item.booking_id}/edit"
        }
        found.append(data.copy())
    
    return found

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
        
        res = search_bookings(service_category, start_created, end_created, booking_status)
        
        print(json.dumps({"result": res}, indent=2))
        
        #post_new_bond_agent_calls(res)

main()
