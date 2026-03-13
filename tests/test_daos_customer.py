"""Tests for app/daos/customer.py — CustomerDAO upsert and race condition guard."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy import exc as sa_exc

from app.daos.customer import CustomerDAO
from app.models.customer import Customer


def _make_dao():
    return CustomerDAO(Customer)


def _make_db(existing_customer=None):
    """Return a mock AsyncSession that returns existing_customer from scalars().first()."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = existing_customer
    db = AsyncMock()
    db.execute.return_value = mock_result
    return db


def _customer_data(**overrides):
    data = {
        "id": "67890",
        "created_at": "2024-01-15T10:00:00+10:00",
        "updated_at": "2024-01-20T10:00:00+10:00",
        "first_name": "Jane",
        "last_name": "Smith",
        "name": "Jane Smith",
        "email": "jane@example.com",
        "zip": "3000",
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# get_by_customer_id
# ---------------------------------------------------------------------------


class TestGetByCustomerId:
    async def test_returns_customer_when_found(self):
        customer = MagicMock(spec=Customer)
        db = _make_db(existing_customer=customer)
        dao = _make_dao()
        result = await dao.get_by_customer_id(db, 67890)
        assert result is customer

    async def test_returns_none_when_not_found(self):
        db = _make_db(existing_customer=None)
        dao = _make_dao()
        result = await dao.get_by_customer_id(db, 99999)
        assert result is None


# ---------------------------------------------------------------------------
# create_customer
# ---------------------------------------------------------------------------


class TestCreateCustomer:
    async def test_creates_and_commits_new_customer(self):
        db = _make_db()
        dao = _make_dao()

        with patch("app.daos.customer._resolve_location", new_callable=AsyncMock):
            await dao.create_customer(db, _customer_data())

        db.add.assert_called_once()
        db.commit.assert_called_once()

    async def test_integrity_error_falls_back_to_update(self):
        """Race condition: IntegrityError on INSERT → fall back to update."""
        existing = MagicMock(spec=Customer)
        existing.updated_at = "2024-01-15T10:00:00+10:00"

        # First execute() call (in create_customer) finds nothing — but we
        # need get_by_customer_id to return the existing record.
        db = _make_db(existing_customer=existing)
        db.commit.side_effect = [
            sa_exc.IntegrityError("stmt", {}, Exception("unique")),
            None,  # second commit from update_customer
        ]

        dao = _make_dao()

        with patch("app.daos.customer._resolve_location", new_callable=AsyncMock):
            await dao.create_customer(db, _customer_data())

        db.rollback.assert_called()

    async def test_data_error_raises_422(self):
        db = _make_db()
        db.commit.side_effect = sa_exc.DataError(
            "stmt", {}, Exception("data type")
        )
        dao = _make_dao()

        with (
            patch("app.daos.customer._resolve_location", new_callable=AsyncMock),
            pytest.raises(HTTPException) as exc_info,
        ):
            await dao.create_customer(db, _customer_data())

        assert exc_info.value.status_code == 422

    async def test_operational_error_rolls_back_silently(self):
        db = _make_db()
        db.commit.side_effect = sa_exc.OperationalError(
            "stmt", {}, Exception("connection lost")
        )
        dao = _make_dao()

        with patch("app.daos.customer._resolve_location", new_callable=AsyncMock):
            # Should not raise — OperationalError is swallowed
            await dao.create_customer(db, _customer_data())

        db.rollback.assert_called()


# ---------------------------------------------------------------------------
# update_customer
# ---------------------------------------------------------------------------


class TestUpdateCustomer:
    async def test_skips_commit_when_data_unchanged(self):
        """If updated_at hasn't changed, no commit should be made."""
        customer = MagicMock(spec=Customer)
        customer.updated_at = "2024-01-15T10:00:00+10:00"

        db = _make_db()
        dao = _make_dao()

        data = _customer_data(updated_at="2024-01-15T10:00:00+10:00")

        def apply_unchanged(data):
            # Simulate update_from_webhook not changing updated_at
            pass

        customer.update_from_webhook.side_effect = apply_unchanged

        with patch("app.daos.customer._resolve_location", new_callable=AsyncMock):
            await dao.update_customer(db, customer, data)

        db.commit.assert_not_called()

    async def test_commits_when_data_changed(self):
        customer = MagicMock(spec=Customer)
        customer.updated_at = "2024-01-10T10:00:00+10:00"

        db = _make_db()
        dao = _make_dao()

        def apply_changed(data):
            customer.updated_at = "2024-01-20T10:00:00+10:00"

        customer.update_from_webhook.side_effect = apply_changed

        with patch("app.daos.customer._resolve_location", new_callable=AsyncMock):
            await dao.update_customer(db, customer, _customer_data())

        db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# create_or_update_customer
# ---------------------------------------------------------------------------


class TestCreateOrUpdateCustomer:
    async def test_creates_when_not_found(self):
        db = _make_db(existing_customer=None)
        dao = _make_dao()

        with patch.object(dao, "create_customer", new_callable=AsyncMock) as mock_create:
            await dao.create_or_update_customer(db, _customer_data())

        mock_create.assert_called_once()

    async def test_updates_when_found(self):
        existing = MagicMock(spec=Customer)
        db = _make_db(existing_customer=existing)
        dao = _make_dao()

        with patch.object(dao, "update_customer", new_callable=AsyncMock) as mock_update:
            await dao.create_or_update_customer(db, _customer_data())

        mock_update.assert_called_once_with(db, existing, _customer_data())
