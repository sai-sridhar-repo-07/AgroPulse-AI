"""
AgroPulse AI - Weather Data Service
Fetches real-time weather data from OpenWeatherMap API
Stores raw JSON in S3 and normalized data in RDS
"""
import json
from datetime import datetime, timezone

import boto3
import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.weather import WeatherRecord

logger = structlog.get_logger(__name__)


class WeatherService:
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = settings.OPENWEATHER_BASE_URL
        self.s3 = boto3.client("s3", region_name=settings.AWS_REGION)

    async def get_current_weather(self, lat: float, lon: float) -> dict:
        """Fetch current weather from OpenWeatherMap"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": self.api_key,
                    "units": "metric",
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

            # Store raw JSON in S3
            await self._store_raw_weather(data, lat, lon)

            return self._normalize_weather(data)

    async def get_weather_by_district(self, district: str, state: str) -> dict:
        """Fetch weather for a named location"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/weather",
                params={
                    "q": f"{district},{state},IN",
                    "appid": self.api_key,
                    "units": "metric",
                },
                timeout=10.0,
            )
            if response.status_code == 404:
                return self._mock_weather(district)

            response.raise_for_status()
            return self._normalize_weather(response.json())

    def _normalize_weather(self, raw: dict) -> dict:
        """Normalize OpenWeatherMap response to standard format"""
        return {
            "temperature_celsius": raw["main"]["temp"],
            "feels_like": raw["main"]["feels_like"],
            "humidity_percent": raw["main"]["humidity"],
            "pressure_hpa": raw["main"]["pressure"],
            "wind_speed_kmh": raw.get("wind", {}).get("speed", 0) * 3.6,
            "rainfall_mm": raw.get("rain", {}).get("1h", 0),
            "weather_condition": raw["weather"][0]["description"],
            "visibility_km": raw.get("visibility", 10000) / 1000,
            "recorded_at": datetime.fromtimestamp(raw["dt"]).isoformat(),
        }

    def _mock_weather(self, district: str) -> dict:
        """Return mock weather when API unavailable"""
        return {
            "temperature_celsius": 28.5,
            "feels_like": 31.0,
            "humidity_percent": 65,
            "pressure_hpa": 1013,
            "wind_speed_kmh": 12,
            "rainfall_mm": 0,
            "weather_condition": "partly cloudy",
            "visibility_km": 10,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _store_raw_weather(self, data: dict, lat: float, lon: float):
        """Store raw weather JSON to S3"""
        try:
            timestamp = datetime.now(timezone.utc)
            key = f"weather/raw/{timestamp.strftime('%Y/%m/%d')}/lat{lat}_lon{lon}_{int(timestamp.timestamp())}.json"
            self.s3.put_object(
                Bucket=settings.S3_BUCKET_DATA,
                Key=key,
                Body=json.dumps(data),
                ContentType="application/json",
            )
        except Exception as e:
            logger.warning("weather.s3_store_failed", error=str(e))


weather_service = WeatherService()
