# test_web.py

import unittest
import json
from datetime import datetime

from app import create_app, db
from app.models import Booking, import_dict, dollar_string_to_int, string_to_boolean

from app.tests import typical_JSON_data


class TestQuery(unittest.TestCase):


    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['DEBUG'] = False
        with self.app.app_context():
            db.drop_all()
            db.create_all()
        self.assertEqual(app.debug, False)


    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def get_result(self, data):
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
            return db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
        
    def test_main_page(self):
        response = self.app.get('/')
        assert response.status_code == 200
