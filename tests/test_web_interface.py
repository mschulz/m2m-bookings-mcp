# test_web.py

import unittest
import json
from datetime import datetime
from werkzeug import exceptions

from app import create_app, db
from app.models import Booking, import_dict, dollar_string_to_int, string_to_boolean

from tests.typical_JSON_data import web_dict

from random import choice
from string import ascii_uppercase


def generate_random_string(l):

    return (''.join(choice(ascii_uppercase) for i in range(l)))

class TestQuery(unittest.TestCase):


    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['DEBUG'] = False
        self.headers = { 'Authorization': f'Bearer {self.app.config["API_KEY"]}', 'Content-Type': 'application/json'}
        with self.app.app_context():
            db.drop_all()
            db.create_all()
        self.assertEqual(self.app.debug, False)


    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        
    def test_authorization_fail(self):
        with self.app.test_client() as c:
            response = c.get('/')
            assert response.status_code == 401
        
    def test_authorization_success(self):
        with self.app.test_client() as c:
            #headers = { 'Authorization': f'Bearer {self.app.config["API_KEY"]}', 'Content-Type': 'application/json'}
            response = c.get('/', headers=self.headers)
            assert response.status_code == 200
        
    def test_new_booking(self):
        with self.app.test_client() as c:
            headers = { 'Authorization': f'Bearer {self.app.config["API_KEY"]}', 'Content-Type': 'application/json'}
            response = c.post('/booking/new', headers=headers, data=json.dumps(web_dict))
            assert response.status_code == 200
            with self.app.app_context():
                b = db.session.query(Booking).filter(Booking.booking_id == 14450).first()
                assert b.name == "Zoe Nall"
                assert b.first_name == "Zoe"
        
    def test_IntegrityViolation_duplicates(self):
        with self.app.test_client() as c:
            headers = { 'Authorization': f'Bearer {self.app.config["API_KEY"]}', 'Content-Type': 'application/json'}
            response = c.post('/booking/new', headers=headers, data=json.dumps(web_dict))
            response = c.post('/booking/new', headers=headers, data=json.dumps(web_dict))
            # These are the same data, so ignored
            #print(f'test_IntegrityViolation_duplicates: {response.status_code}')
            assert response.status_code == 200
        
    def test_IntegrityViolation_differ(self):
        with self.app.test_client() as c:
            headers = { 'Authorization': f'Bearer {self.app.config["API_KEY"]}', 'Content-Type': 'application/json'}
            response = c.post('/booking/new', headers=headers, data=json.dumps(web_dict))
            
            w = web_dict.copy()
            w['updated_at'] = "2019-10-24T13:10:19+10:00"
            response = c.post('/booking/new', headers=headers, data=json.dumps(w))
            # These are the same data, so ignored
            #print(f'test_IntegrityViolation_differ: {response.status_code}')
            assert response.status_code == 500
        
    def test_update_booking(self):
        with self.app.test_client() as c:
            headers = { 'Authorization': f'Bearer {self.app.config["API_KEY"]}', 'Content-Type': 'application/json'}
            response = c.post('/booking/new', headers=headers, data=json.dumps(web_dict))
            # Now update the booking
            response = c.post('/booking/updated', headers=headers, data=json.dumps(web_dict))
            assert response.status_code == 200
            with self.app.app_context():
                b = db.session.query(Booking).filter(Booking.booking_id == 14450).first()
                assert b.name == "Zoe Nall"
                assert b.first_name == "Zoe"
        
    def test_booking_completed(self):
        with self.app.test_client() as c:
            headers = { 'Authorization': f'Bearer {self.app.config["API_KEY"]}', 'Content-Type': 'application/json'}
            response = c.post('/booking/new', headers=headers, data=json.dumps(web_dict))
            # Now update the booking
            response = c.post('/booking/completed', headers=headers, data=json.dumps(web_dict))
            assert response.status_code == 200
            with self.app.app_context():
                b = db.session.query(Booking).filter(Booking.booking_id == 14450).first()
                assert b.name == "Zoe Nall"
                assert b.first_name == "Zoe"
        
    def test_column_overflow(self):
        with self.app.test_client() as c:
            headers = { 'Authorization': f'Bearer {self.app.config["API_KEY"]}', 'Content-Type': 'application/json'}

            w = web_dict.copy()
            w['zip'] = generate_random_string(32) # string exceeds 16 characters in length.  Should generate a DataError exception
            response = c.post('/booking/new', headers=headers, data=json.dumps(w))
            print(response.status_code)
            with self.app.app_context():
                b = db.session.query(Booking).filter(Booking.booking_id == 14450).first()
                print(f'postcode = {b.postcode}')
                assert b.postcode == w['zip']
            assert response.status_code == 422
        
    def test_tags_overflow(self):
        with self.app.test_client() as c:
            headers = { 'Authorization': f'Bearer {self.app.config["API_KEY"]}', 'Content-Type': 'application/json'}

            w = web_dict.copy()
            w['customer']['tags'] = generate_random_string(80)
            response = c.post('/booking/new', headers=headers, data=json.dumps(w))
            print(response.status_code)
            assert response.status_code == 200



if __name__ == '__main__':
    unittest.main()