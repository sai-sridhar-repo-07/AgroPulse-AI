"""
AgroPulse AI - Price Forecasting Model Training
Dataset: Kaggle - Indian Agricultural Mandi Prices (2023-2025)
         arjunyadav99/indian-agricultural-mandi-prices-20232025
         Real AGMARKNET wholesale prices from government-regulated mandis

Download dataset first:
    kaggle datasets download -d arjunyadav99/indian-agricultural-mandi-prices-20232025 -p ../data/ --unzip

Columns expected: date/Date, commodity/Commodity, state/State, district/District,
                  market/Market, modal_price/Modal_Price, min_price/Min_Price, max_price/Max_Price
Target: Forecast next 14–30 days of modal_price per commodity
"""

import json
import os
import sys
import warnings
from datetime import datetime, timedelta

import boto3
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")

# ─── Config ───────────────────────────────────────────────────────────────────
DATA_DIR     = os.path.join(os.path.dirname(__file__), "../data")
ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
S3_BUCKET    = os.getenv("S3_BUCKET_MODELS", "agropulse-model-artifacts")
AWS_REGION   = os.getenv("AWS_REGION", "ap-south-1")
RANDOM_STATE = 42

# Commodities to model
TARGET_COMMODITIES = [
    "Wheat", "Rice", "Maize", "Cotton", "Soyabean",
    "Onion", "Tomato", "Potato", "Groundnut", "Mustard"
]
FORECAST_DAYS = 30


# ─── 1. Load & Find CSV ───────────────────────────────────────────────────────
def find_csv() -> str:
    candidates = [
        "mandi_prices.csv", "indian_mandi_prices.csv",
        "Agricultural_Mandi_Prices.csv", "agmarknet_prices.csv",
        "commodity_prices.csv", "price_data.csv",
        "current-daily-price-of-various-commodities-india.csv",
    ]
    for name in candidates:
        path = os.path.join(DATA_DIR, name)
        if os.path.exists(path):
            return path
    # Try any CSV in data dir that has price-like columns
    for f in os.listdir(DATA_DIR):
        if f.endswith(".csv"):
            path = os.path.join(DATA_DIR, f)
            cols = pd.read_csv(path, nrows=2).columns.str.lower().tolist()
            if any("price" in c or "modal" in c for c in cols):
                return path
    print(f"\n[ERROR] Mandi price dataset not found in {DATA_DIR}")
    print("Download: kaggle datasets download -d arjunyadav99/indian-agricultural-mandi-prices-20232025 "
          "-p backend/ml/data/ --unzip")
    sys.exit(1)


def load_data() -> pd.DataFrame:
    path = find_csv()
    df = pd.read_csv(path, low_memory=False)
    print(f"[DATA] Loaded {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"[DATA] Columns: {list(df.columns)}")
    return df


# ─── 2. Clean & Standardise ──────────────────────────────────────────────────
def clean(df: pd.DataFrame) -> pd.DataFrame:
    # Normalise column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Map known variations to standard names
    rename = {}
    for col in df.columns:
        if "date" in col or col == "arrival_date":
            rename[col] = "date"
        elif "commodity" in col or "crop" in col:
            rename[col] = "commodity"
        elif "modal" in col:
            rename[col] = "modal_price"
        elif "min" in col and "price" in col:
            rename[col] = "min_price"
        elif "max" in col and "price" in col:
            rename[col] = "max_price"
        elif "state" in col:
            rename[col] = "state"
        elif "district" in col:
            rename[col] = "district"
        elif "market" in col:
            rename[col] = "market"

    df = df.rename(columns=rename)

    # Ensure required columns
    if "date" not in df.columns or "commodity" not in df.columns or "modal_price" not in df.columns:
        print(f"[ERROR] Required columns missing. Found: {list(df.columns)}")
        sys.exit(1)

    # Parse date
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "modal_price"])

    # Clean price
    df["modal_price"] = pd.to_numeric(
        df["modal_price"].astype(str).str.replace(",", ""), errors="coerce"
    )
    df = df.dropna(subset=["modal_price"])
    df = df[df["modal_price"] > 0]

    # Normalise commodity names (title case, strip)
    df["commodity"] = df["commodity"].astype(str).str.strip().str.title()

    # Filter to target commodities (fuzzy match)
    def match_commodity(name):
        name_lower = name.lower()
        for target in TARGET_COMMODITIES:
            if target.lower() in name_lower or name_lower in target.lower():
                return target
        return None

    df["commodity_std"] = df["commodity"].apply(match_commodity)
    df = df.dropna(subset=["commodity_std"])
    df["commodity"] = df["commodity_std"]
    df = df.drop(columns=["commodity_std"])

    df = df.sort_values("date").reset_index(drop=True)
    print(f"[CLEAN] After cleaning: {df.shape[0]:,} rows")
    print(f"[CLEAN] Commodities found: {df['commodity'].unique().tolist()}")
    print(f"[CLEAN] Date range: {df['date'].min().date()} → {df['date'].max().date()}")
    return df


# ─── 3. EDA ───────────────────────────────────────────────────────────────────
def run_eda(df: pd.DataFrame):
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    print("\n" + "="*60)
    print("EXPLORATORY DATA ANALYSIS — MANDI PRICES")
    print("="*60)

    print(f"\nShape        : {df.shape}")
    print(f"Date range   : {df['date'].min().date()} → {df['date'].max().date()}")
    print(f"Commodities  : {df['commodity'].nunique()}")
    print(f"\nRecords per commodity:\n{df['commodity'].value_counts()}")
    print(f"\nPrice stats (INR/Quintal):\n{df.groupby('commodity')['modal_price'].describe().round(1)}")

    # Price time series per commodity
    commodities = df["commodity"].unique()
    n = len(commodities)
    ncols = 2
    nrows = (n + 1) // 2
    fig, axes = plt.subplots(nrows, ncols, figsize=(16, 4 * nrows))
    axes = axes.flatten() if n > 1 else [axes]

    for i, comm in enumerate(commodities):
        sub = df[df["commodity"] == comm].groupby("date")["modal_price"].mean()
        axes[i].plot(sub.index, sub.values, linewidth=1.5, color="#22c55e", alpha=0.8)
        axes[i].set_title(f"{comm} — Price Trend")
        axes[i].set_ylabel("₹/Quintal")
        axes[i].grid(alpha=0.3)
        axes[i].tick_params(axis="x", rotation=30)

    for j in range(i + 1, len(axes)):
        axes[j].axis("off")

    plt.suptitle("AGMARKNET Mandi Prices — Real Data", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(f"{ARTIFACT_DIR}/eda_price_trends.png", dpi=100)
    plt.close()

    # Price distribution box plots
    fig, ax = plt.subplots(figsize=(14, 6))
    data_by_comm = [df[df["commodity"] == c]["modal_price"].values
                    for c in commodities]
    ax.boxplot(data_by_comm, labels=commodities, showfliers=False)
    ax.set_title("Price Distribution by Commodity (₹/Quintal)")
    ax.set_ylabel("₹/Quintal")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(f"{ARTIFACT_DIR}/eda_price_boxplot.png", dpi=100)
    plt.close()

    # Monthly seasonality
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%b")
    monthly = df.groupby(["commodity", "month"])["modal_price"].mean().reset_index()
    fig, ax = plt.subplots(figsize=(14, 6))
    for comm in commodities[:6]:  # Top 6 for readability
        sub = monthly[monthly["commodity"] == comm].sort_values("month")
        # Normalise to 100 base for comparison
        base = sub["modal_price"].mean()
        ax.plot(sub["month"], sub["modal_price"] / base * 100,
                marker="o", label=comm, linewidth=2)
    ax.set_title("Seasonal Index by Commodity (Base = 100)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Price Index")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(["Jan","Feb","Mar","Apr","May","Jun",
                         "Jul","Aug","Sep","Oct","Nov","Dec"])
    ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{ARTIFACT_DIR}/eda_seasonality.png", dpi=100)
    plt.close()

    print(f"[EDA] Plots saved to {ARTIFACT_DIR}/")


# ─── 4. Train Prophet per Commodity ─────────────────────────────────────────
def train_prophet(commodity_df: pd.DataFrame, commodity: str):
    try:
        from prophet import Prophet
        from prophet.diagnostics import cross_validation, performance_metrics
    except ImportError:
        print("[ERROR] Install Prophet: pip install prophet")
        sys.exit(1)

    # Prepare Prophet format
    daily = (commodity_df
             .groupby("date")["modal_price"]
             .mean()
             .reset_index()
             .rename(columns={"date": "ds", "modal_price": "y"}))
    daily = daily[daily["y"] > 0].sort_values("ds").reset_index(drop=True)

    # Need at least 30 days
    if len(daily) < 30:
        print(f"[SKIP] {commodity}: only {len(daily)} data points, need ≥30")
        return None, {}

    print(f"\n[PROPHET] Training {commodity} ({len(daily)} daily records)...")

    # 80/20 split for evaluation
    split_idx = int(len(daily) * 0.8)
    train_df = daily.iloc[:split_idx]
    test_df  = daily.iloc[split_idx:]

    model = Prophet(
        changepoint_prior_scale=0.1,       # Flexible trend
        seasonality_prior_scale=10.0,
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        uncertainty_samples=200,
        interval_width=0.95,
    )
    model.add_seasonality(name="monthly", period=30.5, fourier_order=7)
    model.add_seasonality(name="quarterly", period=91.25, fourier_order=5)
    model.fit(train_df)

    # Evaluate on holdout
    future_test = model.make_future_dataframe(periods=len(test_df))
    forecast_test = model.predict(future_test)
    preds = forecast_test.tail(len(test_df))["yhat"].values
    actual = test_df["y"].values

    mae  = np.abs(actual - preds).mean()
    mape = (np.abs(actual - preds) / np.maximum(actual, 1)).mean() * 100
    rmse = np.sqrt(np.mean((actual - preds)**2))

    print(f"  MAE  : {mae:.2f} INR/Quintal")
    print(f"  RMSE : {rmse:.2f} INR/Quintal")
    print(f"  MAPE : {mape:.2f}%")

    # Retrain on full data
    model_full = Prophet(
        changepoint_prior_scale=0.1,
        seasonality_prior_scale=10.0,
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        uncertainty_samples=200,
        interval_width=0.95,
    )
    model_full.add_seasonality(name="monthly", period=30.5, fourier_order=7)
    model_full.add_seasonality(name="quarterly", period=91.25, fourier_order=5)
    model_full.fit(daily)

    # 30-day forecast
    future = model_full.make_future_dataframe(periods=FORECAST_DAYS)
    forecast = model_full.predict(future)

    # Plot forecast
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(daily["ds"], daily["y"], color="#374151", linewidth=1,
            alpha=0.7, label="Historical")
    forecast_tail = forecast.tail(FORECAST_DAYS + 30)
    ax.plot(forecast_tail["ds"], forecast_tail["yhat"],
            color="#22c55e", linewidth=2.5, label="Forecast")
    ax.fill_between(forecast_tail["ds"],
                    forecast_tail["yhat_lower"],
                    forecast_tail["yhat_upper"],
                    alpha=0.2, color="#22c55e", label="95% CI")
    ax.set_title(f"{commodity} — Price Forecast (Prophet)")
    ax.set_ylabel("₹/Quintal")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{ARTIFACT_DIR}/forecast_{commodity.lower()}.png", dpi=100)
    plt.close()

    metrics = {
        "commodity": commodity,
        "n_records": int(len(daily)),
        "mae":       round(float(mae), 2),
        "rmse":      round(float(rmse), 2),
        "mape":      round(float(mape), 2),
        "current_price": round(float(daily["y"].iloc[-1]), 2),
        "forecast_14d":  round(float(forecast.tail(FORECAST_DAYS).head(14)["yhat"].mean()), 2),
        "forecast_30d":  round(float(forecast.tail(FORECAST_DAYS)["yhat"].mean()), 2),
    }
    return model_full, metrics


# ─── 5. Train All ─────────────────────────────────────────────────────────────
def train_all(df: pd.DataFrame):
    models      = {}
    all_metrics = []

    for commodity in df["commodity"].unique():
        sub = df[df["commodity"] == commodity].copy()
        model, metrics = train_prophet(sub, commodity)
        if model:
            models[commodity] = model
            all_metrics.append(metrics)

    return models, all_metrics


# ─── 6. Save ──────────────────────────────────────────────────────────────────
def save_artifacts(models, all_metrics):
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    for commodity, model in models.items():
        fname = f"price_model_{commodity.lower().replace(' ', '_')}.pkl"
        joblib.dump(model, f"{ARTIFACT_DIR}/{fname}")

    with open(f"{ARTIFACT_DIR}/price_metrics.json", "w") as f:
        json.dump(all_metrics, f, indent=2)

    # Summary table
    df_m = pd.DataFrame(all_metrics)
    print(f"\n[SUMMARY] Price Model Performance:\n{df_m[['commodity','mae','mape','n_records']].to_string(index=False)}")
    print(f"\n[SAVE] Artifacts saved to {ARTIFACT_DIR}/")

    try:
        s3 = boto3.client("s3", region_name=AWS_REGION)
        for fname in os.listdir(ARTIFACT_DIR):
            if fname.startswith("price_"):
                s3.upload_file(f"{ARTIFACT_DIR}/{fname}", S3_BUCKET,
                               f"models/price-forecasting/v2/{fname}")
        print(f"[S3]  Uploaded to S3")
    except Exception as e:
        print(f"[S3]  Upload skipped: {e}")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("="*60)
    print("AgroPulse AI — Price Forecasting Model Training")
    print("Dataset: AGMARKNET Real Mandi Prices (Kaggle)")
    print("Algorithm: Facebook Prophet (time-series)")
    print("="*60)

    df_raw = load_data()
    df     = clean(df_raw)
    run_eda(df)

    models, all_metrics = train_all(df)
    save_artifacts(models, all_metrics)

    avg_mape = np.mean([m["mape"] for m in all_metrics]) if all_metrics else 0
    print("\n" + "="*60)
    print(f"Training Complete!")
    print(f"Models trained : {len(models)} commodities")
    print(f"Avg MAPE       : {avg_mape:.2f}%")
    print("="*60)


if __name__ == "__main__":
    main()
