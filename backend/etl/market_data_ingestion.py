"""
AgroPulse AI - Market Data ETL Pipeline
Source: AGMARKNET dataset (data.gov.in) + synthetic data
Target: S3 (raw CSV) + RDS PostgreSQL (normalized)

Pipeline:
  EventBridge (daily trigger) → Lambda → Fetch AGMARKNET → S3 → RDS
"""
import io
import json
import os
from datetime import date, datetime, timedelta, timezone
from typing import List

import boto3
import httpx
import numpy as np
import pandas as pd

S3_BUCKET = os.getenv("S3_BUCKET_DATA", "agropulse-data-lake")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
DB_URL = os.getenv("DATABASE_URL", "")

COMMODITIES = [
    "Wheat", "Rice", "Maize", "Cotton", "Soybean",
    "Onion", "Tomato", "Potato", "Chickpea", "Groundnut",
    "Sugarcane", "Lentil", "Mustard",
]

BASE_PRICES_INR = {
    "Wheat": 2150, "Rice": 2183, "Maize": 1870, "Cotton": 6620,
    "Soybean": 3950, "Onion": 2200, "Tomato": 1800, "Potato": 1400,
    "Chickpea": 5400, "Groundnut": 5550, "Sugarcane": 350,
    "Lentil": 6000, "Mustard": 5200,
}

STATES_MANDIS = {
    "Maharashtra": ["Pune", "Nashik", "Aurangabad", "Nagpur"],
    "Punjab": ["Ludhiana", "Amritsar", "Patiala"],
    "Uttar Pradesh": ["Agra", "Kanpur", "Varanasi", "Lucknow"],
    "Karnataka": ["Mysuru", "Hubli", "Bengaluru"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Kota"],
    "Gujarat": ["Ahmedabad", "Surat", "Rajkot"],
    "Telangana": ["Warangal", "Nizamabad", "Karimnagar"],
    "Tamil Nadu": ["Coimbatore", "Salem", "Madurai"],
}


def fetch_agmarknet_data(commodity: str, state: str, report_date: date) -> List[dict]:
    """
    Fetch from AGMARKNET API.
    In production: GET https://agmarknet.gov.in/api/price_data
    Here: generate realistic synthetic data
    """
    records = []
    base = BASE_PRICES_INR.get(commodity, 2000)
    mandis = STATES_MANDIS.get(state, ["Central Market"])

    for mandi in mandis:
        daily_var = np.random.normal(1.0, 0.03)
        modal_price = round(base * daily_var, 2)
        min_price = round(modal_price * np.random.uniform(0.90, 0.97), 2)
        max_price = round(modal_price * np.random.uniform(1.03, 1.10), 2)

        records.append({
            "commodity": commodity,
            "state": state,
            "district": mandi,
            "market": f"{mandi} APMC",
            "variety": "Common",
            "min_price": min_price,
            "max_price": max_price,
            "modal_price": modal_price,
            "unit": "Quintal",
            "price_date": str(report_date),
            "currency": "INR",
            "source": "AGMARKNET",
        })

    return records


def process_market_data(all_records: List[dict]) -> pd.DataFrame:
    """Clean and transform market data"""
    df = pd.DataFrame(all_records)

    # Data quality checks
    df = df[df["modal_price"] > 0]
    df = df[df["min_price"] <= df["modal_price"]]
    df = df[df["modal_price"] <= df["max_price"]]
    df = df.drop_duplicates(subset=["commodity", "state", "district", "price_date"])
    df = df.dropna(subset=["modal_price", "commodity", "state"])

    # Standardize commodity names
    df["commodity"] = df["commodity"].str.strip().str.title()
    df["state"] = df["state"].str.strip()

    # Add derived columns
    df["price_spread"] = df["max_price"] - df["min_price"]
    df["price_spread_pct"] = df["price_spread"] / df["modal_price"] * 100

    print(f"Processed {len(df)} market price records")
    print(f"Commodities: {df['commodity'].nunique()} | States: {df['state'].nunique()}")
    return df


def save_to_s3(df: pd.DataFrame, s3_client, report_date: date):
    """Save processed market data to S3"""
    # Raw CSV
    raw_key = f"market/raw/{report_date.strftime('%Y/%m/%d')}/agmarknet_prices.csv"
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=raw_key,
        Body=df.to_csv(index=False),
        ContentType="text/csv",
    )

    # Partitioned Parquet (for Athena queries)
    processed_key = f"market/processed/year={report_date.year}/month={report_date.month:02d}/day={report_date.day:02d}/prices.csv"
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=processed_key,
        Body=df.to_csv(index=False),
        ContentType="text/csv",
    )

    print(f"Saved to S3: {raw_key}")
    return raw_key


def save_to_postgres(df: pd.DataFrame):
    """Insert market data to PostgreSQL"""
    if not DB_URL:
        print("DATABASE_URL not set — skipping PostgreSQL")
        return

    try:
        import psycopg2
        from psycopg2.extras import execute_values

        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        values = [
            (
                row["commodity"], row["state"], row["district"], row["market"],
                row["variety"], row["min_price"], row["max_price"], row["modal_price"],
                row["unit"], row["price_date"],
            )
            for _, row in df.iterrows()
        ]

        execute_values(
            cur,
            """
            INSERT INTO market_prices
                (commodity, state, district, market, variety,
                 min_price, max_price, modal_price, unit, price_date)
            VALUES %s
            ON CONFLICT DO NOTHING
            """,
            values,
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"Inserted {len(values)} records to PostgreSQL")
    except Exception as e:
        print(f"PostgreSQL insert failed: {e}")


def run_pipeline(report_date: date = None):
    """Main ETL pipeline"""
    if report_date is None:
        report_date = date.today()

    print(f"[{datetime.now()}] Starting Market Data ETL for {report_date}")

    s3 = boto3.client("s3", region_name=AWS_REGION)
    all_records = []

    for state, mandis in STATES_MANDIS.items():
        for commodity in COMMODITIES[:5]:  # Top 5 commodities
            records = fetch_agmarknet_data(commodity, state, report_date)
            all_records.extend(records)
            print(f"Fetched {len(records)} records: {commodity}, {state}")

    if all_records:
        df = process_market_data(all_records)

        try:
            save_to_s3(df, s3, report_date)
        except Exception as e:
            print(f"S3 save failed: {e}")

        save_to_postgres(df)

    print(f"Market ETL Complete: {len(all_records)} total records")
    return {"processed": len(all_records), "date": str(report_date)}


def lambda_handler(event, context):
    """Lambda entry point"""
    result = run_pipeline()
    return {"statusCode": 200, "body": json.dumps(result)}


if __name__ == "__main__":
    run_pipeline()
