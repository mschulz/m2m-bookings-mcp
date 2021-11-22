# app/database/upload_booking_csv.py

import os
import sys
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
    
    print(sys.argv)

    app = create_app()

    commit_flag = False
    
    with app.app_context():
        if len(sys.argv) == 3:
            filename = sys.argv[1]
            if sys.argv[2] == '-c':
                commit_flag = True
            else:
                print(f'Invalid flag: {sys.argv[2]}')
                sys.exit(1)
        elif len(sys.argv) == 2:
            filename = sys.argv[1]
            commit_flag = False
        else:
            print(f'MIssing filename: {sys.argv}')
            sys.exit(1)

        print(f'{filename = } {commit_flag = }')
        sheet = Spreadsheet(filename)
        
        for row in sheet.get_row():
            # ID,Name,Email,Phone,Address,City,State,Postcode,Date & Time,Service Category,Service Type,Frequency,Final Price,Created By,Created At
            was_first_recurring = False
            booking_id = int(row[0])
            was_first_recurring = row[1] == 'TRUE'
                
            #print(f'{booking_id} == {was_first_recurring}')
            
            res = db.session.query(Booking).filter(Booking.booking_id == booking_id).first()
            if res is None:
                print(f'{booking_id} was not found')
            elif res.was_first_recurring != was_first_recurring:
                    print(f'{booking_id = } {res.was_first_recurring = } => {was_first_recurring = }')
                    res.was_first_recurring = was_first_recurring
                    if commit_flag:
                        print('db.session.commit()')
                        try:
                            db.session.commit()
                        except exc.SQLAlchemyError as e:
                            app.logger.error('Unable to add booking/customer to database')
                            app.logger.error(e)
                            db.session.rollback()
            else:
                print(f'{booking_id = } no change')
       
        db.session.close()

if __name__ == '__main__':
    main()

