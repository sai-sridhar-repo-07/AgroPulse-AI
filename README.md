# AgroPulse AI 🌾
## Hyper-local, Explainable AI Decision Intelligence Platform for Rural Farmers

[![CI/CD](https://github.com/your-org/agropulse-ai/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/your-org/agropulse-ai/actions)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18-blue)](https://react.dev)
[![AWS](https://img.shields.io/badge/AWS-Cloud--Native-orange)](https://aws.amazon.com)

---

## 🎯 Problem Statement

**700+ million** Indian farmers make critical decisions — what to plant, when to sell, when to worry — based on incomplete information or outdated advice. The consequences:

- **₹1.5 lakh crore** in annual crop losses due to poor decisions
- Farmers sell during price dips and hold during peaks
- No access to personalized, location-specific recommendations
- Traditional advisory systems give generic advice, not hyper-local insights

---

## 💡 Solution: AgroPulse AI

A **cloud-native, production-ready AI platform** that delivers:

| Feature | Technology | Output |
|---------|-----------|--------|
| Crop Recommendation | XGBoost + SageMaker | Top 3 crops + confidence |
| Yield Prediction | Gradient Boosting | kg/hectare forecast |
| Price Forecasting | Prophet + mandi data | 7-30 day price forecast |
| Risk Detection | Isolation Forest | Risk probability score |
| AI Explanation | Amazon Bedrock (Claude) | Farmer-friendly narrative |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AGROPULSE AI ARCHITECTURE                    │
│                            AWS Cloud (ap-south-1)                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  👨‍🌾 Farmer (Mobile)                                                  │
│        │                                                              │
│        ▼                                                              │
│  ┌──────────────┐          ┌─────────────────────────────────┐       │
│  │  AWS Amplify │◄────────►│      Amazon CloudFront (CDN)    │       │
│  │  React App   │          │      SSL/TLS Termination        │       │
│  │  (Frontend)  │          └─────────────────────────────────┘       │
│  └──────┬───────┘                                                     │
│         │ HTTPS                                                        │
│         ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │              Amazon API Gateway (REST)                           │  │
│  │              JWT Auth via Cognito Authorizer                     │  │
│  │              Rate Limiting: 500 req/hr per IP                    │  │
│  └────────────────────────┬────────────────────────────────────────┘  │
│                            │                                           │
│         ┌──────────────────┼──────────────────────┐                   │
│         │                  │                       │                   │
│         ▼                  ▼                       ▼                   │
│  ┌─────────────┐  ┌───────────────┐     ┌─────────────────┐          │
│  │ Auth Lambda │  │  ECS Fargate  │     │  AWS Lambda     │          │
│  │  (Cognito)  │  │  FastAPI App  │     │  (ETL Trigger)  │          │
│  │             │  │  2 Tasks      │     │                 │          │
│  └─────────────┘  └───────┬───────┘     └────────┬────────┘          │
│                            │                      │                   │
│         ┌──────────────────┼──────────────────────┤                   │
│         │                  │                       │                   │
│         ▼                  ▼                       ▼                   │
│  ┌─────────────┐  ┌─────────────┐       ┌─────────────────────────┐  │
│  │  Amazon     │  │  Amazon RDS │       │    Amazon SageMaker      │  │
│  │  Cognito    │  │  PostgreSQL │       │    Endpoints (4 Models)  │  │
│  │  User Pool  │  │  (Private)  │       │  • Crop Recommendation   │  │
│  └─────────────┘  └─────────────┘       │  • Yield Prediction     │  │
│                                          │  • Price Forecast        │  │
│  ┌─────────────┐  ┌─────────────┐       │  • Risk Detection        │  │
│  │  Amazon     │  │  Amazon S3  │       └─────────────────────────┘  │
│  │  DynamoDB   │  │  Data Lake  │                                     │
│  │  (Sessions) │  │  (3 buckets)│       ┌─────────────────────────┐  │
│  └─────────────┘  └─────────────┘       │    Amazon Bedrock        │  │
│                                          │    Claude Sonnet         │  │
│  ┌─────────────────────────────────────┐│    GenAI Explanations    │  │
│  │  Amazon CloudWatch + X-Ray          ││    (6 Indian languages)  │  │
│  │  Logs, Metrics, Alarms, Tracing     │└─────────────────────────┘  │
│  └─────────────────────────────────────┘                              │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │              Data Pipeline (EventBridge → Lambda)                │  │
│  │  OpenWeatherMap ──► S3 (raw) ──► PostgreSQL (normalized)        │  │
│  │  AGMARKNET      ──► S3 (raw) ──► PostgreSQL (normalized)        │  │
│  │  Soil Health Card──► S3 (raw) ──► SageMaker (training)          │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
agropulse-ai/
├── backend/                        # FastAPI Python Backend
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Pydantic settings management
│   │   ├── database.py             # PostgreSQL + DynamoDB + S3 clients
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── farmer.py           # Farmer profile
│   │   │   ├── prediction.py       # ML predictions store
│   │   │   ├── alert.py            # Risk alerts
│   │   │   ├── weather.py          # Weather records
│   │   │   └── market.py           # Mandi prices
│   │   ├── routers/                # FastAPI route handlers
│   │   │   ├── auth.py             # POST /auth/login
│   │   │   ├── crop.py             # POST /predict/crop
│   │   │   ├── yield_pred.py       # POST /predict/yield
│   │   │   ├── price.py            # POST /predict/price
│   │   │   ├── alerts.py           # GET /alerts/{farmer_id}
│   │   │   ├── explanation.py      # POST /generate-explanation
│   │   │   └── health.py           # GET /health
│   │   ├── schemas/                # Pydantic input/output models
│   │   ├── services/               # Business logic layer
│   │   │   ├── auth_service.py     # Amazon Cognito integration
│   │   │   ├── bedrock_service.py  # Amazon Bedrock (GenAI)
│   │   │   ├── sagemaker_service.py# SageMaker endpoint invocations
│   │   │   ├── price_service.py    # Price forecasting logic
│   │   │   └── weather_service.py  # OpenWeatherMap integration
│   │   └── middleware/             # Auth + logging middleware
│   ├── ml/                         # Machine Learning Models
│   │   ├── crop_recommendation/    # XGBoost crop classifier
│   │   ├── yield_prediction/       # Gradient Boosting regressor
│   │   ├── price_forecasting/      # Facebook Prophet time-series
│   │   └── risk_detection/         # Isolation Forest anomaly detection
│   ├── etl/                        # Data Pipeline Scripts
│   │   ├── weather_ingestion.py    # OpenWeatherMap → S3 → RDS
│   │   ├── market_data_ingestion.py# AGMARKNET → S3 → RDS
│   │   └── soil_data_ingestion.py  # SHC → S3
│   ├── lambda/                     # AWS Lambda functions
│   │   └── etl_trigger.py          # EventBridge orchestrator
│   ├── scripts/
│   │   └── init_db.sql             # Database initialization
│   ├── Dockerfile                  # Production Docker image
│   ├── docker-compose.yml          # Local dev stack
│   └── requirements.txt            # Python dependencies
│
├── frontend/                       # React TypeScript Frontend
│   ├── src/
│   │   ├── App.tsx                 # Root component + routing
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx       # Cognito login
│   │   │   ├── FarmerInputForm.tsx # 3-step input form
│   │   │   └── Dashboard.tsx       # Main dashboard
│   │   ├── components/dashboard/
│   │   │   ├── CropRecommendationCard.tsx
│   │   │   ├── YieldChart.tsx      # Chart.js bar chart
│   │   │   ├── PriceForecastChart.tsx # Line chart with confidence bands
│   │   │   ├── RiskAlertBanner.tsx # Color-coded alerts
│   │   │   └── ExplanationPanel.tsx # Bedrock AI explanation
│   │   ├── services/api.ts         # Axios API client + auth interceptors
│   │   ├── types/index.ts          # TypeScript type definitions
│   │   └── styles/index.css        # Tailwind + custom styles
│   ├── public/index.html
│   ├── package.json
│   └── tailwind.config.js
│
├── infrastructure/                 # AWS Infrastructure as Code
│   └── terraform/
│       ├── main.tf                 # VPC, ECS, RDS, S3, Cognito, DynamoDB
│       └── iam.tf                  # IAM roles (least privilege)
│
├── .github/
│   └── workflows/
│       └── ci-cd.yml               # GitHub Actions pipeline
│
└── README.md
```

---

## 🤖 Why AI is Required

### Problem with Traditional Systems
Static rule-based advisory systems (e.g., government Kisan Call Centers) provide:
- Generic crop calendars — not location-specific
- No soil data analysis
- No market price integration
- No risk prediction

### Why AgroPulse AI is Different

| Aspect | Traditional | AgroPulse AI |
|--------|-------------|-------------|
| Recommendation | Generic for district | Personalized for individual farm |
| Data sources | Seasonal guides | Real-time weather + live mandi prices + soil health card |
| Explanation | None | Bedrock GenAI in 6 languages |
| Risk alerts | None | Isolation Forest anomaly detection |
| Market timing | None | Prophet price forecast + BUY/SELL signal |

### Why AWS is Used
- **SageMaker**: Managed ML training + inference at scale
- **Bedrock**: Production-grade GenAI without infrastructure management
- **ECS Fargate**: Serverless containers — no VM management
- **RDS Multi-AZ**: 99.95% availability for production databases
- **Cognito**: Enterprise-grade auth for 100M+ users
- **EventBridge + Lambda**: Zero-cost event-driven ETL pipeline
- **CloudWatch**: Full-stack observability out of the box

---

## 🧠 How Amazon Bedrock Adds Value

```
ML Output (numbers):
  {"top_crop": "rice", "confidence": 0.87}

                    ↓ Amazon Bedrock (Claude)

Human-readable explanation (farmer-friendly):
  "Based on your soil's high nitrogen content (90 kg/ha) and
   the expected 800mm rainfall in Pune district, our AI strongly
   recommends cultivating Rice this Kharif season. Rice thrives
   at your soil pH of 6.5, and the confidence level of 87% means
   the conditions closely match successful rice farming patterns
   in your region..."

Action steps:
  1. Prepare nursery beds by May-June
  2. Ensure drainage before monsoon
  3. Apply Zinc Sulphate 25 kg/ha
```

**Bedrock adds:**
- Explainability → Trust → Adoption by rural farmers
- Regional language output (Hindi, Marathi, Telugu, Kannada, Tamil)
- Contextual farming advice beyond raw predictions
- Risk mitigation steps automatically generated

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker + Docker Compose
- AWS CLI configured (`aws configure`)

### 1. Clone and Setup
```bash
git clone https://github.com/your-org/agropulse-ai.git
cd agropulse-ai
```

### 2. Backend (Local Development)
```bash
cd backend

# Create .env file
cat > .env << EOF
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=postgresql+asyncpg://agropulse:password@localhost:5432/agropulse
AWS_REGION=ap-south-1
OPENWEATHER_API_KEY=your_key_here
COGNITO_USER_POOL_ID=ap-south-1_XXXXXXXX
COGNITO_CLIENT_ID=your_client_id
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
EOF

# Start with Docker Compose (includes PostgreSQL + LocalStack)
docker compose up -d

# OR run locally
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend (Local Development)
```bash
cd frontend
cp .env.example .env.local
# Set REACT_APP_API_BASE_URL=http://localhost:8000
npm install
npm start
```

### 4. Train ML Models
```bash
cd backend

# Train all 4 models locally
python ml/crop_recommendation/train.py
python ml/yield_prediction/train.py
python ml/price_forecasting/train.py
python ml/risk_detection/train.py
```

### 5. Access the App
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- pgAdmin: http://localhost:5050

---

## 🔌 API Reference

### Authentication
```http
POST /auth/login
Content-Type: application/json

{
  "username": "farmer@example.com",
  "password": "SecurePass123!"
}
```

### Crop Recommendation
```http
POST /predict/crop
Authorization: Bearer <access_token>

{
  "soil": {"nitrogen": 90, "phosphorus": 42, "potassium": 43, "ph": 6.5},
  "location": {"state": "Maharashtra", "district": "Pune"},
  "rainfall_mm": 800,
  "temperature_celsius": 25,
  "humidity_percent": 65
}
```

### Yield Prediction
```http
POST /predict/yield
Authorization: Bearer <access_token>

{
  "crop": "rice",
  "area_hectares": 2.5,
  "soil_nitrogen": 90,
  "soil_ph": 6.5,
  "weather_forecast": {"temperature_celsius": 28, "rainfall_mm": 120, "humidity_percent": 75},
  "irrigation": true
}
```

### Price Forecast
```http
POST /predict/price
Authorization: Bearer <access_token>

{
  "commodity": "Wheat",
  "state": "Punjab",
  "forecast_days": 14
}
```

### AI Explanation (Bedrock)
```http
POST /generate-explanation
Authorization: Bearer <access_token>

{
  "prediction_type": "crop_recommendation",
  "prediction_output": {"top_crop": "rice", "confidence": 0.87},
  "feature_importance": {"nitrogen": 0.35, "rainfall": 0.28},
  "confidence_score": 0.87,
  "farmer_context": {"name": "Ramesh", "district": "Pune"},
  "language": "hi"
}
```

---

## 🚢 Production Deployment

### Step 1: AWS Infrastructure
```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var="db_password=YourSecurePassword123!"

# Apply (creates all AWS resources)
terraform apply -var="db_password=YourSecurePassword123!"
```

### Step 2: Build & Push Docker Image
```bash
cd backend

# Get ECR login token
aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS \
  --password-stdin <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com

# Build and push
docker build -t agropulse-backend .
docker tag agropulse-backend:latest \
  <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/agropulse-backend:latest
docker push <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/agropulse-backend:latest
```

### Step 3: Deploy Frontend to Amplify
```bash
# Via AWS Console: Connect GitHub repo to Amplify
# Or via CLI:
aws amplify create-app --name agropulse-frontend
aws amplify create-branch --app-id <APP_ID> --branch-name main
aws amplify start-job --app-id <APP_ID> --branch-name main --job-type RELEASE
```

### Step 4: Train & Deploy SageMaker Models
```bash
cd backend/ml/crop_recommendation
python sagemaker_train.py \
  --bucket agropulse-model-artifacts \
  --region ap-south-1 \
  --role-arn arn:aws:iam::<ACCOUNT>:role/agropulse-sagemaker-role \
  --deploy
```

### Step 5: Setup EventBridge ETL Schedule
```bash
# Daily weather + market data ingestion
aws events put-rule \
  --name agropulse-etl-daily \
  --schedule-expression "cron(0 2 * * ? *)" \
  --state ENABLED

aws events put-targets \
  --rule agropulse-etl-daily \
  --targets "Id=ETLLambda,Arn=arn:aws:lambda:ap-south-1:<ACCOUNT>:function:agropulse-etl-trigger"
```

---

## 💰 AWS Cost Estimation

| Service | Configuration | Est. Monthly Cost |
|---------|--------------|------------------|
| ECS Fargate | 2 tasks × 0.5 vCPU × 1GB | ~₹2,500 |
| RDS PostgreSQL | db.t3.small, Multi-AZ, 20GB | ~₹4,500 |
| SageMaker | 4 endpoints × ml.t2.medium | ~₹8,000 |
| Bedrock Claude | 1M tokens/month | ~₹1,500 |
| API Gateway | 1M requests/month | ~₹350 |
| Lambda | 100K invocations/month | ~₹50 |
| S3 (3 buckets) | 50GB storage | ~₹150 |
| Cognito | 1,000 MAU | Free tier |
| CloudWatch | Logs + Alarms | ~₹200 |
| ALB | Application Load Balancer | ~₹800 |
| NAT Gateway | 1 per AZ | ~₹800 |
| **Total** | | **~₹18,850/month** |

> **Cost Optimization**: Use FARGATE_SPOT for 70% discount on ECS. SageMaker endpoints can be stopped between requests using auto-scaling to zero.

---

## 📊 ER Diagram

```
farmers
  ├── id (UUID, PK)
  ├── cognito_sub (VARCHAR, UNIQUE)
  ├── name, phone, state, district
  ├── land_area_hectares
  └── preferred_language

predictions
  ├── id (UUID, PK)
  ├── farmer_id (FK → farmers.id)
  ├── prediction_type (ENUM)
  ├── input_data (JSONB)
  ├── output_data (JSONB)
  ├── confidence_score
  ├── model_version
  └── explanation

alerts
  ├── id (UUID, PK)
  ├── farmer_id (FK → farmers.id)
  ├── alert_type, severity
  ├── title, message
  ├── risk_score
  └── is_read

weather_records
  ├── id (UUID, PK)
  ├── district, state
  ├── latitude, longitude
  ├── temperature_celsius, humidity_percent
  ├── rainfall_mm, wind_speed_kmh
  └── recorded_at

market_prices
  ├── id (UUID, PK)
  ├── commodity, state, district, market
  ├── min_price, max_price, modal_price
  ├── unit ("Quintal")
  └── price_date
```

---

## 🔒 Security Best Practices

1. **No hardcoded credentials** — All secrets in AWS Secrets Manager
2. **IAM least privilege** — Each component has minimal required permissions
3. **HTTPS everywhere** — TLS 1.3 at ALB + CloudFront
4. **Private subnets** — RDS accessible only from ECS security group
5. **Cognito JWT** — RS256 token validation, 1-hour expiry
6. **Input validation** — Pydantic validation on all API inputs
7. **Rate limiting** — SlowAPI: 60/min per IP, 500/hr per user
8. **Container security** — Non-root user, minimal base image
9. **ECR scanning** — Vulnerability scan on every push
10. **VPC isolation** — No public access to databases

---

## 🌏 Impact on Rural India

- **Target users**: 140 million+ small and marginal farmers (< 2 hectares)
- **Languages**: English, Hindi, Marathi, Telugu, Kannada, Tamil
- **Mobile-first**: PWA-ready, works on 2G networks
- **Offline mode**: Core data cached locally (coming soon)
- **Government integration**: Soil Health Card API, AGMARKNET data

### Expected Outcomes
| Metric | Baseline | With AgroPulse AI |
|--------|----------|------------------|
| Crop selection accuracy | 60% | 87%+ |
| Market timing decisions | Random | Data-driven (14-day forecast) |
| Risk preparedness | 20% | 75%+ |
| Income per farmer | Baseline | +15-20% estimated |

---

## 🔮 Future Roadmap

### Phase 2 (3 months)
- [ ] WhatsApp Bot integration (Twilio + Bedrock)
- [ ] SMS alerts for non-smartphone farmers
- [ ] NDVI satellite imagery integration (AWS Earth Observation)
- [ ] Crop disease detection (AWS Rekognition)

### Phase 3 (6 months)
- [ ] Offline PWA with local model inference
- [ ] Government scheme matcher (PM-KISAN, Fasal Bima)
- [ ] FPO (Farmer Producer Organization) dashboard
- [ ] Drone data integration (precision agriculture)

### Phase 4 (12 months)
- [ ] Pan-India expansion (all 28 states)
- [ ] Agri-fintech integration (crop loans based on AI yield prediction)
- [ ] International expansion (Bangladesh, Nepal, Sri Lanka)

---

## 🏆 Hackathon Evaluation Alignment

| Criterion | Our Solution |
|-----------|-------------|
| **AI Usage** | 4 ML models + Amazon Bedrock GenAI |
| **AWS Services** | 12+ AWS services integrated |
| **Scalability** | Auto-scaling ECS + Serverless Lambda |
| **Generative AI** | Bedrock Claude for XAI explanations |
| **Real-world Impact** | 140M+ farmers, 6 languages |
| **Technical Depth** | End-to-end: ETL → ML → GenAI → API → UI |
| **Production Ready** | Docker + CI/CD + Terraform + Monitoring |

---

## 📹 Demo Script (5-7 Minutes)

**[0:00-0:30]** Introduction
> "AgroPulse AI solves the $20 billion problem of uninformed farming decisions in India..."

**[0:30-1:30]** Architecture Overview
> "Built on 12+ AWS services: SageMaker for ML, Bedrock for GenAI, ECS Fargate for API..."

**[1:30-3:00]** Live Demo
1. Login as farmer "Ramesh Kumar" from Pune
2. Enter soil NPK values from Soil Health Card
3. Submit 3-step form

**[3:00-4:30]** Dashboard Walkthrough
1. Crop Recommendation: "Rice — 87% confidence"
2. Yield Chart: "4,350 kg/hectare predicted"
3. Price Forecast: "Rice prices rising — SELL signal"
4. Risk Alert: "Heavy rainfall expected in 72 hours"
5. **AI Explanation (Bedrock)**: "Based on your soil nitrogen..."

**[4:30-5:30]** Technical Deep Dive
- SageMaker endpoint invocation
- Bedrock prompt template
- ETL pipeline architecture

**[5:30-6:00]** Impact + Roadmap
> "15-20% income increase for participating farmers..."

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Follow conventional commits: `feat: add WhatsApp integration`
4. Open PR against `develop` branch

---

## 📜 License

MIT License — See [LICENSE](LICENSE)

---

## 🏗 Built By

**AgroPulse AI Team**
- Architecture: AWS cloud-native microservices
- AI/ML: XGBoost, Gradient Boosting, Prophet, Isolation Forest
- GenAI: Amazon Bedrock Claude Sonnet
- Stack: FastAPI + React + PostgreSQL + Docker + Terraform

---

*Powered by AWS — Built for Bharat 🇮🇳*
