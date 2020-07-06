# test_db.py

import unittest
import json
from datetime import datetime

from app import create_app, db
from app.models import Booking, import_dict, dollar_string_to_int, string_to_boolean


class TestQuery(unittest.TestCase):


    def setUp(self):
        self.app = create_app()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        
    def test_booking_id(self):
        data = {
            "id": "14450"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = int(data['id'])
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.booking_id == expected
    
    def test_created_at(self):
        data = {
            "id": "14450",
            "created_at": "2018-10-24T13:10:19+10:00"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = datetime.strptime("2018-10-24 13:10:19", "%Y-%m-%d %H:%M:%S")
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.created_at == expected
    
    def test_updated_at(self):
        data = {
            "id": "14450",
            "updated_at": "2018-10-24T13:10:19+10:00"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = datetime.strptime("2018-10-24 13:10:19", "%Y-%m-%d %H:%M:%S")
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.updated_at == expected
            
    def test_service_times(self):
        data = {
            "id": "14450",
            "service_time": "12:00 - 12:30"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['service_time']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.service_time == expected
            
    def test_service_date(self):
        data = {
            "id": "14450",
            "service_date": "2018-10-26"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = datetime.strptime(data['service_date'], "%Y-%m-%d").date()
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.service_date == expected
            
    def test_final_price(self):
        data = {
            "id": "14450",
            "final_price": "$124.00"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = dollar_string_to_int(data['final_price'])
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.final_price == expected
            
    def test_extras_price(self):
        data = {
            "id": "14450",
            "extras_price": "$0.00"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = dollar_string_to_int(data['extras_price'])
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.extras_price == expected
            
    def test_subtotal(self):
        data = {
            "id": "14450",
            "subtotal": "$124.00"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = dollar_string_to_int(data['subtotal'])
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.subtotal == expected
            
    def test_tip(self):
        data = {
            "id": "14450",
            "tip": "$124.00"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = dollar_string_to_int(data['tip'])
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.tip == expected
            
    def test_payment_method(self):
        data = {
            "id": "14450",
            "payment_method": "stripe"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['payment_method']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.payment_method == expected
            
    def test_rating_value(self):
        data = {
            "id": "14450",
            "rating_value": "5"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = int(data['rating_value'])
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.rating_value == expected
            
    def test_rating_comment(self):
        data = {
            "id": "14450",
            "rating_value": "Great team"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['rating_value']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.rating_value == expected
            
    def test_rating_comment_presence(self):
        data = {
            "id": "14450",
            "rating_comment_presence": "true"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = string_to_boolean(data['rating_comment_presence'])
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.rating_comment_presence == expected
            
    def test_frequency(self):
        data = {
            "id": "14450",
            "frequency": "1 Time Service"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['frequency']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.frequency == expected
            
    def test_discount_code(self):
        data = {
            "id": "14450",
            "discount_code": "I have no idea - store as a string"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['discount_code']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.discount_code == expected
            
    def test_discount_from_code(self):
        data = {
            "id": "14450",
            "discount_amount": "$10.00"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = dollar_string_to_int(data['discount_amount'])
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.discount_from_code == expected
            
    def test_giftcard_amount(self):
        data = {
            "id": "14450",
            "giftcard_amount": "$0.00"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = dollar_string_to_int(data['giftcard_amount'])
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.giftcard_amount == expected
            
    def test_teams_assigned(self):
        data = {
            "id": "14450",
            "team_details": "[{u'phone': u'+6 (142) 695-8397', u'first_name': u'Irene & Yong', u'last_name': u'', u'image_url': u'', u'name': u'Irene & Yong', u'title': u'Team Euclid', u'id': u'8447'}]"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = json.loads(data['team_details'].replace("'", '"').replace('u"', '"'))[0]['title']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.teams_assigned == expected
            
    def test_teams_assigned_ids(self):
        data = {
            "id": "14450",
            "team_details": "[{u'phone': u'+6 (142) 695-8397', u'first_name': u'Irene & Yong', u'last_name': u'', u'image_url': u'', u'name': u'Irene & Yong', u'title': u'Team Euclid', u'id': u'8447'}]"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = json.loads(data['team_details'].replace("'", '"').replace('u"', '"'))[0]['id']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.teams_assigned_ids == expected
            
    def test_teams_share(self):
        data = {
            "id": "14450",
            "team_share_amount": "Team Euclid - $67.64"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['team_share_amount'].replace('$','').replace('.','')
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.team_share == expected
            
    def test_teams_share_total(self):
        data = {
            "id": "14450",
            "team_share_total": "Team Euclid - $67.64"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['team_share_total'].replace('$','').replace('.','')
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.team_share_total == expected
            
    def test_has_key(self):
        data = {
            "id": "14450",
            "team_has_key": "Yes"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = string_to_boolean(data['team_has_key'])
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.team_has_key == expected
            
    def test_team_requested(self):
        data = {
            "id": "14450",
            "team_requested": "Team Osprey"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['team_requested']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.team_requested == expected
            
    def test_created_by(self):
        data = {
            "id": "14450",
            "created_by": "Jennifer Parker"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['created_by']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.created_by == expected
            
    def test_next_booking_date(self):
        data = {
            "id": "14450",
            "next_booking_date": "2018-10-25T11:06:33+10:00"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = datetime.strptime(data['next_booking_date'].replace('+10:00', ''), "%Y-%m-%dT%H:%M:%S")
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.next_booking_date == expected
            
    def test_service_category(self):
        data = {
            "id": "14450",
            "service_category": "House Clean"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['service_category']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.service_category == expected
            
    def test_service(self):
        data = {
            "id": "14450",
            "service": "2 Bedroom"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['service']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.service == expected
            
    def test_customer_notes(self):
        data = {
            "id": "14450",
            "customer_notes": "I could write for ages, but just say that they are tops."
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['customer_notes']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.customer_notes == expected
            
    def test_staff_notes(self):
        data = {
            "id": "14450",
            "staff_notes": "I could write for ages, but just say that they are tops."
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['staff_notes']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.staff_notes == expected
            
    def test_customer_id(self):
        data = {
            "id": "14450",
            "customer": { "id": "8674" }
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = int(data['customer']['id'])
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.customer_id == expected
            
    def test_cancellation_type(self):
        data = {
            "id": "14450",
            "cancellation_type": "This Booking and all Future Bookings"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['cancellation_type']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.cancellation_type == expected
            
    def test_cancelled_by(self):
        data = {
            "id": "14450",
            "cancelled_by": "Jennifer Parker (Admin)"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['cancelled_by']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.cancelled_by == expected
            
    def test_cancellation_reason(self):
        data = {
            "id": "14450",
            "cancellation_reason": "NFS"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['cancellation_reason']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.cancellation_reason == expected
    
    def test_price_adjustment(self):
        data = {
            "id": "14450",
            "price_adjustment": "$10.00"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = dollar_string_to_int(data['price_adjustment'])
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.price_adjustment == expected
            
    def test_price_adjustment_comment(self):
        data = {
            "id": "14450",
            "price_adjustment_comment": "Feeling generous on the day"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['price_adjustment_comment']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.price_adjustment_comment == expected
            
    def test_booking_status(self):
        data = {
            "id": "14450",
            "booking_status": "Completed"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['booking_status']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.booking_status == expected
            
    def test_is_first_recurring(self):
        data = {
            "id": "14450",
            "is_first_recurring": "Yes"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = string_to_boolean(data['is_first_recurring'])
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.is_first_recurring == expected
            
    def test_is_new_customer(self):
        data = {
            "id": "14450",
            "is_new_customer": "No"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = string_to_boolean(data['is_new_customer'])
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.is_new_customer == expected
            
    def test_extras(self):
        data = {
            "id": "14450",
            "extras": "Completed"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['extras']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.extras == expected
            
    def test_source(self):
        data = {
            "id": "14450",
            "source": "Google"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['source']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.source == expected
            
    def test_sms_notifications_enabled(self):
        data = {
            "id": "14450",
            "sms_notifications_enabled": "Yes"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = string_to_boolean(data['sms_notifications_enabled'])
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.sms_notifications_enabled == expected
            
    def test_pricing_parameters(self):
        data = {
            "id": "14450",
            "pricing_parameters": "1 x Bathroom"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['pricing_parameters']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.pricing_parameters == expected
    
    def test_pricing_parameters_price(self):
        data = {
            "id": "14450",
            "pricing_parameters_price": "$10.00"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = dollar_string_to_int(data['pricing_parameters_price'])
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.pricing_parameters_price == expected
            
    def test_address(self):
        data = {
            "id": "14450",
            "address": "1/121 Stock Rd, Unit"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['address']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.address == expected
            
    def test_last_name(self):
        data = {
            "id": "14450",
            "last_name": "Nall"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['last_name']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.last_name == expected
            
    def test_city(self):
        data = {
            "id": "14450",
            "city": "Attadale"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['city']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.city == expected
            
    def test_state(self):
        data = {
            "id": "14450",
            "state": "WA"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['state']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.state == expected
            
    def test_first_name(self):
        data = {
            "id": "14450",
            "first_name": "Zoe"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['first_name']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.first_name == expected
            
    def test_company_name(self):
        data = {
            "id": "14450",
            "company_name": "ACME Gadgets"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['company_name']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.company_name == expected
            
    def test_email(self):
        data = {
            "id": "14450",
            "email": "karenann1@hotmail.com"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['email']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.email == expected
            
    def test_name(self):
        data = {
            "id": "14450",
            "name": "Zoe Nall"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['name']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.name == expected
            
    def test_phone(self):
        data = {
            "id": "14450",
            "phone": "0412328484"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['phone']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.phone == expected
            
    def test_postcode(self):
        data = {
            "id": "14450",
            "zip": "6157"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['zip']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.postcode == expected
            
    def test_location(self):
        data = {
            "id": "14450",
            "location": "Maid2Match Perth"
        }
        with self.app.app_context():
            b = Booking()
            import_dict(b, data)
            db.session.add(b)
            db.session.commit()
        
            expected = data['location']
            result = db.session.query(Booking).filter(Booking.booking_id == data['id']).first()
            assert result.location == expected



if __name__ == '__main__':
    unittest.main()