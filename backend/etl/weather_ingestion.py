"""
AgroPulse AI - Weather Data ETL Pipeline
Source: OpenWeatherMap API
Target: S3 (raw JSON) + RDS PostgreSQL (normalized)

Architecture:
  EventBridge (daily trigger) → Lambda → this ETL script
  → Raw JSON to S3 Data Lake
  → Normalized records to PostgreSQL
"""
import json
import os
from datetime import datetime, timezone
from typing import List

import boto3
import httpx
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# Configuration
OWM_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OWM_BASE_URL = "https://api.openweathermap.org/data/2.5"
S3_BUCKET = os.getenv("S3_BUCKET_DATA", "agropulse-data-lake")
DB_URL = os.getenv("DATABASE_URL", "")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

# Major agricultural districts in India
DISTRICTS = [
    {"name": "Pune", "state": "Maharashtra", "lat": 18.5204, "lon": 73.8567},
    {"name": "Ludhiana", "state": "Punjab", "lat": 30.9010, "lon": 75.8573},
    {"name": "Nashik", "state": "Maharashtra", "lat": 19.9975, "lon": 73.7898},
    {"name": "Anand", "state": "Gujarat", "lat": 22.5645, "lon": 72.9289},
    {"name": "Warangal", "state": "Telangana", "lat": 18.0000, "lon": 79.5800},
    {"name": "Coimbatore", "state": "Tamil Nadu", "lat": 11.0168, "lon": 76.9558},
    {"name": "Mysuru", "state": "Karnataka", "lat": 12.2958, "lon": 76.6394},
    {"name": "Patna", "state": "Bihar", "lat": 25.5941, "lon": 85.1376},
    {"name": "Jabalpur", "state": "Madhya Pradesh", "lat": 23.1815, "lon": 79.9864},
    {"name": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lon": 75.7873},
]


def fetch_weather(district: dict) -> dict | None:
    """Fetch weather data from OpenWeatherMap for a district"""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"{OWM_BASE_URL}/weather",
                params={
                    "lat": district["lat"],
                    "lon": district["lon"],
                    "appid": OWM_API_KEY,
                    "units": "metric",
                },
            )
            if response.status_code == 200:
                data = response.json()
                data["_meta"] = {
                    "district": district["name"],
                    "state": district["state"],
                    "ingested_at": datetime.now(timezone.utc).isoformat(),
                }
                return data
    except Exception as e:
        print(f"Failed to fetch weather for {district['name']}: {e}")
    return None


def store_raw_in_s3(data: dict, district: str, s3_client) -> str:
    """Store raw JSON in S3 Data Lake"""
    ts = datetime.now(timezone.utc)
    key = f"weather/raw/{ts.strftime('%Y/%m/%d/%H')}/{district.lower().replace(' ', '_')}_{int(ts.timestamp())}.json"

    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=json.dumps(data),
        ContentType="application/json",
        Metadata={
            "district": district,
            "ingested_at": ts.isoformat(),
        },
    )
    return key


def normalize_weather(raw: dict) -> dict:
    """Normalize OpenWeatherMap raw response to flat schema"""
    return {
        "district": raw["_meta"]["district"],
        "state": raw["_meta"]["state"],
        "latitude": raw["coord"]["lat"],
        "longitude": raw["coord"]["lon"],
        "temperature_celsius": raw["main"]["temp"],
        "feels_like_celsius": raw["main"]["feels_like"],
        "humidity_percent": raw["main"]["humidity"],
        "pressure_hpa": raw["main"]["pressure"],
        "wind_speed_kmh": raw.get("wind", {}).get("speed", 0) * 3.6,
        "wind_direction_deg": raw.get("wind", {}).get("deg", 0),
        "rainfall_mm": raw.get("rain", {}).get("1h", 0),
        "cloud_cover_pct": raw.get("clouds", {}).get("all", 0),
        "visibility_km": raw.get("visibility", 10000) / 1000,
        "weather_condition": raw["weather"][0]["description"],
        "weather_icon": raw["weather"][0]["icon"],
        "recorded_at": datetime.fromtimestamp(raw["dt"]).isoformat(),
    }


def save_to_postgres(records: List[dict], db_url: str):
    """Bulk insert normalized weather records to PostgreSQL"""
    if not db_url:
        print("DATABASE_URL not set — skipping PostgreSQL insert")
        return

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    insert_sql = """
        INSERT INTO weather_records (
            district, state, latitude, longitude,
            temperature_celsius, humidity_percent, rainfall_mm,
            wind_speed_kmh, weather_condition, recorded_at
        ) VALUES %s
        ON CONFLICT DO NOTHING
    """

    values = [
        (
            r["district"], r["state"], r["latitude"], r["longitude"],
            r["temperature_celsius"], r["humidity_percent"], r["rainfall_mm"],
            r["wind_speed_kmh"], r["weather_condition"], r["recorded_at"],
        )
        for r in records
    ]

    execute_values(cur, insert_sql, values)
    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted {len(values)} weather records to PostgreSQL")


def run_pipeline():
    """Main ETL pipeline execution"""
    print(f"[{datetime.now()}] Starting Weather ETL Pipeline")

    s3 = boto3.client("s3", region_name=AWS_REGION)
    raw_records = []
    normalized = []

    for district in DISTRICTS:
        raw = fetch_weather(district)
        if raw:
            # Store raw in S3
            try:
                key = store_raw_in_s3(raw, district["name"], s3)
                print(f"Stored raw: s3://{S3_BUCKET}/{key}")
            except Exception as e:
                print(f"S3 store failed for {district['name']}: {e}")

            # Normalize
            norm = normalize_weather(raw)
            normalized.append(norm)
            print(f"Fetched weather for {district['name']}, {district['state']}: {norm['temperature_celsius']}°C")

    # Save normalized to CSV (for S3 processed zone)
    if normalized:
        df = pd.DataFrame(normalized)
        csv_key = f"weather/processed/{datetime.now().strftime('%Y/%m/%d')}/weather_batch.csv"
        try:
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=csv_key,
                Body=df.to_csv(index=False),
                ContentType="text/csv",
            )
            print(f"Saved processed CSV: s3://{S3_BUCKET}/{csv_key}")
        except Exception as e:
            print(f"Processed CSV upload failed: {e}")

        # Save to PostgreSQL
        save_to_postgres(normalized, DB_URL)

    print(f"[{datetime.now()}] Weather ETL Complete. Processed {len(normalized)} districts.")
    return {"processed": len(normalized), "failed": len(DISTRICTS) - len(normalized)}


def lambda_handler(event, context):
    """AWS Lambda entry point (triggered by EventBridge daily schedule)"""
    result = run_pipeline()
    return {"statusCode": 200, "body": json.dumps(result)}


if __name__ == "__main__":
    run_pipeline()
