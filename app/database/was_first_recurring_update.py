# app/database/upload_booking_csv.py

import os
from datetime import datetime
from .. import create_app
from app import db
from app.models import Booking
from sqlalchemy import exc
from .spreadsheet import Spreadsheet


def main():
    ''' Upload data to the  sales database.  Should only call this once. 
        saves the is_first_recurring data in was_first_recurring as the forer gets overwritten
    '''

    app = create_app()

    with app.app_context():
        if app.config['COMPANY_NAME'] == 'Maid2Match':
            sheet = Spreadsheet('app/database/was_first_recurring_data_m2m.csv')
        elif app.config['COMPANY_NAME'] == 'Lawn.com.au':
            sheet = Spreadsheet('app/database/was_first_recurring_data_lca.csv')
    
        for row in sheet.get_row():
            # ID,Name,Email,Phone,Address,City,State,Postcode,Date & Time,Service Category,Service Type,Frequency,Final Price,Created By,Created At
            commit_flag = False
            booking_id = row[0]
            if app.config['COMPANY_NAME'] == 'Maid2Match':
                was_first_recurring = row[1] == 'TRUE'
            elif app.config['COMPANY_NAME'] == 'Lawn.com.au':
                was_first_recurring = row[2] == 'TRUE'
                
            print(f'{booking_id} == {was_first_recurring}')
            
            res = db.session.query(Booking).filter(Booking.booking_id == booking_id).first()
            if res is None:
                print(f'{booking_id} was not found')
            else:
                res.was_first_recurring = was_first_recurring
                try:
                    db.session.commit()
                except exc.SQLAlchemyError as e:
                    app.logger.error('Unable to add booking/customer to database')
                    app.logger.error(e)
                    db.session.rollback()
       
        db.session.close()

if __name__ == '__main__':
    main()

