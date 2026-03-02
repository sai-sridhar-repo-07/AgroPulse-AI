"""
AgroPulse AI - Generative AI Explanation Schemas
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class ExplanationRequest(BaseModel):
    prediction_type: str = Field(
        ...,
        description="Type: 'crop_recommendation', 'yield_prediction', 'price_forecast', 'risk_detection'"
    )
    prediction_output: Dict[str, Any] = Field(..., description="Raw model output")
    feature_importance: Optional[Dict[str, float]] = Field(None, description="SHAP or feature importance values")
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    farmer_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Farmer details: location, crop, land area"
    )
    language: str = Field("en", description="Response language: 'en', 'hi', 'mr', 'te', 'kn'")

    class Config:
        json_schema_extra = {
            "example": {
                "prediction_type": "crop_recommendation",
                "prediction_output": {
                    "top_crop": "Rice",
                    "confidence": 0.87,
                    "alternatives": ["Wheat", "Maize"]
                },
                "feature_importance": {
                    "nitrogen": 0.35,
                    "rainfall": 0.28,
                    "temperature": 0.20,
                    "ph": 0.17
                },
                "confidence_score": 0.87,
                "farmer_context": {
                    "name": "Ramesh",
                    "district": "Pune",
                    "land_area": 2.5,
                    "current_season": "Kharif"
                },
                "language": "en"
            }
        }


class ExplanationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    explanation: str = Field(..., description="Human-readable AI explanation")
    key_insights: List[str] = Field(..., description="Bullet-point key insights")
    risk_mitigation: List[str] = Field(..., description="Actionable risk mitigation steps")
    confidence_narrative: str = Field(..., description="Explanation of confidence level")
    language: str
    tokens_used: Optional[int] = None
    model_used: str
    generated_at: str
