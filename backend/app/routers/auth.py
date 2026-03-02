"""
AgroPulse AI - Authentication Router
"""
from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.services.auth_service import auth_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=TokenResponse, summary="Farmer Login via Cognito")
@limiter.limit("10/minute")
async def login(request: Request, credentials: LoginRequest):
    """
    Authenticate farmer using Amazon Cognito.

    Returns JWT tokens (access_token, id_token, refresh_token).
    Use the **access_token** as Bearer token for all protected endpoints.
    """
    return await auth_service.login(credentials.username, credentials.password)


@router.post("/refresh", response_model=TokenResponse, summary="Refresh Access Token")
async def refresh_token(payload: RefreshRequest):
    """Exchange refresh token for new access token"""
    return await auth_service.refresh_token(payload.refresh_token)


@router.get("/me", summary="Get Current User Profile")
async def get_profile(request: Request):
    """Get authenticated user profile from Cognito"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = auth_header.split(" ")[1]
    return await auth_service.get_user_from_token(token)
