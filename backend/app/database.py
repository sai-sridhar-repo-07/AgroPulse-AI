"""
AgroPulse AI - Database Connections
PostgreSQL (async SQLAlchemy) + DynamoDB + S3
"""
import boto3
import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = structlog.get_logger(__name__)

# ─── PostgreSQL ───────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    """Dependency: Yield async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables (idempotent — safe to call on every startup)"""
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, checkfirst=True))
    logger.info("database.initialized")


async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("database.closed")


# ─── DynamoDB ─────────────────────────────────────────────────────────────────
def get_dynamodb():
    """Get DynamoDB resource"""
    return boto3.resource("dynamodb", region_name=settings.AWS_REGION)


def get_sessions_table():
    """Get farmer sessions DynamoDB table"""
    dynamodb = get_dynamodb()
    return dynamodb.Table(settings.DYNAMODB_TABLE_SESSIONS)


def get_predictions_table():
    """Get predictions cache DynamoDB table"""
    dynamodb = get_dynamodb()
    return dynamodb.Table(settings.DYNAMODB_TABLE_PREDICTIONS)


# ─── S3 ───────────────────────────────────────────────────────────────────────
def get_s3_client():
    """Get S3 client"""
    return boto3.client("s3", region_name=settings.AWS_REGION)


def get_s3_resource():
    """Get S3 resource"""
    return boto3.resource("s3", region_name=settings.AWS_REGION)
