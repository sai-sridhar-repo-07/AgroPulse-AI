"""
AgroPulse AI - Crop Recommendation Schemas
"""
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SoilData(BaseModel):
    nitrogen: float = Field(..., ge=0, le=200, description="Soil Nitrogen content (kg/ha)")
    phosphorus: float = Field(..., ge=0, le=200, description="Soil Phosphorus content (kg/ha)")
    potassium: float = Field(..., ge=0, le=300, description="Soil Potassium content (kg/ha)")
    ph: float = Field(..., ge=3.0, le=10.0, description="Soil pH level")


class LocationData(BaseModel):
    state: str = Field(..., description="Indian state name")
    district: str = Field(..., description="District name")
    latitude: Optional[float] = Field(None, ge=8.0, le=37.0)
    longitude: Optional[float] = Field(None, ge=68.0, le=97.0)


class CropRecommendationRequest(BaseModel):
    soil: SoilData
    location: LocationData
    rainfall_mm: float = Field(..., ge=0, le=3000, description="Annual rainfall in mm")
    temperature_celsius: float = Field(..., ge=5.0, le=50.0, description="Average temperature")
    humidity_percent: float = Field(..., ge=0, le=100, description="Humidity percentage")
    farmer_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "soil": {"nitrogen": 90, "phosphorus": 42, "potassium": 43, "ph": 6.5},
                "location": {"state": "Maharashtra", "district": "Pune", "latitude": 18.5, "longitude": 73.8},
                "rainfall_mm": 800,
                "temperature_celsius": 25,
                "humidity_percent": 65,
            }
        }


class CropScore(BaseModel):
    crop_name: str
    confidence_score: float = Field(..., ge=0, le=1)
    expected_yield_kg_per_hectare: Optional[float] = None
    growing_season_days: Optional[int] = None
    water_requirement_mm: Optional[float] = None


class CropRecommendationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    recommendations: List[CropScore]
    top_crop: str
    confidence: float
    model_version: str
    feature_importance: dict
    prediction_id: str
    location: str
    generated_at: str
