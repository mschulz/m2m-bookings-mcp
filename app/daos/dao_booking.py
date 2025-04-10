# app/daos_booking.py

"""
    Contains all the Data Access Objects (DAOs)

    Services/DAO Singleton Design Pattern: A pattern I have found that works very well in a Flask app is the services/dao (database access object) singleton pattern. The summary of this pattern is outlined below:
        Business logic is placed in services methods.
        Database access (ORM) is in dao methods which use models.
        Routes are kept light and either use service or dao methods.

"""

from datetime import datetime, timedelta
import pytz
import pendulum as pdl

from app import db
from app.daos.dao_base import BaseDAO

from app.models.models_booking import Booking
from calendar import monthrange
from app.local_date_time import utc_to_local
from config import Config
from sqlalchemy import and_


class BookingDAO(BaseDAO):
    def __init__(self, model):
        self.model = model
        super().__init__(model)

    def get_by_booking_email_service_date_range(self, email, service_date):

        def get_week_start_end(date_str):
            """
                Offsets: Current dow (Sunday offset. Saturday Offset)
                Monday(0): (-1, 5)
                Tuesday(1): (-2, 4)
                Wednesday(2): (-3, 3)
                Thursday(3): (-4, 2)
                Friday(4): (-5, 1)
                Saturday(5): (-6, 0)
                Sunday(6): (0, 6)
            """
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            dow = dt.weekday()
            offsets = (
                (-1, 5),
                (-2, 4),
                (-3, 3),
                (-4, 2),
                (-5, 1),
                (-6, 0),
                (0, 6)
            )
            week_start = dt + timedelta(days= offsets[dow][0])
            week_end = dt + timedelta(days= offsets[dow][1])
            week_start_str = week_start.strftime("%Y-%m-%d")
            week_end_str = week_end.strftime("%Y-%m-%d")
            return (week_start_str, week_end_str)
        week_start, week_end = get_week_start_end(service_date)
        
        return db.session.query(self.model) \
        .filter_by(email = email) \
        .filter(and_(self.model._service_date >= week_start, self.model._service_date <= week_end)).first()

    def get_by_date_range(self, service_category, booking_status, start_created, end_created):
    
        print(f'params: category={service_category} date={start_created},{end_created} booking_status={booking_status}')
    
        return db.session.query(self.model) \
            .filter_by(service_category=service_category, booking_status=booking_status) \
            .filter(and_(self.model._created_at >= start_created, self.model._created_at <= end_created)) \
            .all()

    def completed_bookings_by_service_date(self, from_date, to_date):
    
        #print(f'params: from={from_date} to={to_date}')
    
        return db.session.query(self.model) \
            .filter_by(booking_status='COMPLETED') \
            .filter(and_(self.model._service_date >= from_date, self.model._service_date <=to_date)) \
            .all()
        """return db.session.query(self.model) \
            .filter_by(_service_date = from_date) \
            .all()"""
        
    def date_to_UTC_date(self, date_str):
        local = pytz.timezone(Config.TZ_LOCALTIME)
        naive = datetime.strptime(date_str, "%Y-%m-%d")
        local_dt = local.localize(naive, is_dst=Config.TZ_ISDST)
        utc_dt = local_dt.astimezone(pytz.utc)

        #print(f'str={date_str} naive={naive} local_dt={local_dt} utc_dt={utc_dt}')

        return utc_dt

    def _find_dates_range(self, start_date_str, period_days, prior):
        date_start = self.date_to_UTC_date(start_date_str)
        if prior:
            date_end = date_start - timedelta(days=period_days)
            return date_end, date_start
        else:
            date_end = date_start + timedelta(days=period_days)
        return date_start, date_end

    def _get_gain_in_date_range(self, date_start, date_end):
        items = db.session.query(self.model)\
            .filter_by(was_first_recurring = True)\
            .filter(self.model._created_at >= date_start)\
            .filter(self.model._created_at < date_end)\
            .distinct(self.model._customer_id)
        return items

    def get_gain_in_date_range(self, date_start, date_end):
        items = self._get_gain_in_date_range(date_start, date_end)
        return items.count()

    def get_gain_in_date_range_list(self, date_start, date_end):
        items = self._get_gain_in_date_range(date_start, date_end)
        return [item.booking_id for item in items.all()]

    def get_gain(self, start_date_str, period_days, prior=True):
        """
        get count from start_date_str for period_days PRIOR to that date
        """
        date_start, date_end = self. _find_dates_range(start_date_str, period_days, prior)
        return self.get_gain_in_date_range(date_start, date_end)

    def get_gain_list(self, start_date_str, period_days, prior=True):
        """
        get count from start_date_str for period_days PRIOR to that date
        """
        date_start, date_end = self. _find_dates_range(start_date_str, period_days, prior)
        return self.get_gain_in_date_range_list(date_start, date_end)

    def _get_days_in_month(self, month, year):
        if isinstance(month, str):
            month = int(month)
        if isinstance(year, str):
            year = int(year)
        _, period = monthrange(year, month)
        start_date_str = f'{year}-{month:02}-01'
        return (start_date_str, period)

    def get_gain_by_month(self, month, year):
        start_date_str, period = self._get_days_in_month(month, year)
        return self.get_gain(start_date_str, period, prior=False)

    def get_gain_by_month_list(self, month, year):
        start_date_str, period = self._get_days_in_month(month, year)
        return self.get_gain_list(start_date_str, period, prior=False)

    #### CANCELLATION Calculations ####

    def get_cancelled(self, start_date_str, period_days, prior=True):
        """
        get count from start_date_str for period_days PRIOR to that date
        """
        date_start, date_end = self. _find_dates_range(start_date_str, period_days, prior)
        return self.get_cancelled_in_date_range(date_start, date_end)

    def _get_cancelled_in_date_range(self, date_start, date_end):
        items =  db.session.query(self.model)\
            .filter_by(cancellation_type = 'This Booking and all Future Bookings')\
            .filter(self.model._cancellation_date >= date_start)\
            .filter(self.model._cancellation_date < date_end)\
            .distinct(self.model._customer_id)
        return items

    def get_cancelled_in_date_range(self, date_start, date_end):
        items = self._get_cancelled_in_date_range(date_start, date_end)
        
        l = [item.booking_id for item in items.all()]
        print(f'get_cancelled_in_date_range({len(l)}): {l}')
        
        return items.count()

    def get_cancelled_in_date_range_list(self, date_start, date_end):
        items = self._get_cancelled_in_date_range(date_start, date_end)
        return [item.booking_id for item in items.all()]

    def get_cancelled_list(self, start_date_str, period_days, prior=True):
        date_start, date_end = self. _find_dates_range(start_date_str, period_days, prior)
        res = self._get_cancelled_in_date_range_list(date_start, date_end).all()
        return [item.booking_id for item in res]

    def get_cancelled_by_month(self, month, year):
        start_date_str, period = self._get_days_in_month(month, year)
        return self.get_cancelled(start_date_str, period, prior=False)

    # Current Recurring customer count
    def recurring_current(self):
        return db.session.query(self.model)\
            .filter(self.model.service_date >= utc_to_local(datetime.utcnow()).date())\
            .filter_by(booking_status = 'NOT_COMPLETE')\
            .filter(self.model.frequency != '1 Time Service')\
            .distinct(self.model._customer_id)\
            .count()

    def gain_cancelled_in_range(self, start_date, end_date):
        # Need to convert from Pendulum datetime to datetime.datetime format
        start_created = datetime.fromtimestamp(start_date.timestamp(), pdl.tz.UTC)
        end_created = datetime.fromtimestamp(end_date.timestamp(), pdl.tz.UTC)

        gain = self.get_gain_in_date_range(start_created, end_created)
        cancelled = self.get_cancelled_in_date_range(start_created, end_created)
        return gain, cancelled
    
    def get_cancellations(self):
        return db.session.query(self.model)\
        .filter_by(booking_status = 'CANCELLED')\
        .filter(self.model._cancellation_date != None)\
        .all()
    
    def get_missing_cancellations(self):
        return db.session.query(self.model)\
        .filter_by(booking_status = 'CANCELLED')\
        .filter(self.model._cancellation_date == None)\
        .all()
    
    #### CANCELLATION Calculations NEW!!!!####

    def get_cancelled_new(self, start_date_str, period_days, prior=True):
        """
        get count from start_date_str for period_days PRIOR to that date
        """
        date_start, date_end = self. _find_dates_range(start_date_str, period_days, prior)
        return self.get_cancelled_in_date_range_new(date_start, date_end)

    def _get_cancelled_in_date_range_new(self, date_start, date_end):
        items =  db.session.query(self.model)\
            .filter_by(cancellation_type = 'This Booking and all Future Bookings')\
            .filter(self.model._cancellation_datetime >= date_start)\
            .filter(self.model._cancellation_datetime < date_end)\
            .distinct(self.model._customer_id)
        return items

    def get_cancelled_in_date_range_new(self, date_start, date_end):
        items = self._get_cancelled_in_date_range_new(date_start, date_end)
        return items.count()

    def get_cancelled_in_date_range_list_new(self, date_start, date_end):
        items =  self._get_cancelled_in_date_range_new(date_start, date_end)
        return [item.booking_id for item in items.all()]

    def get_cancelled_list(self, start_date_str, period_days, prior=True):
        date_start, date_end = self. _find_dates_range(start_date_str, period_days, prior)
        res = self.get_cancelled_in_date_range_list_new(date_start, date_end)
        return res

    def get_cancelled_by_month_new(self, month, year):
        start_date_str, period = self._get_days_in_month(month, year)
        return self.get_cancelled_new(start_date_str, period, prior=False)

    def gain_cancelled_in_range_new(self, start_date, end_date):
        # Need to convert from Pendulum datetime to datetime.datetime format
        start_created = datetime.fromtimestamp(start_date.timestamp(), pdl.tz.UTC)
        end_created = datetime.fromtimestamp(end_date.timestamp(), pdl.tz.UTC)

        gain = self.get_gain_in_date_range(start_created, end_created)
        cancelled = self.get_cancelled_in_date_range_new(start_created, end_created)
        return gain, cancelled
    
    def get_cancellations_new(self):
        return db.session.query(self.model)\
        .filter_by(booking_status = 'CANCELLED')\
        .filter(self.model._cancellation_datetime != None)\
        .all()
    
    def get_bookings_missing_locations(self):
        return db.session.query(self.model).filter(self.model.location == None).all()
        


booking_dao = BookingDAO(Booking)
