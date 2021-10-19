# app/daos.py

"""
    Contains all the Data Access Objects (DAOs)

    Services/DAO Singleton Design Pattern: A pattern I have found that works very well in a Flask app is the services/dao (database access object) singleton pattern. The summary of this pattern is outlined below:
        Business logic is placed in services methods.
        Database access (ORM) is in dao methods which use models.
        Routes are kept light and either use service or dao methods.
    
"""

import json
from datetime import datetime, timedelta

from app import db
from app.local_date_time import local_time_now
from app.models import Booking, Customer
from calendar import monthrange


class BookingDAO:
    def __init__(self, model):
        self.model = model
    
    def get_by_booking_id(self, booking_id):
        return db.session.query(self.model).filter_by(booking_id = booking_id).first()
    
    def _find_dates_range(self, start_date_str, period_days, prior):
        date_start = datetime.strptime(start_date_str, "%Y-%m-%d")
        if prior:
            date_end = date_start - timedelta(days=period_days)
            return date_end, date_start
        else:
            date_end = date_start + timedelta(days=period_days)
        return date_start, date_end
    
    def get_gain(self, start_date_str, period_days, prior=True):
        """
        get count from start_date_str for period_days PRIOR to that date
        """
        date_start, date_end = self. _find_dates_range(start_date_str, period_days, prior)
        
        print(f'start={date_start}  end={date_end}')
        
        db.session.query(self.model).filter_by(booking_id = 9990).first()
    
        return db.session.query(self.model)\
            .filter_by(was_first_recurring = True)\
            .filter(self.model._updated_at >= date_start)\
            .filter(self.model._updated_at < date_end)\
            .distinct(self.model._customer_id)\
            .count()
    
    def get_loss(self, start_date_str, period_days, prior=True):
        date_start, date_end = self. _find_dates_range(start_date_str, period_days, prior)

        print(f'start={date_start}  end={date_end}')
        
        db.session.query(self.model).filter_by(booking_id = 9990).first()
    
        return db.session.query(self.model)\
            .filter_by(cancellation_type = 'This Booking and all Future Bookings')\
            .filter(self.model._updated_at >= date_start)\
            .filter(self.model._updated_at < date_end)\
            .distinct(self.model._customer_id)\
            .count()
    
    def _get_days_in_month(self, month, year):
        _, period = monthrange(year, month)
        start_date_str = f'{year}-{month:02}-01'
        
        print(f'str={start_date_str} period={period}')
        
        return (start_date_str, period)
        
    def get_gain_by_month(self, month, year):
        start_date_str, period = self._get_days_in_month(month, year)
        return self.get_gain(start_date_str, period, prior=False)
    
    def get_loss_by_month(self, month, year):
        start_date_str, period = self._get_days_in_month(month, year)
        return self.get_loss(start_date_str, period, prior=False)
        
booking_dao = BookingDAO(Booking)


class CustomerDAO:
    def __init__(self, model):
        self.model = model
    
    def get_by_customer_id(self, customer_id):
        return db.session.query(self.model).filter_by(customer_id = customer_id).first()

customer_dao = CustomerDAO(Customer)

if __name__ == '__main__':
    from app import create_app
    
    app = create_app()
    
    start_str = "2021-09-01"
    month = 9
    period = 30
    
    with app.app_context():
        gain = booking_dao.get_gain(start_str, period)
        print(f'Customers_gained={gain}')
        
        loss = booking_dao.get_loss(start_str, period)
        print(f'Customers lost={loss}')
        
        gain = booking_dao.get_gain_by_month(month, 2021)
        print(f'Customers gained in month {month}={gain}')
        
        loss = booking_dao.get_loss_by_month(month, 2021)
        print(f'Customers lostin month (month)={loss}')
        
        