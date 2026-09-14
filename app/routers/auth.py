from fastapi import APIRouter, HTTPException, status

from app.schemas import LoginRequest, TokenResponse
from app.security import verify_credentials, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    """
    Matches authenticateWithBackend() in the firmware exactly:
    POST { "username": "...", "password": "..." } -> { "access_token": "..." }
    """
    if not verify_credentials(body.username, body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=body.username)
    return TokenResponse(access_token=token)
