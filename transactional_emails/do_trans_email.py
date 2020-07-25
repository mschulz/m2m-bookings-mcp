from datetime import datetime, timedelta

from app import create_app, db
from flask import current_app
from app.models import Booking
from app.post_to_sendinblue import post_to_sendinblue, build_payload
from sqlalchemy import and_, or_


def booking_confirmation_email(db):
    

    def count_new_jobs(db):
        res = db.session.query(Booking).filter(
                                            and_(
                                              Booking.booking_status == 'NOT_COMPLETE',
                                                 or_(
                                                     Booking.frequency == '1 Time Service',
                                                     Booking.is_first_recurring)
                                                )
                                            ).count()
        return res

    def find_row_first(db):
        res = db.session.query(Booking).filter(
                                            and_(
                                              Booking.booking_status == 'NOT_COMPLETE',
                                                 or_(
                                                     Booking.frequency == '1 Time Service',
                                                     Booking.is_first_recurring)
                                                )
                                            ).all()
        for item in res:
            yield item
    
    with app.app_context():
        template_id = current_app.config['TEMPLATE_ID_CONFIRMATION']
        if app.testing:
            res = count_new_jobs(db)
            print(f'Number booking confirmations:{res} template_id={template_id}')
        else:
            for idx, item in enumerate(find_row_first(db)):
                email = 'mark.f.schulz@gmail.com' #item.email
                name = item.name
                data = build_payload(email, name, template_id, item)
                p = data['params']
                print(f"{idx}:  email: {email} is_first_recurring: {item.is_first_recurring} service: {item.service}")
                post_to_sendinblue(data)
                
                return

def contact_n_days_out(db, n, template_id):

    def count_n_days_out(db, n):
        n_days_away = (datetime.today() + timedelta(days=n)).date()
    
        print(f'today={datetime.today().date()} {n}_day{"s" if n != 1 else ""}_away={n_days_away}')
    
        return db.session.query(Booking).filter(Booking.service_date == n_days_away).count()

    def find_n_days_out(db, n):
        n_days_away = (datetime.today() + timedelta(days=n)).date()
    
        print(f'today={datetime.today().date()} {n}_days_away={n_days_away}')
    
        res = db.session.query(Booking).filter(Booking.service_date == n_days_away).all()

        for item in res:
            yield item

    with app.app_context():
        if app.testing:
            print(f'Number jobs {n} day{"s" if n != 1 else ""} out:{count_n_days_out(db, n)} template_id={template_id}')
        else:
            for idx, item in enumerate(find_n_days_out(db, n)):
                email = 'mark.f.schulz@gmail.com' #item.email
                name = item.name
                data = build_payload(email, name, template_id, item)
                p = data['params']
                print(f"{idx}:  email: {email} service_date: {item.service_date} service: {item.service}")
                post_to_sendinblue(data)
                return

if __name__ == '__main__':
    
    app = create_app()

    with app.app_context():
        booking_confirmation_email(db)
        contact_n_days_out(db, 1, app.config['TEMPLATE_ID_FIRST_HEADSUP'])
        contact_n_days_out(db, 3, app.config['TEMPLATE_ID_SECOND_HEADSUP'])
    