"""
Shared pytest fixtures for the m2m-bookings-mcp test suite.

Sets up:
- Environment variables required before any app imports
- Mock database session
- FastAPI test client with DB and auth dependencies overridden
- Common booking and customer data payloads
"""

import os
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.testclient import TestClient

# Must be set before app modules are imported so pydantic_settings
# picks them up and the lru_cache returns the right Settings object.
os.environ["ENVIRONMENT"] = "testing"
os.environ["API_KEY"] = "test-api-key"
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("SUPPORT_EMAIL", "support@example.com")
os.environ.setdefault("FROM_ADDRESS", "noreply@example.com")
os.environ.setdefault("FROM_NAME", "Test App")
os.environ.setdefault("COMPANY_NAME", "Test Company")
os.environ.setdefault("APP_NAME", "TestApp")

# Clear the lru_cache so fresh settings are built with the env vars above.
from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Mock database session
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db_session():
    """AsyncSession mock with sensible defaults for DAO queries."""
    session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result
    return session


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------


@pytest.fixture
def client(mock_db_session):
    """
    Starlette TestClient with:
    - get_db overridden to yield the mock AsyncSession
    - verify_api_key overridden to accept the test key without a real DB check
    - app.main.engine patched so the lifespan table-creation step is a no-op
    """
    from app.main import app
    from app.core.database import get_db
    from app.core.auth import verify_api_key

    async def override_get_db():
        yield mock_db_session

    def override_verify_api_key():
        return HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="test-api-key"
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_api_key] = override_verify_api_key

    # Patch the engine used in the lifespan to avoid a real DB connection.
    mock_conn = AsyncMock()
    mock_conn.run_sync = AsyncMock()

    @asynccontextmanager
    async def _mock_begin():
        yield mock_conn

    mock_engine = MagicMock()
    mock_engine.begin = _mock_begin
    mock_engine.dispose = AsyncMock()

    with patch("app.main.engine", mock_engine):
        with TestClient(app) as c:
            yield c

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Authorization header for authenticated requests."""
    return {"Authorization": "Bearer test-api-key"}


# ---------------------------------------------------------------------------
# Sample data payloads
# ---------------------------------------------------------------------------


@pytest.fixture
def booking_data():
    """Minimal valid booking webhook payload."""
    return {
        "id": "12345",
        "created_at": "2024-01-15T10:00:00+10:00",
        "updated_at": "2024-01-15T10:00:00+10:00",
        "service_time": "09:00 AM",
        "service_date": "2024-02-15",
        "duration": "3 hours",
        "final_price": "$143.00",
        "booking_status": "NOT_COMPLETE",
        "service_category": "House Clean",
        "frequency": "Weekly",
        "is_first_recurring": "false",
        "is_new_customer": "true",
        "first_name": "Jane",
        "last_name": "Smith",
        "name": "Jane Smith",
        "email": "jane@example.com",
        "phone": "0412345678",
        "zip": "3000",
        "address": "123 Test St",
        "city": "Melbourne",
        "state": "VIC",
        "customer": {
            "id": "67890",
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "phone": "0412345678",
            "zip": "3000",
        },
    }


@pytest.fixture
def customer_data():
    """Minimal valid customer webhook payload."""
    return {
        "id": "67890",
        "created_at": "2024-01-15T10:00:00+10:00",
        "updated_at": "2024-01-15T10:00:00+10:00",
        "first_name": "Jane",
        "last_name": "Smith",
        "name": "Jane Smith",
        "email": "jane@example.com",
        "phone": "0412345678",
        "zip": "3000",
        "address": "123 Test St",
        "city": "Melbourne",
        "state": "VIC",
    }
