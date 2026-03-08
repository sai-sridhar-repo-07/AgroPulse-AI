"""
AgroPulse AI - Yield Prediction Model Training
Dataset: Kaggle - Crop Production in India (abhinand05/crop-production-in-india)
         246,091 rows | 33 Indian states | 124 crop types | 1997-2015
         Ministry of Agriculture India official data

Download dataset first:
    kaggle datasets download -d abhinand05/crop-production-in-india -p ../data/ --unzip

Columns: State_Name, District_Name, Crop_Year, Season, Crop, Area, Production
Derived: Yield_kg_per_ha = (Production * 1000) / Area  [Production in tonnes]
"""

import json
import os
import sys
import warnings

import boto3
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import (GradientBoostingRegressor, RandomForestRegressor,
                               ExtraTreesRegressor)
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
import xgboost as xgb

warnings.filterwarnings("ignore")

# ─── Config ───────────────────────────────────────────────────────────────────
DATA_DIR     = os.path.join(os.path.dirname(__file__), "../data")
ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
S3_BUCKET    = os.getenv("S3_BUCKET_MODELS", "agropulse-model-artifacts")
AWS_REGION   = os.getenv("AWS_REGION", "ap-south-1")
RANDOM_STATE = 42

# Target crops for AgroPulse (filter dataset to these)
TARGET_CROPS = [
    "Rice", "Wheat", "Maize", "Cotton(lint)", "Sugarcane",
    "Chickpea", "Lentil", "Soyabean", "Groundnut", "Moong(Green Gram)",
    "Urad", "Jute", "Coffee", "Coconut", "Banana",
]

FEATURE_COLS = ["crop_enc", "state_enc", "season_enc", "area_log",
                "crop_year_norm"]


# ─── 1. Load & Find CSV ───────────────────────────────────────────────────────
def find_csv() -> str:
    candidates = [
        "crop_production.csv", "APY_Output.csv", "apy.csv",
        "crop_production_india.csv", "Crop_production_statewise.csv",
    ]
    for name in candidates:
        path = os.path.join(DATA_DIR, name)
        if os.path.exists(path):
            return path
    print(f"\n[ERROR] Yield dataset not found in {DATA_DIR}")
    print("Expected one of:", candidates)
    print("Download: kaggle datasets download -d abhinand05/crop-production-in-india "
          "-p backend/ml/data/ --unzip")
    sys.exit(1)


def load_data() -> pd.DataFrame:
    path = find_csv()
    df = pd.read_csv(path)
    print(f"[DATA] Loaded {df.shape[0]:,} rows × {df.shape[1]} columns from {os.path.basename(path)}")
    print(f"[DATA] Columns: {list(df.columns)}")
    return df


# ─── 2. Clean & Compute Yield ────────────────────────────────────────────────
def clean(df: pd.DataFrame) -> pd.DataFrame:
    # Normalise column names
    df.columns = [c.strip() for c in df.columns]

    # Rename to standard names if needed
    col_map = {
        "State_Name": "State_Name", "state_name": "State_Name",
        "District_Name": "District_Name", "district_name": "District_Name",
        "Crop_Year": "Crop_Year", "crop_year": "Crop_Year",
        "Season": "Season", "season": "Season",
        "Crop": "Crop", "crop": "Crop",
        "Area": "Area", "area": "Area",
        "Production": "Production", "production": "Production",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    req = ["Crop", "Area", "Production", "Season", "State_Name", "Crop_Year"]
    missing_req = [c for c in req if c not in df.columns]
    if missing_req:
        print(f"[WARN] Missing columns: {missing_req}")
        # Try to work with available columns
        if "Crop" not in df.columns or "Area" not in df.columns:
            print("[ERROR] Cannot proceed without Crop and Area columns")
            sys.exit(1)

    # Drop rows with missing Area or Production
    df = df.dropna(subset=["Area", "Production"])
    df = df[df["Area"] > 0]
    df = df[df["Production"] > 0]

    # Compute yield (Production in tonnes → kg/ha)
    df["yield_kg_ha"] = (df["Production"] * 1000) / df["Area"]

    # Remove extreme outliers (yield > 500 tonnes/ha is impossible)
    df = df[df["yield_kg_ha"] < 500_000]
    df = df[df["yield_kg_ha"] > 10]

    # Filter to crops we care about (case-insensitive partial match)
    target_lower = [c.lower() for c in TARGET_CROPS]
    df["crop_lower"] = df["Crop"].str.strip().str.lower()
    df = df[df["crop_lower"].apply(
        lambda c: any(t in c or c in t for t in target_lower)
    )].copy()

    # Clean Season
    if "Season" in df.columns:
        season_map = {
            "kharif": "Kharif", "rabi": "Rabi", "zaid": "Zaid",
            "whole year": "Whole Year", "autumn": "Autumn", "summer": "Summer",
        }
        df["Season"] = df["Season"].str.strip().str.lower().map(
            lambda s: season_map.get(s, "Kharif")
        )

    df = df.reset_index(drop=True)
    print(f"[CLEAN] After cleaning: {df.shape[0]:,} rows | "
          f"{df['Crop'].nunique()} crops | "
          f"{df['State_Name'].nunique() if 'State_Name' in df.columns else '?'} states")
    return df


# ─── 3. EDA ───────────────────────────────────────────────────────────────────
def run_eda(df: pd.DataFrame):
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    print("\n" + "="*60)
    print("EXPLORATORY DATA ANALYSIS — YIELD")
    print("="*60)

    print(f"\nShape        : {df.shape}")
    print(f"Missing vals :\n{df[['Crop','Area','Production','yield_kg_ha']].isnull().sum()}")
    print(f"\nYield Statistics (kg/ha):\n{df['yield_kg_ha'].describe().round(1)}")
    print(f"\nTop 10 crops by row count:\n{df['Crop'].value_counts().head(10)}")
    if "State_Name" in df.columns:
        print(f"\nTop 10 states:\n{df['State_Name'].value_counts().head(10)}")

    # Yield distribution
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].hist(df["yield_kg_ha"], bins=60, color="#3b82f6", edgecolor="white", alpha=0.8)
    axes[0].set_title("Yield Distribution (kg/ha)")
    axes[0].set_xlabel("Yield kg/ha")
    axes[1].hist(np.log1p(df["yield_kg_ha"]), bins=60, color="#22c55e",
                 edgecolor="white", alpha=0.8)
    axes[1].set_title("Log(Yield) Distribution")
    axes[1].set_xlabel("log(1 + Yield)")
    plt.tight_layout()
    plt.savefig(f"{ARTIFACT_DIR}/eda_yield_dist.png", dpi=100)
    plt.close()

    # Mean yield per crop
    crop_yield = df.groupby("Crop")["yield_kg_ha"].median().sort_values(ascending=False).head(15)
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.barh(crop_yield.index, crop_yield.values, color="#22c55e", edgecolor="white")
    ax.set_title("Median Yield by Crop (kg/ha)")
    ax.set_xlabel("Median Yield (kg/ha)")
    plt.tight_layout()
    plt.savefig(f"{ARTIFACT_DIR}/eda_yield_by_crop.png", dpi=100)
    plt.close()

    # Yield trend over years
    if "Crop_Year" in df.columns:
        year_yield = df.groupby("Crop_Year")["yield_kg_ha"].median()
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(year_yield.index, year_yield.values, marker="o",
                color="#3b82f6", linewidth=2)
        ax.set_title("Median Crop Yield Over Years (India)")
        ax.set_xlabel("Year")
        ax.set_ylabel("Median Yield (kg/ha)")
        ax.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{ARTIFACT_DIR}/eda_yield_trend.png", dpi=100)
        plt.close()

    # Season box plot
    if "Season" in df.columns:
        fig, ax = plt.subplots(figsize=(10, 5))
        seasons = df.groupby("Season")["yield_kg_ha"].apply(list)
        ax.boxplot([v for v in seasons], labels=seasons.index, showfliers=False)
        ax.set_title("Yield Distribution by Season")
        ax.set_ylabel("Yield (kg/ha)")
        plt.xticks(rotation=30)
        plt.tight_layout()
        plt.savefig(f"{ARTIFACT_DIR}/eda_yield_by_season.png", dpi=100)
        plt.close()

    print(f"[EDA] Plots saved to {ARTIFACT_DIR}/")


# ─── 4. Feature Engineering & Preprocess ────────────────────────────────────
def preprocess(df: pd.DataFrame):
    encoders = {}

    # Encode categoricals
    for col, enc_col in [("Crop", "crop_enc"),
                          ("State_Name", "state_enc") if "State_Name" in df.columns else ("Crop", "crop_enc"),
                          ("Season", "season_enc") if "Season" in df.columns else ("Crop", "crop_enc")]:
        if col in df.columns and enc_col not in df.columns:
            le = LabelEncoder()
            df[enc_col] = le.fit_transform(df[col].astype(str))
            encoders[col] = le

    # Ensure all feature columns exist
    if "state_enc" not in df.columns:
        df["state_enc"] = 0
    if "season_enc" not in df.columns:
        df["season_enc"] = 0

    # Log-transform area (heavy right skew)
    df["area_log"] = np.log1p(df["Area"])

    # Normalise year
    if "Crop_Year" in df.columns:
        min_yr = df["Crop_Year"].min()
        df["crop_year_norm"] = df["Crop_Year"] - min_yr
    else:
        df["crop_year_norm"] = 0

    # Log-transform target
    df["yield_log"] = np.log1p(df["yield_kg_ha"])

    feat_cols = [c for c in FEATURE_COLS if c in df.columns]
    X = df[feat_cols].values
    y = df["yield_log"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    print(f"[PREP] Features used: {feat_cols}")
    print(f"[PREP] Train: {X_train_s.shape} | Test: {X_test_s.shape}")
    return X_train_s, X_test_s, y_train, y_test, scaler, encoders, feat_cols


# ─── 5. Compare Models ───────────────────────────────────────────────────────
def compare_models(X_train, y_train):
    cv = KFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    models = {
        "XGBoost": xgb.XGBRegressor(
            n_estimators=150, max_depth=5, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            random_state=RANDOM_STATE, n_jobs=-1
        ),
        "Random Forest": RandomForestRegressor(
            n_estimators=80, max_depth=12,
            min_samples_leaf=5, random_state=RANDOM_STATE, n_jobs=-1
        ),
        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=150, max_depth=5, learning_rate=0.1,
            subsample=0.8, random_state=RANDOM_STATE
        ),
        "Extra Trees": ExtraTreesRegressor(
            n_estimators=80, max_depth=12, random_state=RANDOM_STATE, n_jobs=-1
        ),
    }

    print("\n" + "="*60)
    print("MODEL COMPARISON (5-Fold CV — R² on log-yield)")
    print("="*60)
    results = {}
    for name, m in models.items():
        scores = cross_val_score(m, X_train, y_train, cv=cv,
                                 scoring="r2", n_jobs=-1)
        print(f"  {name:25s}: R² = {scores.mean():.4f} ± {scores.std():.4f}")
        results[name] = (scores.mean(), scores.std(), m)

    best = max(results, key=lambda k: results[k][0])
    print(f"\n[BEST] {best} selected (R²={results[best][0]:.4f})")
    return results[best][2], best, results


# ─── 6. Evaluate ─────────────────────────────────────────────────────────────
def evaluate(model, X_test, y_test, feat_cols):
    model.fit(model.__class__(**model.get_params()).get_params() if False else model, None) \
        if False else None  # noop

    y_pred_log = model.predict(X_test)
    # Convert back from log
    y_pred = np.expm1(y_pred_log)
    y_true = np.expm1(y_test)

    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    mape = np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1))) * 100

    print(f"\n[EVAL] On actual yield (kg/ha):")
    print(f"  MAE  : {mae:.1f} kg/ha")
    print(f"  RMSE : {rmse:.1f} kg/ha")
    print(f"  R²   : {r2:.4f}")
    print(f"  MAPE : {mape:.2f}%")

    # Actual vs Predicted scatter
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.scatter(y_true[:2000], y_pred[:2000], alpha=0.3, s=10, color="#22c55e")
    lims = [min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())]
    ax.plot(lims, lims, "r--", linewidth=1.5, label="Perfect prediction")
    ax.set_xlabel("Actual Yield (kg/ha)")
    ax.set_ylabel("Predicted Yield (kg/ha)")
    ax.set_title(f"Actual vs Predicted Yield (R²={r2:.3f})")
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"{ARTIFACT_DIR}/eval_actual_vs_predicted.png", dpi=100)
    plt.close()

    # Feature importance
    if hasattr(model, "feature_importances_"):
        fi = dict(zip(feat_cols, model.feature_importances_))
        fi = dict(sorted(fi.items(), key=lambda x: x[1], reverse=True))
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.barh(list(fi.keys()), list(fi.values()), color="#3b82f6", edgecolor="white")
        ax.set_title("Feature Importance (Yield Model)")
        plt.tight_layout()
        plt.savefig(f"{ARTIFACT_DIR}/yield_feature_importance.png", dpi=100)
        plt.close()
        return {"mae": float(mae), "rmse": float(rmse), "r2": float(r2), "mape": float(mape)}, fi

    return {"mae": float(mae), "rmse": float(rmse), "r2": float(r2), "mape": float(mape)}, {}


# ─── 7. Save ──────────────────────────────────────────────────────────────────
def save_artifacts(model, scaler, encoders, metrics):
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    joblib.dump(model,    f"{ARTIFACT_DIR}/yield_model.pkl")
    joblib.dump(scaler,   f"{ARTIFACT_DIR}/yield_scaler.pkl")
    joblib.dump(encoders, f"{ARTIFACT_DIR}/yield_encoders.pkl")
    with open(f"{ARTIFACT_DIR}/yield_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[SAVE] Artifacts saved to {ARTIFACT_DIR}/")

    try:
        s3 = boto3.client("s3", region_name=AWS_REGION)
        for fname in ["yield_model.pkl", "yield_scaler.pkl",
                      "yield_encoders.pkl", "yield_metrics.json"]:
            s3.upload_file(f"{ARTIFACT_DIR}/{fname}", S3_BUCKET,
                           f"models/yield-prediction/v2/{fname}")
        print(f"[S3]  Uploaded to S3")
    except Exception as e:
        print(f"[S3]  Upload skipped: {e}")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("="*60)
    print("AgroPulse AI — Yield Prediction Model Training")
    print("Dataset: Kaggle — abhinand05/crop-production-in-india")
    print("="*60)

    df_raw = load_data()
    df     = clean(df_raw)
    run_eda(df)

    X_train, X_test, y_train, y_test, scaler, encoders, feat_cols = preprocess(df)

    best_model, best_name, all_results = compare_models(X_train, y_train)

    # Retrain best model on full train set
    best_model.fit(X_train, y_train)
    eval_metrics, feat_importance = evaluate(best_model, X_test, y_test, feat_cols)

    metrics = {
        "model_version":     "yield-real-v2",
        "algorithm":         best_name,
        "dataset":           "abhinand05/crop-production-in-india",
        "n_train":           int(len(X_train)),
        "n_test":            int(len(X_test)),
        "target_crops":      TARGET_CROPS,
        "features":          feat_cols,
        "eval_metrics":      eval_metrics,
        "feature_importance": feat_importance,
        "model_comparison": {
            name: {"r2_mean": round(float(r[0]), 4), "r2_std": round(float(r[1]), 4)}
            for name, r in all_results.items()
        },
    }
    save_artifacts(best_model, scaler, encoders, metrics)

    print("\n" + "="*60)
    print(f"Training Complete!")
    print(f"Model : {best_name}")
    print(f"R²    : {eval_metrics['r2']:.4f}")
    print(f"MAE   : {eval_metrics['mae']:.1f} kg/ha")
    print(f"MAPE  : {eval_metrics['mape']:.2f}%")
    print("="*60)


if __name__ == "__main__":
    main()
