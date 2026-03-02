"""
AgroPulse AI - Soil Data ETL Pipeline
Source: Soil Health Card (SHC) public dataset (soilhealth.dac.gov.in)
Target: S3 (raw) + RDS PostgreSQL (processed NPK features)

Pipeline: Lambda (monthly) → Download SHC CSV → Process → S3 + RDS
"""
import io
import json
import os
from datetime import datetime, timezone
from typing import List

import boto3
import numpy as np
import pandas as pd

S3_BUCKET = os.getenv("S3_BUCKET_DATA", "agropulse-data-lake")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

# Soil parameter reference ranges (Indian ICAR standards)
NPK_RANGES = {
    "nitrogen": {"low": 280, "medium": 560, "unit": "kg/ha"},
    "phosphorus": {"low": 10, "medium": 25, "unit": "kg/ha"},
    "potassium": {"low": 108, "medium": 280, "unit": "kg/ha"},
    "ph": {"acidic": 6.0, "neutral": 7.5, "alkaline": 8.5},
    "organic_carbon": {"low": 0.5, "medium": 0.75, "unit": "%"},
    "ec": {"safe": 1.0, "unit": "dS/m"},
}

STATES_NPK_PROFILES = {
    "Punjab":       {"N": (150, 280), "P": (25, 60),  "K": (150, 280), "ph": (7.0, 8.5), "OC": (0.3, 0.8)},
    "Maharashtra":  {"N": (80, 200),  "P": (15, 45),  "K": (100, 220), "ph": (6.5, 8.0), "OC": (0.4, 0.9)},
    "Karnataka":    {"N": (100, 250), "P": (10, 35),  "K": (120, 250), "ph": (5.5, 7.5), "OC": (0.5, 1.0)},
    "Uttar Pradesh":{"N": (120, 280), "P": (20, 55),  "K": (130, 260), "ph": (7.0, 8.5), "OC": (0.3, 0.7)},
    "Gujarat":      {"N": (100, 220), "P": (15, 40),  "K": (100, 200), "ph": (7.0, 8.5), "OC": (0.3, 0.6)},
    "Telangana":    {"N": (90, 210),  "P": (12, 40),  "K": (110, 230), "ph": (6.0, 8.0), "OC": (0.4, 0.8)},
    "Tamil Nadu":   {"N": (100, 240), "P": (15, 45),  "K": (120, 240), "ph": (6.0, 7.5), "OC": (0.4, 0.9)},
    "Rajasthan":    {"N": (80, 160),  "P": (10, 30),  "K": (100, 200), "ph": (7.5, 9.0), "OC": (0.2, 0.5)},
    "Bihar":        {"N": (120, 260), "P": (15, 45),  "K": (110, 230), "ph": (6.5, 8.0), "OC": (0.4, 0.8)},
    "Madhya Pradesh":{"N":(100,230),  "P": (12, 40),  "K": (110, 220), "ph": (6.5, 8.0), "OC": (0.3, 0.7)},
}


def generate_shc_dataset(n_samples: int = 10000) -> pd.DataFrame:
    """
    Generate synthetic Soil Health Card data.
    In production: download from soilhealth.dac.gov.in API
    """
    np.random.seed(42)
    records = []

    states = list(STATES_NPK_PROFILES.keys())
    districts_per_state = {
        "Punjab": ["Ludhiana", "Amritsar", "Patiala", "Bathinda"],
        "Maharashtra": ["Pune", "Nashik", "Nagpur", "Aurangabad", "Kolhapur"],
        "Karnataka": ["Mysuru", "Dharwad", "Raichur", "Haveri"],
        "Uttar Pradesh": ["Agra", "Meerut", "Varanasi", "Kanpur"],
        "Gujarat": ["Anand", "Surat", "Rajkot", "Junagadh"],
        "Telangana": ["Warangal", "Nizamabad", "Karimnagar", "Nalgonda"],
        "Tamil Nadu": ["Coimbatore", "Salem", "Trichy", "Madurai"],
        "Rajasthan": ["Jaipur", "Jodhpur", "Kota", "Bikaner"],
        "Bihar": ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur"],
        "Madhya Pradesh": ["Indore", "Jabalpur", "Bhopal", "Gwalior"],
    }

    soil_types = ["Alluvial", "Black Cotton", "Red Laterite", "Sandy Loam", "Clay Loam", "Loamy Sand"]

    for _ in range(n_samples):
        state = np.random.choice(states)
        profile = STATES_NPK_PROFILES[state]
        districts = districts_per_state.get(state, ["Central"])
        district = np.random.choice(districts)
        soil_type = np.random.choice(soil_types)

        N = round(np.random.uniform(*profile["N"]), 2)
        P = round(np.random.uniform(*profile["P"]), 2)
        K = round(np.random.uniform(*profile["K"]), 2)
        ph = round(np.random.uniform(*profile["ph"]), 2)
        OC = round(np.random.uniform(*profile["OC"]), 3)
        ec = round(np.random.uniform(0.1, 0.8), 3)

        # Classify NPK status
        n_status = "Low" if N < 280 else ("Medium" if N < 560 else "High")
        p_status = "Low" if P < 10 else ("Medium" if P < 25 else "High")
        k_status = "Low" if K < 108 else ("Medium" if K < 280 else "High")

        records.append({
            "sample_id": f"SHC-{state[:3].upper()}-{np.random.randint(100000, 999999)}",
            "state": state,
            "district": district,
            "soil_type": soil_type,
            "nitrogen_kg_ha": N,
            "phosphorus_kg_ha": P,
            "potassium_kg_ha": K,
            "ph": ph,
            "organic_carbon_pct": OC,
            "electrical_conductivity": ec,
            "n_status": n_status,
            "p_status": p_status,
            "k_status": k_status,
            "ph_status": "Acidic" if ph < 6.5 else ("Neutral" if ph <= 7.5 else "Alkaline"),
            "suitable_crops": _recommend_crops(N, P, K, ph),
        })

    df = pd.DataFrame(records)
    print(f"Generated {len(df)} soil health card records")
    print(f"States: {df['state'].nunique()} | Districts: {df['district'].nunique()}")
    return df


def _recommend_crops(N: float, P: float, K: float, ph: float) -> str:
    """Rule-based crop suitability from NPK + pH"""
    crops = []
    if N > 150 and 6.0 <= ph <= 7.5:
        crops.append("Rice")
    if K > 150 and 6.0 <= ph <= 8.0:
        crops.append("Wheat")
    if P > 25 and 5.5 <= ph <= 7.5:
        crops.append("Maize")
    if K > 180 and ph > 6.5:
        crops.append("Cotton")
    if N < 60 and P > 40 and ph > 6.0:
        crops.append("Chickpea")
    if not crops:
        crops = ["Millet", "Sorghum"]
    return ", ".join(crops[:3])


def process_soil_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and engineer features for ML model input"""
    # Remove outliers
    df = df[df["ph"].between(3.0, 10.0)]
    df = df[df["nitrogen_kg_ha"] > 0]
    df = df[df["phosphorus_kg_ha"] > 0]
    df = df[df["potassium_kg_ha"] > 0]
    df = df.dropna(subset=["nitrogen_kg_ha", "phosphorus_kg_ha", "potassium_kg_ha", "ph"])

    # District-level aggregations for ML features
    district_stats = df.groupby(["state", "district"]).agg(
        avg_N=("nitrogen_kg_ha", "mean"),
        avg_P=("phosphorus_kg_ha", "mean"),
        avg_K=("potassium_kg_ha", "mean"),
        avg_ph=("ph", "mean"),
        avg_OC=("organic_carbon_pct", "mean"),
        sample_count=("sample_id", "count"),
    ).reset_index()

    print(f"District-level aggregations: {len(district_stats)} districts")
    return df, district_stats


def save_to_s3(df: pd.DataFrame, district_stats: pd.DataFrame, s3_client):
    """Save soil data to S3"""
    ts = datetime.now(timezone.utc)
    prefix = f"soil/processed/{ts.strftime('%Y/%m')}"

    # Full dataset
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=f"{prefix}/soil_health_cards.csv",
        Body=df.to_csv(index=False),
        ContentType="text/csv",
    )

    # District aggregations (used by ML models)
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=f"{prefix}/district_soil_stats.csv",
        Body=district_stats.to_csv(index=False),
        ContentType="text/csv",
    )

    print(f"Soil data saved to S3: {S3_BUCKET}/{prefix}/")


def run_pipeline():
    """Main soil ETL pipeline"""
    print(f"[{datetime.now()}] Starting Soil Data ETL Pipeline")

    s3 = boto3.client("s3", region_name=AWS_REGION)
    df = generate_shc_dataset(n_samples=5000)
    df_processed, district_stats = process_soil_data(df)

    try:
        save_to_s3(df_processed, district_stats, s3)
    except Exception as e:
        print(f"S3 save skipped: {e}")
        # Save locally for testing
        os.makedirs("data", exist_ok=True)
        df_processed.to_csv("data/soil_health_cards.csv", index=False)
        district_stats.to_csv("data/district_soil_stats.csv", index=False)
        print("Saved locally to ./data/")

    print(f"Soil ETL Complete: {len(df_processed)} records processed")
    return {"processed": len(df_processed), "districts": len(district_stats)}


def lambda_handler(event, context):
    result = run_pipeline()
    return {"statusCode": 200, "body": json.dumps(result)}


if __name__ == "__main__":
    run_pipeline()
