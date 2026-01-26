# app/daos.py

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
from app.models import (
    Booking,
    Customer,
    import_dict,
    import_customer,
    import_cancel_dict,
)
from app.models_reservation import Reservation
from app.models_sales_reservation import SalesReservation
from app.models_reservation import import_dict as res_import_dict
from app.models_reservation import import_cancel_dict as res_import_cancel_dict
from calendar import monthrange
from app.local_date_time import utc_to_local
from config import Config
from sqlalchemy import exc, and_
from flask import current_app, request, abort


class BookingDAO:
    def __init__(self, model):
        self.model = model

    def get_by_booking_id(self, booking_id):
        return db.session.query(self.model).filter_by(booking_id=booking_id).first()

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
            offsets = ((-1, 5), (-2, 4), (-3, 3), (-4, 2), (-5, 1), (-6, 0), (0, 6))
            week_start = dt + timedelta(days=offsets[dow][0])
            week_end = dt + timedelta(days=offsets[dow][1])
            week_start_str = week_start.strftime("%Y-%m-%d")
            week_end_str = week_end.strftime("%Y-%m-%d")
            return (week_start_str, week_end_str)

        week_start, week_end = get_week_start_end(service_date)

        return (
            db.session.query(self.model)
            .filter_by(email=email)
            .filter(
                and_(
                    self.model._service_date >= week_start,
                    self.model._service_date <= week_end,
                )
            )
            .first()
        )

    def create_update_booking(self, new_data):
        booking_id = new_data["id"] if "id" in new_data else None
        if not booking_id:
            # This is a malformed set of data (this test might be redundant)
            current_app.logger.error("booking has no booking_id - ignore this data")
            abort(422, description="booking has no booking_id - ignore this data")

        # Check if we already have a booking under this id
        b = db.session.query(self.model).filter_by(booking_id=booking_id).first()

        if b is None:
            # Haven't seen the original booking - ADD it now
            current_app.logger.info("haven't seen this booking - ADDING to database")

            # Load the database table
            b = Booking()
            import_dict(b, new_data)
            db.session.add(b)
        else:
            # Have seen the original booking - UPDATE it now
            current_app.logger.info("have seen this booking - UPDATING database")

            import_dict(b, new_data)

            current_app.logger.info(
                f'Loading ... Name: "{b.name}" team: "{b.teams_assigned}" booking_id: {b.booking_id}'
            )

        try:
            db.session.commit()
            # current_app.logger.info(f'Data loaded into database: {b.to_dict()}')
        except exc.DataError:
            abort(422, description=f"Data loaded into database: {b.to_dict()}")
        except exc.IntegrityError:
            db.session.rollback()
            current_app.logger.info(f"Data already loaded into database: {b.to_dict()}")
        except exc.OperationalError:
            db.session.rollback()
            current_app.logger.info("SSL connection has been closed unexpectedly")

    def update_booking(self, new_data):
        booking_id = new_data["booking_id"] if "booking_id" in new_data else None
        b = db.session.query(self.model).filter_by(booking_id=booking_id).first()
        current_app.logger.info("have seen this booking - UPDATING database")

        import_cancel_dict(b, new_data)

        current_app.logger.info(
            f'Loading ... Name: "{b.name}" team: "{b.teams_assigned}" booking_id: {b.booking_id}'
        )

        try:
            db.session.commit()
            # current_app.logger.info(f'Data loaded into database: {b.to_dict()}')
        except exc.DataError:
            abort(422, description=f"Data loaded into database: {b.to_dict()}")
        except exc.IntegrityError:
            db.session.rollback()
            current_app.logger.info(f"Data already loaded into database: {b.to_dict()}")
        except exc.OperationalError:
            db.session.rollback()
            current_app.logger.info("SSL connection has been closed unexpectedly")

    def get_by_date_range(
        self, service_category, booking_status, start_created, end_created
    ):
        print(
            f"params: category={service_category} date={start_created},{end_created} booking_status={booking_status}"
        )

        return (
            db.session.query(self.model)
            .filter_by(service_category=service_category, booking_status=booking_status)
            .filter(
                and_(
                    self.model._created_at >= start_created,
                    self.model._created_at <= end_created,
                )
            )
            .all()
        )

    def completed_bookings_by_service_date(self, from_date, to_date):
        # print(f'params: from={from_date} to={to_date}')

        return (
            db.session.query(self.model)
            .filter_by(booking_status="COMPLETED")
            .filter(
                and_(
                    self.model._service_date >= from_date,
                    self.model._service_date <= to_date,
                )
            )
            .all()
        )
        """return db.session.query(self.model) \
            .filter_by(_service_date = from_date) \
            .all()"""

    def date_to_UTC_date(self, date_str):
        local = pytz.timezone(Config.TZ_LOCALTIME)
        naive = datetime.strptime(date_str, "%Y-%m-%d")
        local_dt = local.localize(naive, is_dst=Config.TZ_ISDST)
        utc_dt = local_dt.astimezone(pytz.utc)

        # print(f'str={date_str} naive={naive} local_dt={local_dt} utc_dt={utc_dt}')

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
        items = (
            db.session.query(self.model)
            .filter_by(was_first_recurring=True)
            .filter(self.model._created_at >= date_start)
            .filter(self.model._created_at < date_end)
            .distinct(self.model._customer_id)
        )
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
        date_start, date_end = self._find_dates_range(
            start_date_str, period_days, prior
        )
        return self.get_gain_in_date_range(date_start, date_end)

    def get_gain_list(self, start_date_str, period_days, prior=True):
        """
        get count from start_date_str for period_days PRIOR to that date
        """
        date_start, date_end = self._find_dates_range(
            start_date_str, period_days, prior
        )
        return self.get_gain_in_date_range_list(date_start, date_end)

    def _get_days_in_month(self, month, year):
        if isinstance(month, str):
            month = int(month)
        if isinstance(year, str):
            year = int(year)
        _, period = monthrange(year, month)
        start_date_str = f"{year}-{month:02}-01"
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
        date_start, date_end = self._find_dates_range(
            start_date_str, period_days, prior
        )
        return self.get_cancelled_in_date_range(date_start, date_end)

    def _get_cancelled_in_date_range(self, date_start, date_end):
        items = (
            db.session.query(self.model)
            .filter_by(cancellation_type="This Booking and all Future Bookings")
            .filter(self.model._cancellation_date >= date_start)
            .filter(self.model._cancellation_date < date_end)
            .distinct(self.model._customer_id)
        )
        return items

    def get_cancelled_in_date_range(self, date_start, date_end):
        items = self._get_cancelled_in_date_range(date_start, date_end)

        items_cancelled = [item.booking_id for item in items.all()]
        print(f"get_cancelled_in_date_range({len(items_cancelled)}): {items_cancelled}")

        return items.count()

    def get_cancelled_in_date_range_list(self, date_start, date_end):
        items = self._get_cancelled_in_date_range(date_start, date_end)
        return [item.booking_id for item in items.all()]

    def get_cancelled_list(self, start_date_str, period_days, prior=True):
        date_start, date_end = self._find_dates_range(
            start_date_str, period_days, prior
        )
        res = self._get_cancelled_in_date_range_list(date_start, date_end).all()
        return [item.booking_id for item in res]

    def get_cancelled_by_month(self, month, year):
        start_date_str, period = self._get_days_in_month(month, year)
        return self.get_cancelled(start_date_str, period, prior=False)

    # Current Recurring customer count
    def recurring_current(self):
        return (
            db.session.query(self.model)
            .filter(self.model.service_date >= utc_to_local(datetime.utcnow()).date())
            .filter_by(booking_status="NOT_COMPLETE")
            .filter(self.model.frequency != "1 Time Service")
            .distinct(self.model._customer_id)
            .count()
        )

    def gain_cancelled_in_range(self, start_date, end_date):
        # Need to convert from Pendulum datetime to datetime.datetime format
        start_created = datetime.fromtimestamp(start_date.timestamp(), pdl.tz.UTC)
        end_created = datetime.fromtimestamp(end_date.timestamp(), pdl.tz.UTC)

        gain = self.get_gain_in_date_range(start_created, end_created)
        cancelled = self.get_cancelled_in_date_range(start_created, end_created)
        return gain, cancelled

    def get_cancellations(self):
        return (
            db.session.query(self.model)
            .filter_by(booking_status="CANCELLED")
            .filter(self.model._cancellation_date is not None)
            .all()
        )

    def get_missing_cancellations(self):
        return (
            db.session.query(self.model)
            .filter_by(booking_status="CANCELLED")
            .filter(self.model._cancellation_date is None)
            .all()
        )

    #### CANCELLATION Calculations NEW!!!!####

    def get_cancelled_new(self, start_date_str, period_days, prior=True):
        """
        get count from start_date_str for period_days PRIOR to that date
        """
        date_start, date_end = self._find_dates_range(
            start_date_str, period_days, prior
        )
        return self.get_cancelled_in_date_range_new(date_start, date_end)

    def _get_cancelled_in_date_range_new(self, date_start, date_end):
        items = (
            db.session.query(self.model)
            .filter_by(cancellation_type="This Booking and all Future Bookings")
            .filter(self.model._cancellation_datetime >= date_start)
            .filter(self.model._cancellation_datetime < date_end)
            .distinct(self.model._customer_id)
        )
        return items

    def get_cancelled_in_date_range_new(self, date_start, date_end):
        items = self._get_cancelled_in_date_range_new(date_start, date_end)
        return items.count()

    def get_cancelled_in_date_range_list_new(self, date_start, date_end):
        items = self._get_cancelled_in_date_range_new(date_start, date_end)
        return [item.booking_id for item in items.all()]

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
        return (
            db.session.query(self.model)
            .filter_by(booking_status="CANCELLED")
            .filter(self.model._cancellation_datetime is not None)
            .all()
        )


booking_dao = BookingDAO(Booking)


class ReservationDAO:
    def __init__(self, model):
        self.model = model

    def get_by_booking_id(self, booking_id):
        return db.session.query(self.model).filter_by(booking_id=booking_id).first()

    def create_update_booking(self, new_data):
        booking_id = new_data["id"] if "id" in new_data else None
        if not booking_id:
            # This is a malformed set of data (this test might be redundant)
            current_app.logger.error("reservation has no booking_id - ignore this data")
            abort(422, description="reservation has no booking_id - ignore this data")

        # Check if we already have a booking under this id
        b = db.session.query(self.model).filter_by(booking_id=booking_id).first()

        if b is None:
            # Haven't seen the original booking - ADD it now
            current_app.logger.info(
                "haven't seen this reservation - ADDING to database"
            )

            # Load the database table
            b = Reservation()
            res_import_dict(b, new_data)
            db.session.add(b)
        else:
            # Have seen the original booking - UPDATE it now
            current_app.logger.info("have seen this NDIS reservation - UPDATING table")

            res_import_cancel_dict(b, new_data)

            current_app.logger.info(
                f'Loading ... Name: "{b.name}" team: "{b.teams_assigned}" booking_id: {b.booking_id}'
            )

        try:
            db.session.commit()
            # info(f'reservation loaded into database: {b.to_dict()}')
        except exc.DataError:
            abort(422, description=f"NDIS reservation loaded into table: {b.to_dict()}")
        except exc.IntegrityError:
            db.session.rollback()
            current_app.logger.info(
                f"NDIS reservation already loaded into table: {b.to_dict()}"
            )
        except exc.OperationalError:
            db.session.rollback()
            current_app.logger.info("SSL connection has been closed unexpectedly")

    def update_booking(self, new_data):
        booking_id = new_data["booking_id"] if "booking_id" in new_data else None
        b = db.session.query(self.model).filter_by(booking_id=booking_id).first()
        current_app.logger.info("have seen this NDIS reservation - UPDATING table")

        res_import_cancel_dict(b, new_data)

        current_app.logger.info(
            f'Loading ... Name: "{b.name}" team: "{b.teams_assigned}" booking_id: {b.booking_id}'
        )

        try:
            db.session.commit()
            # current_app.logger.info(f'Data loaded into database: {b.to_dict()}')
        except exc.DataError:
            abort(422, description=f"Data loaded into table: {b.to_dict()}")
        except exc.IntegrityError:
            db.session.rollback()
            current_app.logger.info(f"Data already loaded into table: {b.to_dict()}")
        except exc.OperationalError:
            db.session.rollback()
            current_app.logger.info("SSL connection has been closed unexpectedly")

    def cancel_booking(self, new_data):
        booking_id = new_data["id"] if "id" in new_data else None
        if booking_id is None:
            return
        db.session.query(self.model).filter_by(booking_id=booking_id).delete()
        try:
            db.session.commit()
            current_app.logger.info(
                f"NDIS Reservation deleted from table: {booking_id}"
            )
        except exc.DataError:
            abort(422, description=f"Reservation data error: {new_data}")
        except exc.IntegrityError:
            db.session.rollback()
            current_app.logger.info(f"NDIS Reservation Inegrity error: {new_data}")
        except exc.OperationalError:
            db.session.rollback()
            current_app.logger.info("SSL connection has been closed unexpectedly")

    def mark_converted(self, booking_id):
        if booking_id is None:
            return
        b = db.session.query(self.model).filter_by(booking_id=booking_id).first()
        current_app.logger.info("mark this booking as CONVERTED in database")
        b.booking_status = "CONVERTED"
        try:
            db.session.commit()
            current_app.logger.info(
                f"NDIS Reservation status changed to CONVERTED: {booking_id=}"
            )
        except exc.DataError:
            abort(422, description=f"NDIS Reservation data error: {booking_id=}")
        except exc.IntegrityError:
            db.session.rollback()
            current_app.logger.info(f"NDIS Reservation Inegrity error: {booking_id=}")
        except exc.OperationalError:
            db.session.rollback()
            current_app.logger.info("SSL connection has been closed unexpectedly")


reservation_dao = ReservationDAO(Reservation)


class SalesReservationDAO:
    def __init__(self, model):
        self.model = model

    def get_by_booking_id(self, booking_id):
        return db.session.query(self.model).filter_by(booking_id=booking_id).first()

    def create_update_booking(self, new_data):
        booking_id = new_data["id"] if "id" in new_data else None
        if not booking_id:
            # This is a malformed set of data (this test might be redundant)
            current_app.logger.error(
                "sales reservation has no booking_id - ignore this data"
            )
            abort(
                422,
                description="sales reservation has no booking_id - ignore this data",
            )

        # Check if we already have a booking under this id
        b = db.session.query(self.model).filter_by(booking_id=booking_id).first()

        if b is None:
            # Haven't seen the original booking - ADD it now
            current_app.logger.info(
                "haven't seen this sales reservation - ADDING to table"
            )

            # Load the database table
            b = SalesReservation()
            res_import_dict(b, new_data)
            db.session.add(b)
        else:
            # Have seen the original booking - UPDATE it now
            current_app.logger.info("have seen this sales reservation - UPDATING table")

            res_import_cancel_dict(b, new_data)

            current_app.logger.info(
                f'Loading ... Name: "{b.name}" team: "{b.teams_assigned}" booking_id: {b.booking_id}'
            )

        try:
            db.session.commit()
            # info(f'reservation loaded into database: {b.to_dict()}')
        except exc.DataError:
            abort(
                422, description=f"sales reservation loaded into table: {b.to_dict()}"
            )
        except exc.IntegrityError:
            db.session.rollback()
            current_app.logger.info(
                f"sales reservation already loaded into table: {b.to_dict()}"
            )
        except exc.OperationalError:
            db.session.rollback()
            current_app.logger.info("SSL connection has been closed unexpectedly")

    def update_booking(self, new_data):
        booking_id = new_data["booking_id"] if "booking_id" in new_data else None
        b = db.session.query(self.model).filter_by(booking_id=booking_id).first()
        current_app.logger.info(
            "have seen this booking - UPDATING sales reservation table"
        )

        res_import_cancel_dict(b, new_data)

        current_app.logger.info(
            f'Loading ... Name: "{b.name}" team: "{b.teams_assigned}" booking_id: {b.booking_id}'
        )

        try:
            db.session.commit()
            # current_app.logger.info(f'Data loaded into database: {b.to_dict()}')
        except exc.DataError:
            abort(422, description=f"Data loaded into table: {b.to_dict()}")
        except exc.IntegrityError:
            db.session.rollback()
            current_app.logger.info(f"Data already loaded into table: {b.to_dict()}")
        except exc.OperationalError:
            db.session.rollback()
            current_app.logger.info("SSL connection has been closed unexpectedly")

    def cancel_booking(self, new_data):
        booking_id = new_data["id"] if "id" in new_data else None
        if booking_id is None:
            return
        db.session.query(self.model).filter_by(booking_id=booking_id).delete()
        try:
            db.session.commit()
            current_app.logger.info(
                f"Sales Reservation deleted from table: {booking_id}"
            )
        except exc.DataError:
            abort(422, description=f"Sales Reservation data error: {new_data}")
        except exc.IntegrityError:
            db.session.rollback()
            current_app.logger.info(f"Sales Reservation Inegrity error: {new_data}")
        except exc.OperationalError:
            db.session.rollback()
            current_app.logger.info("SSL connection has been closed unexpectedly")

    def mark_converted(self, booking_id):
        if booking_id is None:
            return
        b = db.session.query(self.model).filter_by(booking_id=booking_id).first()
        current_app.logger.info("mark this booking as CONVERTED in table")
        b.booking_status = "CONVERTED"
        try:
            db.session.commit()
            current_app.logger.info(
                f"Sales Reservation status changed to CONVERTED: {booking_id=}"
            )
        except exc.DataError:
            abort(422, description=f"Sales Reservation data error: {booking_id=}")
        except exc.IntegrityError:
            db.session.rollback()
            current_app.logger.info(f"Sales Reservation Inegrity error: {booking_id=}")
        except exc.OperationalError:
            db.session.rollback()
            current_app.logger.info("SSL connection has been closed unexpectedly")


sales_reservation_dao = SalesReservationDAO(SalesReservation)


class CustomerDAO:
    def __init__(self, model):
        self.model = model

    def get_by_customer_id(self, customer_id):
        return db.session.query(self.model).filter_by(customer_id=customer_id).first()

    def create_or_update_customer(self, data):
        # Update the customer information table, if it has been updated since the last time it was stored
        # current_app.logger.info(f'Customer data received: {data}')

        c = db.session.query(self.model).filter_by(customer_id=data["id"]).first()
        if c is None:
            # Nothing stored about this customer, so create a new row in the table
            c = Customer()
            import_customer(c, data)
            db.session.add(c)
            current_app.logger.info("Create row for new customer data")
        else:
            # Check if there is updated data in the customer fields
            # First get the updated_at time from the stored data
            stored_update_time = c.updated_at
            import_customer(c, data)
            new_update_time = c.updated_at

            # Check if the data has been updated since the last time it was stored in the table
            if stored_update_time == new_update_time:
                current_app.logger.info("No change to customer data")
                return
        try:
            db.session.commit()
            current_app.logger.info(f"({request.path}) Updated Customer data")
        except exc.DataError as e:
            db.session.rollback()
            abort(422, description=f"Customer error in model data: {e}")
        except exc.OperationalError:
            db.session.rollback()
            current_app.logger.info("SSL connection has been closed unexpectedly")


customer_dao = CustomerDAO(Customer)


if __name__ == "__main__":
    from app import create_app

    def get_month_by_year(year):
        for month in range(1, 13, 1):
            gain = booking_dao.get_gain_by_month(month, year)
            cancelled = booking_dao.get_cancelled_by_month(month, year)
            print(
                f"{year}-{month}: gain={gain} cancelled={cancelled} nett={gain - cancelled}"
            )

    def get_daily(init_total, start_date_str, end_date_str):
        print("Reccuring customer totals")

        date_d = datetime.utcnow().astimezone(pytz.utc)
        end_date_str = "2021-10-01"
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").astimezone(pytz.utc)
        print(f"start at {date_d}")
        total = init_total
        while date_d > end_date:
            date_str = date_d.strftime("%Y-%m-%d")
            gain = booking_dao.get_gain(date_str, 1)
            cancelled = booking_dao.get_cancelled(date_str, 1)

            date_d = date_d - timedelta(days=1)

            print(
                f"{date_str}: total = {total} gain={gain} cancelled={cancelled} nett={gain - cancelled}"
            )
            total -= gain - cancelled
        return total

    app = create_app()

    with app.app_context():
        start_str = "2022-05-05"
        period = 1

        """
        gain = booking_dao.get_gain(start_str, period)
        print(f'Customers_gained={gain}')

        cancelled = booking_dao.get_cancelled(start_str, period)
        print(f'Customers lost={cancelled}')

        gain = booking_dao.get_gain_by_month(month, 2021)
        print(f'Customers gained in month {month}={gain}')

        cancelled = booking_dao.get_cancelled_by_month(month, 2021)
        print(f'Customers lostin month (month)={cancelled}')

        current = booking_dao.recurring_current()
        print(f'Recurring customer count today={current}')"""

        ### Daily totals
        """start_date_str = "2021-10-21"
        end_date_str = "2021-10-01"
        init_total = 684
        print("Reccuring customer totals")
        total = get_daily(init_total, start_date_str, end_date_str)
        print(f'Monthly Nett: {init_total-total}\n')"""

        ### Get yearly, nett by month
        """print("Monthly totals for a specific year")
        year = 2021
        get_month_by_year(year)"""

        """print(f'Date: {start_str} -- looking at prior day')

        date_start, date_end = booking_dao._find_dates_range(start_str, 1, True)
        print(f'{date_start = }  {date_end = }')
        local_date_start = utc_to_local(date_start)
        local_date_end = utc_to_local(date_end)
        print(f'{local_date_start = }  {local_date_end = }')
        
        gain = booking_dao.get_gain(start_str, period)
        print(f'Customers_gained={gain}')

        cancelled = booking_dao.get_cancelled(start_str, period)
        print(f'Customers cancelled={cancelled}')
        
        cancel_list = booking_dao.get_cancelled_list(start_str, period)
        print(f'Customers cancel list={cancel_list}')"""

        """start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        
        items = booking_dao.completed_bookings_by_service_date(start_date, start_date)
        print(items)"""

        # Get booking details from email and service_date
        # first_name='Jerome' email='jeromeadkins1954@icloud.com' service_date=datetime.datetime(2024, 3, 13, 0, 0) rating='5' comment='The cleaner is on time and is polite and and does a good job'
        print(" Get booking details from email and service_date")
        email = "jeromeadkins1954@icloud.com"
        service_date = "2024-03-13"
        item = booking_dao.get_by_booking_email_service_date_range(email, service_date)
        print(item)
        if item:
            print(item.to_dict())
