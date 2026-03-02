"""
AgroPulse AI - Agricultural Risk Detection Model Training
Datasets:
  1. Kaggle - Rainfall in India (rajanand/rainfall-in-india)
     District-level monthly rainfall 1901-2015 (IMD data)
  2. Kaggle - Flood Risk in India (s3programmer/flood-risk-in-india)

Download datasets:
    kaggle datasets download -d rajanand/rainfall-in-india -p ../data/ --unzip
    kaggle datasets download -d s3programmer/flood-risk-in-india -p ../data/ --unzip

Approach:
  - Compute rainfall deviation (% from 30-year normal) per district/month
  - Derive drought / flood / heat risk features from real IMD data
  - Train Isolation Forest (unsupervised) + Random Forest classifier (supervised)
  - Compare both and save best model
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
from scipy.special import expit
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import (classification_report, roc_auc_score,
                              confusion_matrix, ConfusionMatrixDisplay,
                              precision_recall_curve)
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ─── Config ───────────────────────────────────────────────────────────────────
DATA_DIR     = os.path.join(os.path.dirname(__file__), "../data")
ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
S3_BUCKET    = os.getenv("S3_BUCKET_MODELS", "agropulse-model-artifacts")
AWS_REGION   = os.getenv("AWS_REGION", "ap-south-1")
RANDOM_STATE = 42

FEATURE_COLS = [
    "rainfall_deviation_pct",
    "drought_index",
    "flood_index",
    "annual_rainfall_pct",
    "monsoon_onset_deviation",
    "cv_rainfall",
    "consecutive_dry_months",
    "rainfall_trend",
]


# ─── 1. Load Rainfall Dataset ────────────────────────────────────────────────
def find_rainfall_csv() -> str:
    # Exact filenames from the Kaggle rajanand/rainfall-in-india dataset
    candidates = [
        "rainfall in india 1901-2015.csv",
        "district wise rainfall normal.csv",
        "rainfall in india.csv",
        "rainfall_india.csv",
        "Rainfall_india.csv",
        "Sub_Division_IMD_2017.csv",
        "rainfall-in-india.csv",
        "district_rainfall.csv",
    ]
    for name in candidates:
        path = os.path.join(DATA_DIR, name)
        if os.path.exists(path):
            return path
    # Fallback: scan for CSVs with monthly rainfall columns (JAN..DEC)
    # but explicitly skip known non-rainfall files
    skip_files = {"Crop_recommendation.csv", "crop_production.csv",
                  "Agriculture_price_dataset.csv"}
    for f in os.listdir(DATA_DIR):
        if f.endswith(".csv") and f not in skip_files:
            path = os.path.join(DATA_DIR, f)
            try:
                cols = pd.read_csv(path, nrows=2).columns.str.upper().tolist()
                month_hits = sum(1 for c in cols if c in
                                 ["JAN","FEB","MAR","APR","MAY","JUN",
                                  "JUL","AUG","SEP","OCT","NOV","DEC"])
                if month_hits >= 6:   # Must have at least 6 month columns
                    return path
            except Exception:
                continue
    print(f"\n[ERROR] Rainfall dataset not found in {DATA_DIR}")
    print("Download: kaggle datasets download -d rajanand/rainfall-in-india "
          "-p backend/ml/data/ --unzip")
    sys.exit(1)


def load_rainfall_data() -> pd.DataFrame:
    path = find_rainfall_csv()
    df = pd.read_csv(path)
    print(f"[DATA] Loaded {df.shape[0]:,} rows × {df.shape[1]} columns from {os.path.basename(path)}")
    print(f"[DATA] Columns: {list(df.columns)}")
    return df


# ─── 2. Engineer Risk Features from Rainfall Data ────────────────────────────
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute risk features from real IMD rainfall data.
    The IMD dataset has columns: SUBDIVISION, YEAR, JAN, FEB, ..., DEC, ANNUAL
    """
    df.columns = [c.strip().upper() for c in df.columns]

    # Detect month columns
    month_cols = [c for c in df.columns if c in [
        "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
        "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"
    ]]

    if not month_cols:
        print(f"[WARN] No monthly columns found. Attempting fallback...")
        num_cols = df.select_dtypes(include=np.number).columns.tolist()
        month_cols = num_cols[:12] if len(num_cols) >= 12 else num_cols

    if "YEAR" not in df.columns:
        yr_candidates = [c for c in df.columns if "year" in c.lower() or "yr" in c.lower()]
        if yr_candidates:
            df = df.rename(columns={yr_candidates[0]: "YEAR"})
        else:
            df["YEAR"] = range(1900, 1900 + len(df))

    if "SUBDIVISION" not in df.columns:
        sub_candidates = [c for c in df.columns
                          if any(k in c.lower() for k in ["sub", "district", "state", "region"])]
        df = df.rename(columns={sub_candidates[0]: "SUBDIVISION"}) if sub_candidates else None
        if "SUBDIVISION" not in df.columns:
            df["SUBDIVISION"] = "India"

    print(f"[FEAT] Using month columns: {month_cols}")
    df["ANNUAL_COMPUTED"] = df[month_cols].sum(axis=1)

    records = []
    for subdivision, group in df.groupby("SUBDIVISION"):
        group = group.sort_values("YEAR").reset_index(drop=True)
        annual = group["ANNUAL_COMPUTED"].values

        for i in range(len(group)):
            year = group["YEAR"].iloc[i]
            start = max(0, i - 29)
            normal = annual[start:i].mean() if i > 0 else annual.mean()
            if normal == 0 or np.isnan(normal):
                continue

            ann = annual[i]
            rain_dev_pct = ((ann - normal) / normal) * 100

            monthly_vals = group[month_cols].iloc[i].values
            monthly_normals = (group[month_cols].iloc[start:i].mean().values
                               if i > 0 else group[month_cols].mean().values)

            dry_months = int(np.sum(monthly_vals < 0.5 * monthly_normals))

            excess = np.maximum(monthly_vals - 1.5 * monthly_normals, 0)
            flood_idx = float(excess.max() / (normal / 12 + 1))

            consec = 0
            max_consec = 0
            for mv in monthly_vals:
                norm_m = normal / 12
                if mv < 0.4 * norm_m:
                    consec += 1
                    max_consec = max(max_consec, consec)
                else:
                    consec = 0

            cv = float(annual[max(0, i-9):i].std() / (annual[max(0, i-9):i].mean() + 1)) \
                if i >= 5 else 0.0

            trend = float(np.polyfit(range(5), annual[i-4:i+1], 1)[0] / (normal + 1)) \
                if i >= 4 else 0.0

            ann_pct = (ann / normal) * 100

            jun_val = float(group["JUN"].iloc[i]) if "JUN" in group.columns else ann * 0.15
            jun_norm = float(group["JUN"].iloc[start:i].mean()) \
                if i > 0 and "JUN" in group.columns else ann * 0.15
            monsoon_dev = ((jun_val - jun_norm) / (jun_norm + 1)) * 30

            # Risk label based on IMD drought/flood criteria
            if ann_pct < 75:
                risk_label = 1   # Drought
            elif ann_pct > 150 or flood_idx > 2.0:
                risk_label = 1   # Flood
            elif ann_pct < 85 or dry_months >= 4:
                risk_label = 1   # Moderate risk
            else:
                risk_label = 0   # Normal

            records.append({
                "subdivision":             subdivision,
                "year":                    int(year),
                "rainfall_deviation_pct":  round(float(rain_dev_pct), 2),
                "drought_index":           round(float(dry_months / 12), 3),
                "flood_index":             round(float(min(flood_idx, 10)), 3),
                "annual_rainfall_pct":     round(float(ann_pct), 2),
                "monsoon_onset_deviation": round(float(np.clip(monsoon_dev, -30, 30)), 2),
                "cv_rainfall":             round(float(cv), 4),
                "consecutive_dry_months":  int(max_consec),
                "rainfall_trend":          round(float(np.clip(trend, -0.5, 0.5)), 4),
                "is_risk":                 int(risk_label),
            })

    result = pd.DataFrame(records)
    risk_rate = result["is_risk"].mean()
    print(f"[FEAT] Engineered {len(result):,} samples | Risk rate: {risk_rate:.1%}")
    return result


# ─── 3. EDA ───────────────────────────────────────────────────────────────────
def run_eda(df: pd.DataFrame):
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    print("\n" + "="*60)
    print("EXPLORATORY DATA ANALYSIS — RISK FEATURES")
    print("="*60)

    print(f"\nShape        : {df.shape}")
    print(f"Risk rate    : {df['is_risk'].mean():.1%} ({df['is_risk'].sum()} risk samples)")
    feat_cols_present = [c for c in FEATURE_COLS if c in df.columns]
    print(f"\nFeature Stats:\n{df[feat_cols_present].describe().round(3)}")

    # Feature distributions: Normal vs Risk
    n = len(feat_cols_present)
    ncols = 4
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(16, 4 * nrows))
    axes = axes.flatten()
    for i, col in enumerate(feat_cols_present):
        axes[i].hist(df[df["is_risk"] == 0][col], bins=30, alpha=0.6,
                     color="#22c55e", label="Normal", density=True)
        axes[i].hist(df[df["is_risk"] == 1][col], bins=30, alpha=0.6,
                     color="#ef4444", label="Risk", density=True)
        axes[i].set_title(col.replace("_", " ").title())
        axes[i].legend(fontsize=8)
    for j in range(i + 1, len(axes)):
        axes[j].axis("off")
    plt.suptitle("Feature Distributions: Normal vs Risk (Real IMD Data)",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(f"{ARTIFACT_DIR}/eda_risk_features.png", dpi=100)
    plt.close()

    # Correlation heatmap
    corr = df[feat_cols_present + ["is_risk"]].corr()
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdYlGn_r",
                center=0, ax=ax, linewidths=0.5)
    ax.set_title("Feature Correlation with Risk Label")
    plt.tight_layout()
    plt.savefig(f"{ARTIFACT_DIR}/eda_risk_correlation.png", dpi=100)
    plt.close()

    # Risk rate over time
    if "year" in df.columns:
        risk_trend = df.groupby("year")["is_risk"].mean()
        fig, ax = plt.subplots(figsize=(14, 5))
        ax.plot(risk_trend.index, risk_trend.values * 100,
                color="#ef4444", linewidth=2)
        ax.fill_between(risk_trend.index, risk_trend.values * 100,
                        alpha=0.2, color="#ef4444")
        ax.set_title("% Agricultural Risk Years Over Time (India — IMD Data)")
        ax.set_ylabel("% Subdivisions at Risk")
        ax.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{ARTIFACT_DIR}/eda_risk_trend.png", dpi=100)
        plt.close()

    print(f"[EDA] Plots saved to {ARTIFACT_DIR}/")


# ─── 4. Train Models ──────────────────────────────────────────────────────────
def train_models(df: pd.DataFrame):
    feat_cols = [c for c in FEATURE_COLS if c in df.columns]
    X = df[feat_cols].fillna(0).values
    y = df["is_risk"].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    print(f"\n[PREP] Features: {feat_cols}")
    print(f"[PREP] Train: {X_train.shape} | Test: {X_test.shape}")
    print(f"[PREP] Risk rate — train: {y_train.mean():.1%} | test: {y_test.mean():.1%}")

    # ── Model A: Isolation Forest (unsupervised) ──────────────────────────────
    print("\n[IF] Training Isolation Forest (unsupervised)...")
    contamination = float(np.clip(y_train.mean(), 0.05, 0.45))
    iso = IsolationForest(
        n_estimators=300, contamination=contamination,
        max_samples="auto", random_state=RANDOM_STATE, n_jobs=-1,
    )
    iso.fit(X_train[y_train == 0])  # Only normal samples
    iso_scores = 1 - expit(iso.score_samples(X_test))
    iso_pred   = (iso.predict(X_test) == -1).astype(int)
    iso_auc = roc_auc_score(y_test, iso_scores)
    print(f"  AUC-ROC : {iso_auc:.4f}")
    print(classification_report(y_test, iso_pred, target_names=["Normal", "Risk"]))

    # ── Model B: Random Forest (supervised) ──────────────────────────────────
    print("\n[RF] Training Random Forest Classifier (supervised)...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    rf = RandomForestClassifier(
        n_estimators=300, max_depth=None, min_samples_leaf=3,
        class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1,
    )
    cv_scores = cross_val_score(rf, X_train, y_train, cv=cv,
                                scoring="roc_auc", n_jobs=-1)
    print(f"  5-Fold CV AUC : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    rf.fit(X_train, y_train)
    rf_proba = rf.predict_proba(X_test)[:, 1]
    rf_pred  = rf.predict(X_test)
    rf_auc   = roc_auc_score(y_test, rf_proba)
    print(f"  Test AUC-ROC  : {rf_auc:.4f}")
    print(classification_report(y_test, rf_pred, target_names=["Normal", "Risk"]))

    # Feature importance plot
    fi = dict(sorted(zip(feat_cols, rf.feature_importances_),
                     key=lambda x: x[1], reverse=True))
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(list(fi.keys()), list(fi.values()), color="#ef4444", edgecolor="white")
    ax.set_title("Feature Importance — Risk Detection (Random Forest)")
    plt.tight_layout()
    plt.savefig(f"{ARTIFACT_DIR}/risk_feature_importance.png", dpi=100)
    plt.close()

    # Confusion matrix
    cm = confusion_matrix(y_test, rf_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    ConfusionMatrixDisplay(cm, display_labels=["Normal", "Risk"]).plot(
        ax=ax, colorbar=False)
    ax.set_title("Risk Detection — Confusion Matrix (RF)")
    plt.tight_layout()
    plt.savefig(f"{ARTIFACT_DIR}/risk_confusion_matrix.png", dpi=100)
    plt.close()

    # Precision-Recall curve
    precision, recall, _ = precision_recall_curve(y_test, rf_proba)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(recall, precision, color="#ef4444", linewidth=2)
    ax.set_title("Precision-Recall Curve (Risk Detection)")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{ARTIFACT_DIR}/risk_precision_recall.png", dpi=100)
    plt.close()

    best_name = "RandomForest" if rf_auc >= iso_auc else "IsolationForest"
    metrics = {
        "model_version":    "risk-real-v2",
        "best_model":       best_name,
        "dataset":          "rajanand/rainfall-in-india (IMD)",
        "n_train":          int(len(X_train)),
        "n_test":           int(len(X_test)),
        "features":         feat_cols,
        "isolation_forest": {"auc_roc": round(float(iso_auc), 4)},
        "random_forest": {
            "auc_roc": round(float(rf_auc), 4),
            "cv_mean": round(float(cv_scores.mean()), 4),
            "cv_std":  round(float(cv_scores.std()), 4),
        },
        "feature_importance": {k: round(float(v), 4) for k, v in fi.items()},
        "risk_thresholds": {
            "low": 0.25, "medium": 0.50, "high": 0.75, "critical": 0.90
        },
    }
    return iso, rf, scaler, metrics


# ─── 5. Save ──────────────────────────────────────────────────────────────────
def save_artifacts(iso, rf, scaler, metrics):
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    joblib.dump(iso,    f"{ARTIFACT_DIR}/risk_isolation_forest.pkl")
    joblib.dump(rf,     f"{ARTIFACT_DIR}/risk_random_forest.pkl")
    joblib.dump(scaler, f"{ARTIFACT_DIR}/risk_scaler.pkl")
    with open(f"{ARTIFACT_DIR}/risk_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[SAVE] Artifacts saved to {ARTIFACT_DIR}/")

    try:
        s3 = boto3.client("s3", region_name=AWS_REGION)
        for fname in ["risk_isolation_forest.pkl", "risk_random_forest.pkl",
                      "risk_scaler.pkl", "risk_metrics.json"]:
            s3.upload_file(f"{ARTIFACT_DIR}/{fname}", S3_BUCKET,
                           f"models/risk-detection/v2/{fname}")
        print(f"[S3]  Uploaded to S3")
    except Exception as e:
        print(f"[S3]  Upload skipped: {e}")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("="*60)
    print("AgroPulse AI — Risk Detection Model Training")
    print("Dataset: IMD Rainfall India (Kaggle rajanand/rainfall-in-india)")
    print("Models: Isolation Forest + Random Forest Classifier")
    print("="*60)

    df_raw  = load_rainfall_data()
    df_feat = engineer_features(df_raw)
    run_eda(df_feat)
    iso, rf, scaler, metrics = train_models(df_feat)
    save_artifacts(iso, rf, scaler, metrics)

    print("\n" + "="*60)
    print(f"Training Complete!")
    print(f"Best model       : {metrics['best_model']}")
    print(f"RF AUC-ROC       : {metrics['random_forest']['auc_roc']:.4f}")
    print(f"IF AUC-ROC       : {metrics['isolation_forest']['auc_roc']:.4f}")
    print(f"Top risk feature : {list(metrics['feature_importance'].keys())[0]}")
    print("="*60)


if __name__ == "__main__":
    main()
