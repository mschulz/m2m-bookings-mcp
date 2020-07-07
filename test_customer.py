# test_customer.py

import unittest
import json
from datetime import datetime

from app import create_app, db
from app.models import Customer, import_customer


class TestQuery(unittest.TestCase):
    
    def setUp(self):
        self.app = create_app()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def get_result(self, data):
        with self.app.app_context():
            b = Customer()
            import_customer(b, data)
            db.session.add(b)
            db.session.commit()
            return db.session.query(Customer).filter(Customer.customer_id == data['id']).first()

        
    def test_customer_id(self):
        data = {
            "id": "8674"
        }
        expected = int(data['id'])
        result = self.get_result(data)
        assert result.customer_id == expected
    
    def test_created_at(self):
        data = {
            "id": "8674",
            "created_at": "2018-10-24T13:10:19+10:00"
        }
        expected = datetime.strptime("2018-10-24T13:10:19", "%Y-%m-%dT%H:%M:%S")
        result = self.get_result(data)
        assert result.created_at == expected
    
    def test_updated_at(self):
        data = {
            "id": "8674",
            "updated_at": "2018-10-24T13:10:19+10:00"
        }
        expected = datetime.strptime("2018-10-24T13:10:19", "%Y-%m-%dT%H:%M:%S")
        result = self.get_result(data)
        assert result.updated_at == expected
            
    def test_title(self):
        data = {
            "id": "14450",
            "title": ""
        }
        expected = data['title']
        result = self.get_result(data)
        assert result.title == expected
            
    def test_first_name(self):
        data = {
            "id": "14450",
            "first_name": "Zoe"
        }
        expected = data['first_name']
        result = self.get_result(data)
        assert result.first_name == expected
            
            
    def test_last_name(self):
        data = {
            "id": "14450",
            "last_name": "Nall"
        }
        expected = data['last_name']
        result = self.get_result(data)
        assert result.last_name == expected
            
    def test_name(self):
        data = {
            "id": "14450",
            "name": "Zoe Nall"
        }
        expected = data['name']
        result = self.get_result(data)
        #print(f'expected: {expected}({type(expected)}) result {result.created_at}({type(result.created_at)})')
        assert result.name == expected
            
    def test_email(self):
        data = {
            "id": "14450",
            "email": "karenann1@hotmail.com"
        }
        expected = data['email']
        result = self.get_result(data)
        assert result.email == expected
            
    def test_phone(self):
        data = {
            "id": "14450",
            "phone": "0412328484"
        }
        expected = data['phone']
        result = self.get_result(data)
        assert result.phone == expected

    def test_address(self):
        data = {
            "id": "14450",
            "address": "1/121 Stock Rd, Unit"
        }
        expected = data['address']
        result = self.get_result(data)
        assert result.address == expected
            
    def test_city(self):
        data = {
            "id": "14450",
            "city": "Attadale"
        }
        expected = data['city']
        result = self.get_result(data)
        assert result.city == expected
            
    def test_state(self):
        data = {
            "id": "14450",
            "state": "WA"
        }
        expected = data['state']
        result = self.get_result(data)
        assert result.state == expected
            
    def test_company_name(self):
        data = {
            "id": "14450",
            "company_name": "ACME Gadgets"
        }
        expected = data['company_name']
        result = self.get_result(data)
        assert result.company_name == expected
            
    def test_postcode(self):
        data = {
            "id": "14450",
            "zip": "6157"
        }
        expected = data['zip']
        result = self.get_result(data)
        assert result.postcode == expected
            
    def test_location(self):
        data = {
            "id": "14450",
            "location": "Maid2Match Perth"
        }
        expected = data['location']
        result = self.get_result(data)
        assert result.location == expected
            
    def test_tags(self):
        data = {
            "id": "14450",
            "tags": "abc"
        }
        expected = data['tags']
        result = self.get_result(data)
        assert result.tags == expected
            
    def test_notes(self):
        data = {
            "id": "14450",
            "notes": "aaaaaaaaaaaaaaaaaaaaaaaaaaa bbbbbbbbbbbbbbbbbbbbbb bbbbbbbbbbbb cccccccccccccccccccccc"
        }
        expected = data['notes']
        result = self.get_result(data)
        assert result.notes == expected


if __name__ == '__main__':
    unittest.main() 
