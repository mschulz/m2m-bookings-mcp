"""Tests for app/routers/customers.py — customer webhook endpoints."""

from unittest.mock import AsyncMock, patch

import pytest


def _patch_create_or_update(return_value="OK"):
    return patch(
        "app.routers.customers.create_or_update_customer",
        new_callable=AsyncMock,
        return_value=return_value,
    )


def _patch_klaviyo():
    return patch("app.routers.customers.process_with_klaviyo", new_callable=AsyncMock)


class TestPostCustomerNew:
    def test_returns_ok_for_valid_data(self, client, auth_headers, customer_data):
        with _patch_create_or_update(), _patch_klaviyo():
            response = client.post("/customer/new", json=customer_data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == "OK"

    def test_empty_body_missing_id_raises_422(self, client, auth_headers):
        with _patch_klaviyo():
            response = client.post("/customer/new", json={"email": "x@x.com"}, headers=auth_headers)
        assert response.status_code == 422

    def test_missing_id_raises_422(self, client, auth_headers):
        # Let the real service run; it should raise 422 for missing id
        with _patch_klaviyo():
            response = client.post("/customer/new", json={}, headers=auth_headers)
        assert response.status_code == 422


class TestPostCustomerUpdated:
    def test_returns_ok_for_valid_data(self, client, auth_headers, customer_data):
        with _patch_create_or_update(), _patch_klaviyo():
            response = client.post("/customer/updated", json=customer_data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == "OK"

    def test_missing_id_raises_422(self, client, auth_headers):
        with _patch_klaviyo():
            response = client.post("/customer/updated", json={}, headers=auth_headers)
        assert response.status_code == 422
