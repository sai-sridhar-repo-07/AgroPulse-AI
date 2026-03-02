"""
AgroPulse AI - Authentication Schemas
"""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100, description="Cognito username or email")
    password: str = Field(..., min_length=8, description="User password")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "farmer@example.com",
                "password": "SecurePass123!"
            }
        }


class TokenResponse(BaseModel):
    access_token: str
    id_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class UserProfile(BaseModel):
    sub: str
    email: str
    name: str
    phone_number: str | None = None
    preferred_language: str = "en"
