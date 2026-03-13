"""Tests for app/services/customers.py — customer upsert validation."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.services.customers import create_or_update_customer


class TestCreateOrUpdateCustomer:
    async def test_raises_422_when_id_missing(self):
        db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await create_or_update_customer({}, db)
        assert exc_info.value.status_code == 422
        assert "id" in exc_info.value.detail.lower()

    async def test_delegates_to_dao_when_id_present(self):
        db = AsyncMock()
        data = {"id": "67890", "email": "jane@example.com"}

        with patch(
            "app.services.customers.customer_dao.create_or_update_customer",
            new_callable=AsyncMock,
        ) as mock_dao:
            result = await create_or_update_customer(data, db)

        mock_dao.assert_called_once_with(db, data)
        assert result == "OK"

    async def test_falsy_id_value_raises_422(self):
        """An id key present but empty/falsy should also raise 422."""
        db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await create_or_update_customer({"id": ""}, db)
        assert exc_info.value.status_code == 422
