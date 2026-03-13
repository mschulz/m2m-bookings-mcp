"""Tests for app/daos/base.py — safe_commit, _resolve_location, and BaseDAO methods."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy import exc as sa_exc

from app.daos.base import BaseDAO, _resolve_location, safe_commit
from app.models.booking import Booking


# ---------------------------------------------------------------------------
# safe_commit
# ---------------------------------------------------------------------------


class TestSafeCommit:
    async def test_success_returns_true(self):
        db = AsyncMock()
        result = await safe_commit(db, "error detail")
        assert result is True
        db.commit.assert_called_once()

    async def test_data_error_rolls_back_and_raises_422(self):
        db = AsyncMock()
        db.commit.side_effect = sa_exc.DataError(
            "stmt", {}, Exception("data type mismatch")
        )
        with pytest.raises(HTTPException) as exc_info:
            await safe_commit(db, "bad data")
        assert exc_info.value.status_code == 422
        db.rollback.assert_called_once()

    async def test_integrity_error_with_message_logs_and_returns_false(self):
        db = AsyncMock()
        db.commit.side_effect = sa_exc.IntegrityError(
            "stmt", {}, Exception("unique violation")
        )
        result = await safe_commit(db, "error detail", integrity_msg="already exists")
        assert result is False
        db.rollback.assert_called_once()

    async def test_integrity_error_without_message_re_raises(self):
        db = AsyncMock()
        db.commit.side_effect = sa_exc.IntegrityError(
            "stmt", {}, Exception("unique violation")
        )
        with pytest.raises(sa_exc.IntegrityError):
            await safe_commit(db, "error detail")  # no integrity_msg
        db.rollback.assert_called_once()

    async def test_operational_error_rolls_back_and_returns_false(self):
        db = AsyncMock()
        db.commit.side_effect = sa_exc.OperationalError(
            "stmt", {}, Exception("connection closed")
        )
        result = await safe_commit(db, "error detail")
        assert result is False
        db.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# _resolve_location
# ---------------------------------------------------------------------------


class TestResolveLocation:
    async def test_fetches_location_when_postcode_set_and_no_location_in_data(self):
        instance = MagicMock()
        instance.postcode = "3000"
        instance.location = None
        data = {"id": "123"}

        with patch(
            "app.daos.base.get_location",
            new_callable=AsyncMock,
            return_value="Melbourne",
        ):
            await _resolve_location(instance, data)

        assert instance.location == "Melbourne"

    async def test_skips_lookup_when_location_already_in_data(self):
        instance = MagicMock()
        instance.postcode = "3000"
        data = {"id": "123", "location": "Melbourne"}

        with patch(
            "app.daos.base.get_location", new_callable=AsyncMock
        ) as mock_get:
            await _resolve_location(instance, data)

        mock_get.assert_not_called()

    async def test_skips_lookup_when_no_postcode(self):
        instance = MagicMock()
        instance.postcode = None
        data = {"id": "123"}

        with patch(
            "app.daos.base.get_location", new_callable=AsyncMock
        ) as mock_get:
            await _resolve_location(instance, data)

        mock_get.assert_not_called()

    async def test_location_not_set_when_api_returns_none(self):
        instance = MagicMock()
        instance.postcode = "9999"
        instance.location = None
        data = {"id": "123"}

        with patch(
            "app.daos.base.get_location",
            new_callable=AsyncMock,
            return_value=None,
        ):
            await _resolve_location(instance, data)

        # location should remain unchanged (None)
        assert instance.location is None


# ---------------------------------------------------------------------------
# BaseDAO
# ---------------------------------------------------------------------------


class TestBaseDAOGetByBookingId:
    async def test_returns_none_when_not_found(self):
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        db = AsyncMock()
        db.execute.return_value = mock_result

        dao = BaseDAO(Booking)
        result = await dao.get_by_booking_id(db, 99999)
        assert result is None

    async def test_returns_booking_when_found(self):
        booking = MagicMock(spec=Booking)
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = booking
        db = AsyncMock()
        db.execute.return_value = mock_result

        dao = BaseDAO(Booking)
        result = await dao.get_by_booking_id(db, 12345)
        assert result is booking


class TestBaseDAOCreateUpdateBooking:
    async def test_raises_422_when_no_booking_id(self):
        db = AsyncMock()
        dao = BaseDAO(Booking)
        with pytest.raises(HTTPException) as exc_info:
            await dao.create_update_booking(db, {})
        assert exc_info.value.status_code == 422

    async def test_creates_new_booking_when_not_found(self):
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        db = AsyncMock()
        db.execute.return_value = mock_result

        dao = BaseDAO(Booking)
        data = {
            "id": "99",
            "is_first_recurring": "false",
            "is_new_customer": "false",
            "customer": {"id": "1"},
        }

        with patch("app.daos.base.get_location", new_callable=AsyncMock, return_value=None):
            await dao.create_update_booking(db, data)

        db.add.assert_called_once()
        db.commit.assert_called_once()

    async def test_updates_existing_booking_when_found(self):
        existing = MagicMock(spec=Booking)
        existing.booking_id = 99
        existing.name = "Old Name"
        existing.teams_assigned = None
        existing.model_dump.return_value = {}

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = existing
        db = AsyncMock()
        db.execute.return_value = mock_result

        dao = BaseDAO(Booking)
        data = {
            "id": "99",
            "is_first_recurring": "false",
            "is_new_customer": "false",
            "customer": {"id": "1"},
        }

        with patch("app.daos.base.get_location", new_callable=AsyncMock, return_value=None):
            await dao.create_update_booking(db, data)

        existing.update_from_webhook.assert_called_once_with(data)
        db.commit.assert_called_once()


class TestBaseDAOCancelBooking:
    async def test_deletes_booking_when_found(self):
        booking = MagicMock(spec=Booking)
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = booking
        db = AsyncMock()
        db.execute.return_value = mock_result

        dao = BaseDAO(Booking)
        await dao.cancel_booking(db, {"id": "12345"})

        db.delete.assert_called_once_with(booking)
        db.commit.assert_called_once()

    async def test_no_op_when_booking_id_is_none(self):
        db = AsyncMock()
        dao = BaseDAO(Booking)
        await dao.cancel_booking(db, {})  # no "id" key
        db.delete.assert_not_called()
        db.commit.assert_not_called()

    async def test_skips_delete_when_booking_not_found(self):
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        db = AsyncMock()
        db.execute.return_value = mock_result

        dao = BaseDAO(Booking)
        await dao.cancel_booking(db, {"id": "99999"})

        db.delete.assert_not_called()
        db.commit.assert_called_once()  # safe_commit still called
