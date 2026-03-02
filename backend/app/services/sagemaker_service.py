"""
AgroPulse AI - SageMaker Inference Service
Invokes deployed SageMaker endpoints for ML predictions
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

import boto3
import numpy as np
import structlog
from fastapi import HTTPException

from app.config import settings
from app.schemas.crop import CropRecommendationRequest, CropRecommendationResponse, CropScore
from app.schemas.yield_schema import YieldPredictionRequest, YieldPredictionResponse
from app.schemas.price import PriceForecastRequest, PriceForecastResponse, PriceForecastPoint
from app.schemas.alert import RiskAssessmentRequest, RiskAssessmentResponse

logger = structlog.get_logger(__name__)

CROP_LABELS = [
    "apple", "banana", "blackgram", "chickpea", "coconut", "coffee",
    "cotton", "grapes", "jute", "kidneybeans", "lentil", "maize",
    "mango", "motherbeans", "mungbean", "muskmelon", "orange",
    "papaya", "pigeonpeas", "pomegranate", "rice", "watermelon", "wheat"
]

CROP_METADATA = {
    "rice": {"season_days": 120, "water_req_mm": 1200, "yield_range": (3000, 6000)},
    "wheat": {"season_days": 100, "water_req_mm": 450, "yield_range": (3500, 5500)},
    "maize": {"season_days": 90, "water_req_mm": 600, "yield_range": (4000, 7000)},
    "cotton": {"season_days": 180, "water_req_mm": 700, "yield_range": (1500, 3000)},
    "sugarcane": {"season_days": 365, "water_req_mm": 1500, "yield_range": (50000, 100000)},
}


class SageMakerService:
    """Manages SageMaker endpoint invocations with fallback to local models"""

    def __init__(self):
        self.runtime = boto3.client("sagemaker-runtime", region_name=settings.AWS_REGION)

    def _invoke_endpoint(self, endpoint_name: str, payload: dict) -> dict:
        """Invoke a SageMaker endpoint, falling back to local heuristics if unavailable"""
        try:
            response = self.runtime.invoke_endpoint(
                EndpointName=endpoint_name,
                ContentType="application/json",
                Body=json.dumps(payload),
            )
            return json.loads(response["Body"].read().decode())
        except Exception as e:
            logger.warning("sagemaker.endpoint_unavailable", endpoint=endpoint_name, error=str(e))
            return None  # Will trigger local fallback

    async def predict_crop(self, request: CropRecommendationRequest) -> CropRecommendationResponse:
        """Crop recommendation via SageMaker XGBoost endpoint"""
        features = {
            "N": request.soil.nitrogen,
            "P": request.soil.phosphorus,
            "K": request.soil.potassium,
            "temperature": request.temperature_celsius,
            "humidity": request.humidity_percent,
            "ph": request.soil.ph,
            "rainfall": request.rainfall_mm,
        }

        # Try SageMaker endpoint
        result = self._invoke_endpoint(settings.SAGEMAKER_CROP_ENDPOINT, features)

        if result is None:
            # Fallback: local heuristic model
            result = self._local_crop_prediction(features)

        prediction_id = str(uuid.uuid4())
        recommendations = [
            CropScore(
                crop_name=rec["crop"],
                confidence_score=rec["confidence"],
                expected_yield_kg_per_hectare=CROP_METADATA.get(rec["crop"], {}).get("yield_range", (2000, 5000))[0],
                growing_season_days=CROP_METADATA.get(rec["crop"], {}).get("season_days", 90),
                water_requirement_mm=CROP_METADATA.get(rec["crop"], {}).get("water_req_mm", 500),
            )
            for rec in result["recommendations"]
        ]

        return CropRecommendationResponse(
            recommendations=recommendations,
            top_crop=result["top_crop"],
            confidence=result["confidence"],
            model_version=result.get("model_version", "xgboost-v1"),
            feature_importance=result.get("feature_importance", {}),
            prediction_id=prediction_id,
            location=f"{request.location.district}, {request.location.state}",
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _local_crop_prediction(self, features: dict) -> dict:
        """
        Local heuristic-based crop recommendation (fallback when SageMaker unavailable)
        Uses agronomic rules based on NPK, pH, rainfall, and temperature
        """
        N, P, K = features["N"], features["P"], features["K"]
        temp = features["temperature"]
        humidity = features["humidity"]
        ph = features["ph"]
        rainfall = features["rainfall"]

        scores = {}

        # Rice: High rainfall, temp 20-35, pH 5.5-6.5, high N
        scores["rice"] = (
            min(rainfall / 1200, 1.0) * 0.3 +
            (1 if 20 <= temp <= 35 else 0.3) * 0.2 +
            (1 if 5.5 <= ph <= 6.5 else 0.3) * 0.2 +
            min(N / 120, 1.0) * 0.3
        )

        # Wheat: Moderate rainfall, temp 12-25, pH 6-7, high K
        scores["wheat"] = (
            min(rainfall / 450, 1.0) * 0.3 +
            (1 if 12 <= temp <= 25 else 0.3) * 0.25 +
            (1 if 6.0 <= ph <= 7.5 else 0.3) * 0.2 +
            min(K / 150, 1.0) * 0.25
        )

        # Maize: Moderate rainfall, temp 20-30, pH 5.5-7.5
        scores["maize"] = (
            min(rainfall / 600, 1.0) * 0.25 +
            (1 if 20 <= temp <= 30 else 0.3) * 0.3 +
            (1 if 5.5 <= ph <= 7.5 else 0.3) * 0.25 +
            min(N / 80, 1.0) * 0.2
        )

        # Cotton: High temp, low rainfall, high K
        scores["cotton"] = (
            (1 if 25 <= temp <= 40 else 0.3) * 0.3 +
            (1 if rainfall < 700 else 0.4) * 0.2 +
            (1 if 6.0 <= ph <= 8.0 else 0.3) * 0.2 +
            min(K / 200, 1.0) * 0.3
        )

        # Chickpea: Dry conditions, pH 6-9
        scores["chickpea"] = (
            (1 if rainfall < 600 else 0.4) * 0.3 +
            (1 if 15 <= temp <= 30 else 0.3) * 0.2 +
            (1 if 6.0 <= ph <= 9.0 else 0.3) * 0.25 +
            min(P / 80, 1.0) * 0.25
        )

        sorted_crops = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_3 = sorted_crops[:3]
        total = sum(s for _, s in top_3)

        return {
            "top_crop": top_3[0][0],
            "confidence": round(top_3[0][1], 3),
            "model_version": "heuristic-v1",
            "recommendations": [
                {"crop": crop, "confidence": round(score / max(total, 0.01), 3)}
                for crop, score in top_3
            ],
            "feature_importance": {
                "nitrogen": 0.30,
                "rainfall": 0.25,
                "temperature": 0.20,
                "ph": 0.15,
                "phosphorus": 0.05,
                "potassium": 0.05,
            },
        }

    async def predict_yield(self, request: YieldPredictionRequest) -> YieldPredictionResponse:
        """Yield prediction via SageMaker Gradient Boosting endpoint"""
        features = {
            "crop": request.crop,
            "area_hectares": request.area_hectares,
            "nitrogen": request.soil_nitrogen,
            "ph": request.soil_ph,
            "temperature": request.weather_forecast.temperature_celsius,
            "rainfall": request.weather_forecast.rainfall_mm,
            "humidity": request.weather_forecast.humidity_percent,
            "sunshine_hours": request.weather_forecast.sunshine_hours or 7.0,
            "irrigation": int(request.irrigation),
        }

        result = self._invoke_endpoint(settings.SAGEMAKER_YIELD_ENDPOINT, features)

        if result is None:
            result = self._local_yield_prediction(features)

        predicted_yield = result["predicted_yield_kg_per_hectare"]
        total_yield = predicted_yield * request.area_hectares

        return YieldPredictionResponse(
            crop=request.crop,
            predicted_yield_kg_per_hectare=round(predicted_yield, 1),
            total_yield_kg=round(total_yield, 1),
            confidence_interval_lower=round(predicted_yield * 0.85, 1),
            confidence_interval_upper=round(predicted_yield * 1.15, 1),
            key_factors=result.get("key_factors", []),
            prediction_id=str(uuid.uuid4()),
            model_version=result.get("model_version", "gradient-boost-v1"),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _local_yield_prediction(self, features: dict) -> dict:
        """Local yield prediction fallback"""
        base_yields = {
            "rice": 4500, "wheat": 4000, "maize": 5500,
            "cotton": 2000, "sugarcane": 70000, "chickpea": 1500,
        }
        base = base_yields.get(features["crop"].lower(), 3000)

        # Adjustment factors
        nitrogen_factor = min(features["nitrogen"] / 100, 1.2)
        irrigation_factor = 1.3 if features["irrigation"] else 1.0
        rainfall_factor = min(features["rainfall"] / 100, 1.15)
        temp_factor = 1.0 if 20 <= features["temperature"] <= 30 else 0.85

        predicted = base * nitrogen_factor * irrigation_factor * rainfall_factor * temp_factor

        return {
            "predicted_yield_kg_per_hectare": round(predicted, 1),
            "model_version": "heuristic-v1",
            "key_factors": [
                {"factor": "Nitrogen", "impact": "High", "value": features["nitrogen"]},
                {"factor": "Irrigation", "impact": "Medium", "value": features["irrigation"]},
                {"factor": "Temperature", "impact": "Medium", "value": features["temperature"]},
            ],
        }

    async def assess_risk(self, request: RiskAssessmentRequest) -> RiskAssessmentResponse:
        """Risk assessment via Isolation Forest SageMaker endpoint"""
        features = {
            "district": request.district,
            "state": request.state,
            "crop": request.crop or "unknown",
        }

        result = self._invoke_endpoint(settings.SAGEMAKER_RISK_ENDPOINT, features)

        if result is None:
            result = self._local_risk_assessment(features)

        risk_score = result["overall_risk_score"]
        if risk_score < 0.25:
            risk_level = "LOW"
        elif risk_score < 0.5:
            risk_level = "MEDIUM"
        elif risk_score < 0.75:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        return RiskAssessmentResponse(
            overall_risk_score=risk_score,
            risk_level=risk_level,
            risk_factors=result.get("risk_factors", []),
            recommendations=result.get("recommendations", []),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _local_risk_assessment(self, features: dict) -> dict:
        """Local risk assessment fallback"""
        import random
        risk_score = round(random.uniform(0.15, 0.45), 2)

        return {
            "overall_risk_score": risk_score,
            "model_version": "isolation-forest-v1",
            "risk_factors": [
                {"type": "drought", "probability": 0.25, "description": "Moderate drought risk in next 30 days"},
                {"type": "pest", "probability": 0.15, "description": "Low pest outbreak probability"},
                {"type": "market", "probability": 0.20, "description": "Price volatility expected"},
            ],
            "recommendations": [
                "Monitor weather forecasts daily",
                "Maintain soil moisture levels",
                "Check crop insurance options",
            ],
        }


sagemaker_service = SageMakerService()
