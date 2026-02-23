# app/auth.py

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import get_settings

security = HTTPBearer()


def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> HTTPAuthorizationCredentials:
    if credentials.credentials != get_settings().API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials
