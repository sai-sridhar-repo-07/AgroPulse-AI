"""
AgroPulse AI - FastAPI Application Entry Point
Production-ready API with full middleware stack
"""
import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.database import init_db, close_db
from app.routers import auth, crop, yield_pred, price, alerts, explanation, health
from app.middleware.logging import setup_logging

# ─── Logging ──────────────────────────────────────────────────────────────────
setup_logging()
logger = structlog.get_logger(__name__)

# ─── Rate Limiter ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("agropulse.startup", environment=settings.ENVIRONMENT)
    await init_db()
    yield
    await close_db()
    logger.info("agropulse.shutdown")


# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="AgroPulse AI API",
    description="""
    ## Hyper-local AI Decision Intelligence Platform for Rural Farmers

    AgroPulse AI provides:
    - **Crop Recommendations** powered by ML models
    - **Yield Predictions** using weather + soil data
    - **Price Forecasting** from mandi market data
    - **Risk Alerts** via anomaly detection
    - **AI Explanations** using Amazon Bedrock (Generative AI)
    """,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ─── Middleware Stack ──────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Request tracing + timing middleware"""
    request_id = str(uuid.uuid4())
    start_time = time.time()

    request.state.request_id = request_id

    logger.info(
        "request.started",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else "unknown",
    )

    response = await call_next(request)

    duration_ms = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

    logger.info(
        "request.completed",
        request_id=request_id,
        status_code=response.status_code,
        duration_ms=round(duration_ms, 2),
    )

    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please try again.",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(crop.router, prefix="/predict", tags=["Predictions"])
app.include_router(yield_pred.router, prefix="/predict", tags=["Predictions"])
app.include_router(price.router, prefix="/predict", tags=["Predictions"])
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
app.include_router(explanation.router, prefix="", tags=["GenAI Explanation"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "AgroPulse AI",
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
    }
