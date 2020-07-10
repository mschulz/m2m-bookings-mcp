# test_db.py

import unittest
import json
from datetime import datetime

from app import create_app, db
from app.models import Booking, import_dict, string_to_boolean


class TestQuery(unittest.TestCase):


    def setUp(self):
        self.app = create_app()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        

            
    def test_lead_source(self):
        data = {
            "id": "14450",
            "custom_fields": {
                "drop_down:65c938ba-a125-48ba-a21f-9fb34350ab24": "Google"
            }
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['custom_fields']["drop_down:65c938ba-a125-48ba-a21f-9fb34350ab24"]
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.lead_source == expected
            
    def test_team_member(self):
        data = {
            "id": "14450",
            "custom_fields": {
                "single_line:a3a07fee-eb4f-42ae-ab31-9977d4d1acf9": "MFS"
            }
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['custom_fields']["single_line:a3a07fee-eb4f-42ae-ab31-9977d4d1acf9"]
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.booked_by == expected
            
    def test_flexible_date_time(self):
        data = {
            "id": "14450",
            "custom_fields": {
                "drop_down:f5c6492a-82cc-41cf-8e0b-5390bea7d71b": "time yes, date no"
            }
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['custom_fields']["drop_down:f5c6492a-82cc-41cf-8e0b-5390bea7d71b"]
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.flexible_date_time == expected
            
    def test_invoice_name(self):
        data = {
            "id": "14450",
            "custom_fields": {
                "single_line:b382b477-5ddd-498e-ba36-74d55c7f0146": "Joe Blogs"
            }
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['custom_fields']["single_line:b382b477-5ddd-498e-ba36-74d55c7f0146"]
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.invoice_name == expected
            
    def test_invoice_email(self):
        data = {
            "id": "14450",
            "custom_fields": {
                "single_line:c131935b-e8cf-4ef9-b6ff-6068a674c49d": "me@example.com"
            }
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['custom_fields']["single_line:c131935b-e8cf-4ef9-b6ff-6068a674c49d"]
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.invoice_email == expected
            
    def test_invoice_reference(self):
        data = {
            "id": "14450",
            "custom_fields": {
                "single_line:73238370-80d8-4cbe-8577-74e3ade200a0": "123456768xx"
            }
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['custom_fields']["single_line:73238370-80d8-4cbe-8577-74e3ade200a0"]
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.invoice_reference == expected
            
    def test_invoice_tobe_emailed(self):
        data = {
            "id": "14450",
            "custom_fields": {
                "drop_down:a255d2c7-fb9a-4fa8-beb6-a91bc1ef6fed": "No"
            }
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = string_to_boolean(data['custom_fields']["drop_down:a255d2c7-fb9a-4fa8-beb6-a91bc1ef6fed"])
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.invoice_tobe_emailed == expected
            
    def test_NDIS_who_pays(self):
        data = {
            "id": "14450",
            "custom_fields": {
                "drop_down:5842d47d-52c9-4cff-ba42-f5b90ada72e5": "me@example.com"
            }
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['custom_fields']["drop_down:5842d47d-52c9-4cff-ba42-f5b90ada72e5"]
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.NDIS_who_pays == expected
            
    def test_NDIS_reference(self):
        data = {
            "id": "14450",
            "custom_fields": {
                "single_line:2b738d28-6c2c-4850-ae47-2c4902da9d8d": "987654321"
            }
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['custom_fields']["single_line:2b738d28-6c2c-4850-ae47-2c4902da9d8d"]
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.NDIS_reference == expected


if __name__ == '__main__':
    unittest.main()