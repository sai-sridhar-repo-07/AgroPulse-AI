"""
AgroPulse AI - Authentication Service (Amazon Cognito)
"""
import boto3
import structlog
from botocore.exceptions import ClientError
from fastapi import HTTPException, status

from app.config import settings
from app.schemas.auth import TokenResponse

logger = structlog.get_logger(__name__)


class AuthService:
    def __init__(self):
        self.client = boto3.client("cognito-idp", region_name=settings.COGNITO_REGION)

    async def login(self, username: str, password: str) -> TokenResponse:
        """Authenticate user via Amazon Cognito USER_PASSWORD_AUTH flow"""
        try:
            response = self.client.initiate_auth(
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": username,
                    "PASSWORD": password,
                },
                ClientId=settings.COGNITO_CLIENT_ID,
            )

            auth_result = response["AuthenticationResult"]
            logger.info("auth.login.success", username=username)

            return TokenResponse(
                access_token=auth_result["AccessToken"],
                id_token=auth_result["IdToken"],
                refresh_token=auth_result["RefreshToken"],
                token_type="Bearer",
                expires_in=auth_result["ExpiresIn"],
            )

        except self.client.exceptions.NotAuthorizedException:
            logger.warning("auth.login.invalid_credentials", username=username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
        except self.client.exceptions.UserNotFoundException:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        except ClientError as e:
            logger.error("auth.login.error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error",
            )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token"""
        try:
            response = self.client.initiate_auth(
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters={"REFRESH_TOKEN": refresh_token},
                ClientId=settings.COGNITO_CLIENT_ID,
            )
            auth_result = response["AuthenticationResult"]
            return TokenResponse(
                access_token=auth_result["AccessToken"],
                id_token=auth_result["IdToken"],
                refresh_token=refresh_token,
                token_type="Bearer",
                expires_in=auth_result["ExpiresIn"],
            )
        except ClientError as e:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    async def get_user_from_token(self, access_token: str) -> dict:
        """Get user details from access token"""
        try:
            response = self.client.get_user(AccessToken=access_token)
            attributes = {attr["Name"]: attr["Value"] for attr in response["UserAttributes"]}
            return {
                "sub": attributes.get("sub"),
                "email": attributes.get("email"),
                "name": attributes.get("name", ""),
                "phone_number": attributes.get("phone_number"),
            }
        except ClientError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")


auth_service = AuthService()
