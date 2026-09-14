from datetime import datetime, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings, JWT_EXPIRE_DELTA

bearer_scheme = HTTPBearer(auto_error=False)


def verify_credentials(username: str, password: str) -> bool:
    """
    Plain comparison against env-configured credentials.

    This matches the firmware's simple username/password login flow.
    For anything beyond a prototype, swap this for per-device API keys
    and hashed credentials in the database instead of a single shared
    admin/admin123-style login baked into every device.
    """
    return username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD


def create_access_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + JWT_EXPIRE_DELTA,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def require_auth(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """Dependency that guards both device POSTs and (optionally) dashboard reads."""
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    payload = decode_access_token(creds.credentials)
    return payload.get("sub", "unknown")
