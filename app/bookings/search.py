# app/bookings/search.py

from app import create_app
#from app.bookings.views import search_bookings
import pendulum as pdl

def main():

    app = create_app()

    with app.app_context():
        
        service_category = 'Bond Clean'
        created_at_str = '' #Yesterday, in UTC
        booking_status = 'NOT_COMPLETED'
        
        #item_list = search_bookings(service_category, created_at_str, booking_status)
        
        #print(item_list)
        
        yesterday = pdl.now()
        
        print(yesterday)
        
main()
