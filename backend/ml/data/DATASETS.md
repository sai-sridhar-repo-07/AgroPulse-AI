# AgroPulse AI — Real Dataset Download Instructions

All 4 ML models use real publicly available datasets. Download each before running training scripts.

---

## Setup: Install Kaggle API

```bash
pip install kaggle
# Place your kaggle.json at ~/.kaggle/kaggle.json
# Get it from: https://www.kaggle.com/settings → API → Create New Token
chmod 600 ~/.kaggle/kaggle.json
```

---

## Dataset 1 — Crop Recommendation
**File:** `data/Crop_recommendation.csv`
**Rows:** 2,200 | **Features:** N, P, K, temperature, humidity, ph, rainfall, label (22 crops)
**Source:** Real hand-collected data by Indian Chamber of Food and Agriculture

```bash
kaggle datasets download -d atharvaingle/crop-recommendation-dataset -p backend/ml/data/ --unzip
```
Direct link: https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset

---

## Dataset 2 — Yield Prediction
**File:** `data/crop_production.csv`
**Rows:** ~246,000 | **Features:** State, District, Crop_Year, Season, Crop, Area, Production
**Source:** Ministry of Agriculture India (1997–2015, 33 states, 124 crops)

```bash
kaggle datasets download -d abhinand05/crop-production-in-india -p backend/ml/data/ --unzip
```
Direct link: https://www.kaggle.com/datasets/abhinand05/crop-production-in-india

---

## Dataset 3 — Price Forecasting
**File:** `data/mandi_prices.csv`
**Rows:** 1M+ | **Features:** date, commodity, state, district, market, modal_price, min_price, max_price
**Source:** AGMARKNET (Ministry of Agriculture real mandi data 2023–2025)

```bash
kaggle datasets download -d arjunyadav99/indian-agricultural-mandi-prices-20232025 -p backend/ml/data/ --unzip
# Rename to mandi_prices.csv
```
Direct link: https://www.kaggle.com/datasets/arjunyadav99/indian-agricultural-mandi-prices-20232025

Alternative (more commodities):
```bash
kaggle datasets download -d anshtanwar/current-daily-price-of-various-commodities-india -p backend/ml/data/ --unzip
```

---

## Dataset 4 — Risk Detection
**Files:**
- `data/rainfall_india.csv` — District-level monthly rainfall (IMD 1901–2015)
- `data/flood_risk_india.csv` — Flood risk by district

```bash
# Rainfall data (IMD)
kaggle datasets download -d rajanand/rainfall-in-india -p backend/ml/data/ --unzip

# Flood risk
kaggle datasets download -d s3programmer/flood-risk-in-india -p backend/ml/data/ --unzip
```

Direct links:
- https://www.kaggle.com/datasets/rajanand/rainfall-in-india
- https://www.kaggle.com/datasets/s3programmer/flood-risk-in-india

---

## Quick Download All (run from project root)

```bash
cd "backend/ml/data"
kaggle datasets download -d atharvaingle/crop-recommendation-dataset --unzip
kaggle datasets download -d abhinand05/crop-production-in-india --unzip
kaggle datasets download -d arjunyadav99/indian-agricultural-mandi-prices-20232025 --unzip
kaggle datasets download -d rajanand/rainfall-in-india --unzip
kaggle datasets download -d s3programmer/flood-risk-in-india --unzip
```

---

## Expected Files After Download

```
backend/ml/data/
├── Crop_recommendation.csv        # 2,200 rows
├── crop_production.csv            # ~246,000 rows (or APY_Output.csv)
├── mandi_prices.csv               # 1M+ rows
├── rainfall_india.csv             # District rainfall
└── flood_risk_india.csv           # Flood risk by district
```
