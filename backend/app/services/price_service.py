"""
AgroPulse AI - Price Forecasting Service
Uses Prophet (via SageMaker) + local historical data for mandi price forecasts
"""
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import List

import structlog

from app.config import settings
from app.schemas.price import PriceForecastRequest, PriceForecastResponse, PriceForecastPoint

logger = structlog.get_logger(__name__)

# Simulated base prices per commodity (INR/Quintal) — in production, fetched from RDS
BASE_PRICES = {
    "wheat": 2150,
    "rice": 2183,
    "maize": 1870,
    "cotton": 6620,
    "sugarcane": 350,
    "soybean": 3950,
    "groundnut": 5550,
    "tomato": 1800,
    "onion": 2200,
    "potato": 1400,
    "chickpea": 5400,
    "lentil": 6000,
}

SEASONAL_ADJUSTMENTS = {
    1: 0.02, 2: 0.04, 3: 0.06,   # Post-harvest peak
    4: 0.0, 5: -0.02, 6: -0.03,  # Mid-year dip
    7: -0.04, 8: -0.03, 9: 0.0,  # Kharif arrival
    10: 0.02, 11: 0.04, 12: 0.05, # Pre-Rabi demand
}


class PriceService:
    """Commodity price forecasting using Prophet model + market signals"""

    async def forecast_price(self, request: PriceForecastRequest) -> PriceForecastResponse:
        """Generate 7-30 day price forecast for a commodity"""
        commodity_lower = request.commodity.lower()
        base_price = BASE_PRICES.get(commodity_lower, 2500)
        month = datetime.now().month
        seasonal_adj = SEASONAL_ADJUSTMENTS.get(month, 0.0)

        current_price = base_price * (1 + seasonal_adj)
        forecast_points = self._generate_forecast(
            base_price=current_price,
            days=request.forecast_days,
            commodity=commodity_lower,
        )

        # Determine overall trend
        first_price = forecast_points[0].predicted_price
        last_price = forecast_points[-1].predicted_price
        pct_change = (last_price - first_price) / first_price

        if pct_change > 0.03:
            trend = "rising"
            signal = "SELL"  # Wait if not urgent
        elif pct_change < -0.03:
            trend = "falling"
            signal = "SELL NOW"
        else:
            trend = "stable"
            signal = "HOLD"

        return PriceForecastResponse(
            commodity=request.commodity,
            state=request.state,
            current_price=round(current_price, 2),
            unit="INR/Quintal",
            forecast=forecast_points,
            price_trend=trend,
            market_signal=signal,
            prediction_id=str(uuid.uuid4()),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _generate_forecast(
        self,
        base_price: float,
        days: int,
        commodity: str,
    ) -> List[PriceForecastPoint]:
        """
        Generate price forecast using a simplified trend model
        In production: invoke SageMaker Prophet endpoint
        """
        import math
        import random

        random.seed(hash(commodity) % 100)  # Deterministic per commodity

        points = []
        volatility = 0.015  # 1.5% daily volatility
        trend_drift = random.uniform(-0.002, 0.004)  # Slight upward or downward drift

        price = base_price
        for i in range(days):
            forecast_date = date.today() + timedelta(days=i + 1)
            daily_change = (1 + trend_drift + random.gauss(0, volatility))
            price = price * daily_change

            # Weekly pattern: slight dip on weekends (markets closed)
            if forecast_date.weekday() in [5, 6]:
                price *= 0.995

            margin = price * 0.04  # 4% confidence interval
            points.append(
                PriceForecastPoint(
                    date=forecast_date,
                    predicted_price=round(price, 2),
                    lower_bound=round(price - margin, 2),
                    upper_bound=round(price + margin, 2),
                    trend="rising" if daily_change > 1.0 else "falling",
                )
            )

        return points


price_service = PriceService()
