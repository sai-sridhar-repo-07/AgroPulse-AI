"""
AgroPulse AI - Crop Recommendation Model Training
Dataset: Kaggle - Crop Recommendation Dataset (atharvaingle/crop-recommendation-dataset)
         Real hand-collected data by Indian Chamber of Food and Agriculture
         2,200 rows | 22 crop classes | 7 features

Download dataset first:
    kaggle datasets download -d atharvaingle/crop-recommendation-dataset -p ../data/ --unzip

Features: N, P, K (soil nutrients kg/ha), temperature (°C), humidity (%), pH, rainfall (mm)
Target:   22 crop classes
"""

import json
import os
import warnings
import sys

import boto3
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import shap
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (accuracy_score, classification_report,
                              confusion_matrix, ConfusionMatrixDisplay)
from sklearn.model_selection import (cross_val_score, train_test_split,
                                     GridSearchCV, StratifiedKFold)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC
import xgboost as xgb

warnings.filterwarnings("ignore")

# ─── Config ───────────────────────────────────────────────────────────────────
DATA_DIR    = os.path.join(os.path.dirname(__file__), "../data")
CSV_PATH    = os.path.join(DATA_DIR, "Crop_recommendation.csv")
ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
S3_BUCKET   = os.getenv("S3_BUCKET_MODELS", "agropulse-model-artifacts")
AWS_REGION  = os.getenv("AWS_REGION", "ap-south-1")
RANDOM_STATE = 42
FEATURE_COLS = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
TARGET_COL   = "label"


# ─── 1. Load Data ─────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    if not os.path.exists(CSV_PATH):
        print(f"\n[ERROR] Dataset not found at: {CSV_PATH}")
        print("Download it with:")
        print("  kaggle datasets download -d atharvaingle/crop-recommendation-dataset -p backend/ml/data/ --unzip")
        sys.exit(1)

    df = pd.read_csv(CSV_PATH)
    print(f"[DATA] Loaded {df.shape[0]} rows × {df.shape[1]} columns")
    return df


# ─── 2. EDA ───────────────────────────────────────────────────────────────────
def run_eda(df: pd.DataFrame):
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    print("\n" + "="*60)
    print("EXPLORATORY DATA ANALYSIS")
    print("="*60)

    # Basic info
    print(f"\nShape        : {df.shape}")
    print(f"Columns      : {list(df.columns)}")
    print(f"Dtypes       :\n{df.dtypes}")
    print(f"\nMissing vals :\n{df.isnull().sum()}")
    print(f"\nDuplicates   : {df.duplicated().sum()}")
    print(f"\nClass distribution:\n{df[TARGET_COL].value_counts()}")
    print(f"\nStatistical Summary:\n{df[FEATURE_COLS].describe().round(2)}")

    # Correlation heatmap
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(df[FEATURE_COLS].corr(), annot=True, fmt=".2f",
                cmap="RdYlGn", ax=ax, linewidths=0.5)
    ax.set_title("Feature Correlation Matrix")
    plt.tight_layout()
    plt.savefig(f"{ARTIFACT_DIR}/eda_correlation.png", dpi=100)
    plt.close()

    # Feature distributions
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    axes = axes.flatten()
    for i, col in enumerate(FEATURE_COLS):
        axes[i].hist(df[col], bins=40, color="#22c55e", edgecolor="white", alpha=0.8)
        axes[i].set_title(col)
        axes[i].set_xlabel("Value")
        axes[i].set_ylabel("Frequency")
    axes[-1].axis("off")
    plt.suptitle("Feature Distributions", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(f"{ARTIFACT_DIR}/eda_distributions.png", dpi=100)
    plt.close()

    # Box plots: feature by crop (top 10 crops for readability)
    top_crops = df[TARGET_COL].value_counts().head(10).index
    df_top = df[df[TARGET_COL].isin(top_crops)]
    fig, axes = plt.subplots(2, 4, figsize=(18, 10))
    axes = axes.flatten()
    for i, col in enumerate(FEATURE_COLS):
        df_top.boxplot(column=col, by=TARGET_COL, ax=axes[i], rot=45)
        axes[i].set_title(f"{col} by Crop")
        axes[i].set_xlabel("")
    axes[-1].axis("off")
    plt.suptitle("Feature Ranges per Crop (Top 10)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(f"{ARTIFACT_DIR}/eda_boxplots.png", dpi=100)
    plt.close()

    print(f"\n[EDA] Plots saved to {ARTIFACT_DIR}/eda_*.png")

    # Outlier detection with IQR
    print("\nOutlier counts (IQR method):")
    for col in FEATURE_COLS:
        Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        IQR = Q3 - Q1
        outliers = ((df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)).sum()
        print(f"  {col:20s}: {outliers} outliers")


# ─── 3. Preprocess ────────────────────────────────────────────────────────────
def preprocess(df: pd.DataFrame):
    # Drop duplicates
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"\n[PREP] After dedup: {df.shape[0]} rows")

    X = df[FEATURE_COLS]
    y = df[TARGET_COL]

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, random_state=RANDOM_STATE, stratify=y_enc
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    print(f"[PREP] Train: {X_train_s.shape} | Test: {X_test_s.shape}")
    print(f"[PREP] Classes: {len(le.classes_)} → {list(le.classes_[:5])}...")
    return X_train_s, X_test_s, y_train, y_test, scaler, le, X.columns.tolist()


# ─── 4. Train & Compare Multiple Models ──────────────────────────────────────
def compare_models(X_train, X_test, y_train, y_test, feature_names):
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    candidates = {
        "Random Forest": RandomForestClassifier(
            n_estimators=200, max_depth=None,
            min_samples_leaf=2, random_state=RANDOM_STATE, n_jobs=-1
        ),
        "XGBoost": xgb.XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            use_label_encoder=False, eval_metric="mlogloss",
            random_state=RANDOM_STATE, n_jobs=-1
        ),
        "KNN (k=5)": KNeighborsClassifier(n_neighbors=5, metric="euclidean", n_jobs=-1),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.1,
            random_state=RANDOM_STATE
        ),
    }

    print("\n" + "="*60)
    print("MODEL COMPARISON (5-Fold Stratified CV)")
    print("="*60)
    results = {}
    for name, clf in candidates.items():
        cv_scores = cross_val_score(clf, X_train, y_train, cv=cv,
                                    scoring="accuracy", n_jobs=-1)
        print(f"  {name:25s}: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        results[name] = (cv_scores.mean(), cv_scores.std(), clf)

    best_name = max(results, key=lambda k: results[k][0])
    print(f"\n[BEST] {best_name} selected (CV acc: {results[best_name][0]:.4f})")
    return results[best_name][2], best_name, results


# ─── 5. Hyperparameter Tuning (XGBoost) ──────────────────────────────────────
def tune_xgboost(X_train, y_train):
    print("\n[TUNE] Hyperparameter search for XGBoost...")
    param_grid = {
        "n_estimators":     [150, 200, 300],
        "max_depth":        [4, 6, 8],
        "learning_rate":    [0.05, 0.1, 0.15],
        "subsample":        [0.8, 1.0],
        "colsample_bytree": [0.8, 1.0],
    }
    base = xgb.XGBClassifier(
        use_label_encoder=False, eval_metric="mlogloss",
        random_state=RANDOM_STATE, n_jobs=-1
    )
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
    search = GridSearchCV(base, param_grid, cv=cv, scoring="accuracy",
                          n_jobs=-1, verbose=1, refit=True)
    search.fit(X_train, y_train)
    print(f"[TUNE] Best params : {search.best_params_}")
    print(f"[TUNE] Best CV acc : {search.best_score_:.4f}")
    return search.best_estimator_, search.best_params_


# ─── 6. Evaluate Best Model ───────────────────────────────────────────────────
def evaluate(model, X_test, y_test, le, model_name):
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n[EVAL] {model_name}")
    print(f"  Test Accuracy  : {acc:.4f} ({acc*100:.2f}%)")
    print(f"\nClassification Report:\n"
          f"{classification_report(y_test, y_pred, target_names=le.classes_)}")

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(14, 12))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=le.classes_)
    disp.plot(ax=ax, xticks_rotation=45, colorbar=False)
    ax.set_title(f"Confusion Matrix — {model_name}", fontsize=13)
    plt.tight_layout()
    plt.savefig(f"{ARTIFACT_DIR}/confusion_matrix.png", dpi=100)
    plt.close()
    print(f"[EVAL] Confusion matrix saved.")
    return acc


# ─── 7. SHAP Feature Importance ──────────────────────────────────────────────
def compute_shap(model, X_test, feature_names):
    print("\n[SHAP] Computing SHAP feature importance...")
    try:
        explainer = shap.TreeExplainer(model)
        shap_vals = explainer.shap_values(X_test[:200])
        # Multi-class: mean absolute SHAP across all classes
        if isinstance(shap_vals, list):
            mean_abs = np.mean([np.abs(sv).mean(axis=0) for sv in shap_vals], axis=0)
        else:
            mean_abs = np.abs(shap_vals).mean(axis=0)
        importance = {feature_names[i]: float(mean_abs[i]) for i in range(len(feature_names))}
        # Normalize
        total = sum(importance.values())
        importance = {k: round(v / total, 4) for k, v in
                      sorted(importance.items(), key=lambda x: x[1], reverse=True)}
        print(f"[SHAP] Feature importance: {importance}")

        # Bar chart
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.barh(list(importance.keys()), list(importance.values()),
                color="#22c55e", edgecolor="white")
        ax.set_title("SHAP Feature Importance (Crop Recommendation)")
        ax.set_xlabel("Mean |SHAP|")
        plt.tight_layout()
        plt.savefig(f"{ARTIFACT_DIR}/shap_importance.png", dpi=100)
        plt.close()
        return importance
    except Exception as e:
        print(f"[SHAP] Warning: {e}")
        # Fallback to built-in feature importance
        fi = model.feature_importances_
        total = fi.sum()
        return {feature_names[i]: round(float(fi[i] / total), 4)
                for i in np.argsort(fi)[::-1]}


# ─── 8. Save Artifacts ───────────────────────────────────────────────────────
def save_artifacts(model, scaler, le, metrics):
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    joblib.dump(model,  f"{ARTIFACT_DIR}/crop_model.pkl")
    joblib.dump(scaler, f"{ARTIFACT_DIR}/crop_scaler.pkl")
    joblib.dump(le,     f"{ARTIFACT_DIR}/crop_label_encoder.pkl")
    with open(f"{ARTIFACT_DIR}/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n[SAVE] Artifacts saved to {ARTIFACT_DIR}/")

    try:
        s3 = boto3.client("s3", region_name=AWS_REGION)
        prefix = f"models/crop-recommendation/{metrics['model_version']}"
        for fname in ["crop_model.pkl", "crop_scaler.pkl",
                      "crop_label_encoder.pkl", "metrics.json"]:
            s3.upload_file(f"{ARTIFACT_DIR}/{fname}", S3_BUCKET,
                           f"{prefix}/{fname}")
        print(f"[S3]  Uploaded to s3://{S3_BUCKET}/{prefix}/")
    except Exception as e:
        print(f"[S3]  Upload skipped: {e}")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("="*60)
    print("AgroPulse AI — Crop Recommendation Model Training")
    print("Dataset: Kaggle — atharvaingle/crop-recommendation-dataset")
    print("="*60)

    df = load_data()
    run_eda(df)

    X_train, X_test, y_train, y_test, scaler, le, feat_names = preprocess(df)

    # Compare all models first
    _, best_name, all_results = compare_models(
        X_train, X_test, y_train, y_test, feat_names
    )

    # Always tune XGBoost (consistently best on this dataset ~98-99%)
    best_model, best_params = tune_xgboost(X_train, y_train)

    test_acc = evaluate(best_model, X_test, y_test, le, "XGBoost (tuned)")
    feature_importance = compute_shap(best_model, X_test, feat_names)

    metrics = {
        "model_version":    "xgboost-real-v2",
        "dataset":          "atharvaingle/crop-recommendation-dataset",
        "n_samples":        len(X_train) + len(X_test),
        "test_accuracy":    round(float(test_acc), 4),
        "num_classes":      int(len(le.classes_)),
        "classes":          list(le.classes_),
        "best_params":      best_params,
        "feature_importance": feature_importance,
        "model_comparison": {
            name: {"cv_mean": round(float(r[0]), 4), "cv_std": round(float(r[1]), 4)}
            for name, r in all_results.items()
        },
    }

    save_artifacts(best_model, scaler, le, metrics)

    print("\n" + "="*60)
    print(f"Training Complete!")
    print(f"Model       : XGBoost (tuned)")
    print(f"Test Acc    : {test_acc*100:.2f}%")
    print(f"Classes     : {len(le.classes_)} crops")
    print(f"Top factor  : {list(feature_importance.keys())[0]} "
          f"({list(feature_importance.values())[0]*100:.1f}%)")
    print("="*60)


if __name__ == "__main__":
    main()
