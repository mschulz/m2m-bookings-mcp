"""Tests for app/models/customer.py — Customer webhook import logic."""

import pytest

from app.models.customer import Customer


def _base_customer(**overrides):
    data = {
        "id": "67890",
        "created_at": "2024-01-15T10:00:00+10:00",
        "updated_at": "2024-01-15T10:00:00+10:00",
        "title": "Ms",
        "first_name": "Jane",
        "last_name": "Smith",
        "name": "Jane Smith",
        "email": "jane@example.com",
        "phone": "0412345678",
        "zip": "3000",
        "address": "123 Test St",
        "city": "Melbourne",
        "state": "VIC",
        "company_name": "ACME",
        "notes": "Prefers morning",
        "tags": "vip,regular",
    }
    data.update(overrides)
    return data


class TestCustomerFromWebhook:
    def test_sets_customer_id(self):
        c = Customer.from_webhook(_base_customer())
        assert c.customer_id == 67890

    def test_sets_name_fields(self):
        c = Customer.from_webhook(_base_customer())
        assert c.first_name == "Jane"
        assert c.last_name == "Smith"
        assert c.name == "Jane Smith"

    def test_sets_email(self):
        c = Customer.from_webhook(_base_customer())
        assert c.email == "jane@example.com"

    def test_sets_phone(self):
        c = Customer.from_webhook(_base_customer())
        assert c.phone == "0412345678"

    def test_sets_address_fields(self):
        c = Customer.from_webhook(_base_customer())
        assert c.address == "123 Test St"
        assert c.city == "Melbourne"
        assert c.state == "VIC"

    def test_valid_postcode_stored(self):
        c = Customer.from_webhook(_base_customer(zip="3000"))
        assert c.postcode == "3000"

    def test_non_numeric_postcode_rejected(self):
        c = Customer.from_webhook(_base_customer(zip="TBC"))
        assert c.postcode is None

    def test_location_set_when_provided(self):
        c = Customer.from_webhook(_base_customer(location="Melbourne"))
        assert c.location == "Melbourne"

    def test_location_absent_when_not_in_data(self):
        data = _base_customer()
        data.pop("location", None)
        c = Customer.from_webhook(data)
        assert c.location is None

    def test_sets_notes(self):
        c = Customer.from_webhook(_base_customer(notes="Prefers afternoon"))
        assert c.notes == "Prefers afternoon"

    def test_sets_tags(self):
        c = Customer.from_webhook(_base_customer(tags="vip"))
        assert c.tags == "vip"

    def test_tags_absent_when_not_in_data(self):
        data = _base_customer()
        data.pop("tags", None)
        c = Customer.from_webhook(data)
        assert c.tags is None

    def test_title_set(self):
        c = Customer.from_webhook(_base_customer(title="Dr"))
        assert c.title == "Dr"


class TestCustomerUpdateFromWebhook:
    def test_updates_email(self):
        c = Customer.from_webhook(_base_customer())
        c.update_from_webhook(_base_customer(email="new@example.com"))
        assert c.email == "new@example.com"

    def test_updates_phone(self):
        c = Customer.from_webhook(_base_customer())
        c.update_from_webhook(_base_customer(phone="0499999999"))
        assert c.phone == "0499999999"

    def test_updates_address(self):
        c = Customer.from_webhook(_base_customer())
        c.update_from_webhook(_base_customer(address="456 New Rd"))
        assert c.address == "456 New Rd"
