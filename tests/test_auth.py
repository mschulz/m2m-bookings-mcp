"""Tests for app/core/auth.py — Bearer token validation dependency."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.auth import verify_api_key


class TestVerifyApiKey:
    def test_valid_key_returns_credentials(self):
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="test-api-key"
        )
        with patch(
            "app.core.auth.get_settings",
            return_value=MagicMock(API_KEY="test-api-key"),
        ):
            result = verify_api_key(credentials)
        assert result is credentials

    def test_invalid_key_raises_401(self):
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="wrong-key"
        )
        with (
            patch(
                "app.core.auth.get_settings",
                return_value=MagicMock(API_KEY="correct-key"),
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            verify_api_key(credentials)
        assert exc_info.value.status_code == 401

    def test_empty_key_raises_401(self):
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=""
        )
        with (
            patch(
                "app.core.auth.get_settings",
                return_value=MagicMock(API_KEY="correct-key"),
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            verify_api_key(credentials)
        assert exc_info.value.status_code == 401
