"""
AgroPulse AI - Prediction ORM Model
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Float, JSON, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.database import Base


class PredictionType(str, enum.Enum):
    CROP_RECOMMENDATION = "crop_recommendation"
    YIELD_PREDICTION = "yield_prediction"
    PRICE_FORECAST = "price_forecast"
    RISK_DETECTION = "risk_detection"


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    farmer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farmers.id"), nullable=True, index=True
    )
    prediction_type: Mapped[PredictionType] = mapped_column(
        Enum(PredictionType), nullable=False, index=True
    )
    input_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    output_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    model_version: Mapped[str] = mapped_column(String(50), default="v1")
    explanation: Mapped[Optional[str]] = mapped_column(String(4000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<Prediction id={self.id} type={self.prediction_type}>"
