"""
AgroPulse AI - JWT Authentication Middleware
Validates Cognito JWTs on protected endpoints
"""
import json
import urllib.request

import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

logger = structlog.get_logger(__name__)
security = HTTPBearer(auto_error=False)

# Cache JWKS to avoid repeated network calls
_jwks_cache = None


def _get_cognito_jwks() -> dict:
    """Fetch Cognito JWKS for token verification"""
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache

    jwks_url = (
        f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/"
        f"{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    )
    try:
        with urllib.request.urlopen(jwks_url) as resp:
            _jwks_cache = json.loads(resp.read())
            return _jwks_cache
    except Exception as e:
        logger.error("auth.jwks_fetch_failed", error=str(e))
        return {}


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Dependency: Validate JWT and return user context.
    In development (no Cognito configured), returns a mock user.
    Raises 401 if token is missing or invalid in production.
    """
    # Local dev bypass — no Cognito pool configured
    if not settings.COGNITO_USER_POOL_ID:
        return {"sub": "local-dev-user", "email": "dev@agropulse.local", "username": "devuser"}

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        from jose import jwt, jwk
        from jose.utils import base64url_decode

        jwks = _get_cognito_jwks()
        if not jwks:
            raise HTTPException(status_code=503, detail="Auth service unavailable")

        header = jwt.get_unverified_header(token)
        key = None
        for k in jwks.get("keys", []):
            if k["kid"] == header.get("kid"):
                key = jwk.construct(k)
                break

        if not key:
            raise HTTPException(status_code=401, detail="Token signing key not found")

        claims = jwt.decode(
            token,
            key,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.COGNITO_CLIENT_ID,
        )

        return {
            "sub": claims["sub"],
            "email": claims.get("email"),
            "username": claims.get("cognito:username"),
        }

    except Exception as e:
        logger.warning("auth.token_invalid", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict | None:
    """Optional auth dependency — returns None if no token provided"""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials=credentials, request=None)
    except HTTPException:
        return None
