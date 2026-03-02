"""
AgroPulse AI - Application Configuration
Centralized settings management using Pydantic Settings
"""
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ─── App ──────────────────────────────────────────────────────────────
    APP_NAME: str = "AgroPulse AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://agropulse.ai"]

    # ─── AWS Region ───────────────────────────────────────────────────────
    AWS_REGION: str = "ap-south-1"
    AWS_ACCOUNT_ID: str = ""

    # ─── Amazon Cognito ───────────────────────────────────────────────────
    COGNITO_USER_POOL_ID: str = ""
    COGNITO_CLIENT_ID: str = ""
    COGNITO_REGION: str = "ap-south-1"
    JWT_ALGORITHM: str = "RS256"

    # ─── RDS PostgreSQL ───────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://agropulse:password@localhost:5432/agropulse"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ─── DynamoDB ─────────────────────────────────────────────────────────
    DYNAMODB_TABLE_SESSIONS: str = "agropulse-farmer-sessions"
    DYNAMODB_TABLE_PREDICTIONS: str = "agropulse-predictions-cache"

    # ─── S3 ───────────────────────────────────────────────────────────────
    S3_BUCKET_DATA: str = "agropulse-data-lake"
    S3_BUCKET_MODELS: str = "agropulse-model-artifacts"
    S3_BUCKET_REPORTS: str = "agropulse-reports"

    # ─── SageMaker Endpoints ──────────────────────────────────────────────
    SAGEMAKER_CROP_ENDPOINT: str = "agropulse-crop-recommendation-v1"
    SAGEMAKER_YIELD_ENDPOINT: str = "agropulse-yield-prediction-v1"
    SAGEMAKER_PRICE_ENDPOINT: str = "agropulse-price-forecast-v1"
    SAGEMAKER_RISK_ENDPOINT: str = "agropulse-risk-detection-v1"

    # ─── Amazon Bedrock ───────────────────────────────────────────────────
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    BEDROCK_MAX_TOKENS: int = 1024
    BEDROCK_TEMPERATURE: float = 0.3

    # ─── OpenWeatherMap ───────────────────────────────────────────────────
    OPENWEATHER_API_KEY: str = ""
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"

    # ─── Rate Limiting ────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 500

    # ─── CloudWatch ───────────────────────────────────────────────────────
    CLOUDWATCH_LOG_GROUP: str = "/agropulse/backend"
    CLOUDWATCH_NAMESPACE: str = "AgroPulseAI"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
