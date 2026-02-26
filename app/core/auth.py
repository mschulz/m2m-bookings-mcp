"""Bearer token authentication dependency for FastAPI routes."""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import get_settings

security = HTTPBearer()


def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> HTTPAuthorizationCredentials:
    """Validate the Bearer token against the configured API_KEY."""
    if credentials.credentials != get_settings().API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials
