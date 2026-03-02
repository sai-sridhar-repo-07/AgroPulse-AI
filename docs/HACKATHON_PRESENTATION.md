# AgroPulse AI - Hackathon Presentation Outline
## PPT Slide Content & Demo Script

---

## SLIDE 1: Title Slide

**AgroPulse AI**
*Hyper-local, Explainable AI Decision Intelligence for Rural Farmers*

Powered by: AWS SageMaker | Amazon Bedrock | ECS Fargate

---

## SLIDE 2: The Problem

### 700 Million Farmers. Zero AI Support.

**Pain Points:**
- ❌ No personalized crop advice
- ❌ No market timing guidance (buy/sell signals)
- ❌ No early risk warnings (drought, flood, pest)
- ❌ Government advisories are generic, not farm-specific

**Impact:**
- ₹1.5 lakh crore in annual crop losses
- 40% of farm income lost to wrong market timing
- 60% farmers can't read government bulletins

---

## SLIDE 3: The Solution

### AgroPulse AI: Your Pocket Farm Advisor

**3-Step Process:**
1. 📱 Enter soil + location data (30 seconds)
2. 🤖 AI analyzes 7+ parameters in real-time
3. 💡 Get personalized advice in your language

**What you get:**
- 🌾 Top 3 crops to grow (with confidence %)
- 📊 Expected yield (kg/hectare)
- 💰 14-day price forecast + BUY/SELL signal
- ⚠️ Risk alerts (drought, flood, pest)
- 🗣️ Bedrock AI explanation in Hindi/Marathi/Telugu

---

## SLIDE 4: Architecture

```
Farmer (Mobile) → AWS Amplify (React)
              → API Gateway → ECS Fargate (FastAPI)
                         ├── Amazon SageMaker (4 ML Models)
                         ├── Amazon Bedrock (Explanation AI)
                         ├── Amazon Cognito (Auth)
                         ├── RDS PostgreSQL (Data)
                         ├── DynamoDB (Sessions)
                         └── S3 (Data Lake)

EventBridge → Lambda → ETL Pipelines:
  • OpenWeatherMap → S3 → RDS
  • AGMARKNET Mandi → S3 → RDS
  • Soil Health Card → S3 → SageMaker
```

---

## SLIDE 5: 4 AI Models

| Model | Algorithm | Input | Output |
|-------|-----------|-------|--------|
| Crop Recommendation | XGBoost | NPK, pH, rainfall, temp | Top 3 crops + confidence |
| Yield Prediction | Gradient Boosting | Soil + weather + area | kg/hectare + CI |
| Price Forecasting | Prophet | Historical mandi prices | 14-30 day forecast |
| Risk Detection | Isolation Forest | Weather anomalies, NDVI | Risk probability score |

**All deployed on Amazon SageMaker with auto-scaling endpoints**

---

## SLIDE 6: Amazon Bedrock (GenAI Magic)

### Why Bedrock is the Core Differentiator

**Input:**
```json
{"top_crop": "rice", "confidence": 0.87,
 "nitrogen_importance": 0.35}
```

**Output (Bedrock Claude Sonnet):**
> *"Based on your soil's high nitrogen content of 90 kg/ha
> and the 800mm annual rainfall in Pune district, Rice is
> the ideal crop for this Kharif season. The AI is 87%
> confident because your soil conditions match 94% of
> successful rice farms in Maharashtra..."*
>
> **Action Steps:**
> 1. Prepare nursery beds by June 15th
> 2. Ensure drainage channels before monsoon
> 3. Apply Zinc Sulphate (25 kg/ha)

**Supports 6 languages: en/hi/mr/te/kn/ta**

---

## SLIDE 7: AWS Services & Justification

| AWS Service | Why Used | Alternative |
|-------------|----------|-------------|
| **Bedrock** | Managed GenAI, no infra | Self-hosted LLM (10x cost) |
| **SageMaker** | Scalable ML endpoints | EC2 GPU (ops overhead) |
| **ECS Fargate** | Serverless containers | Kubernetes (complex) |
| **Cognito** | Enterprise auth for 100M+ | Custom JWT (security risk) |
| **RDS Multi-AZ** | 99.95% uptime | Single EC2 (no HA) |
| **EventBridge** | Zero-cost scheduling | Cron on EC2 (wasteful) |
| **CloudWatch** | Native observability | Datadog ($$$) |

---

## SLIDE 8: Data Pipeline

```
SOURCES              PROCESSING           STORAGE
─────────            ──────────           ───────

OpenWeatherMap  →    Lambda ETL      →    S3 (raw JSON)
API (real-time)      Normalize            RDS (normalized)
                     Validate

AGMARKNET       →    Lambda ETL      →    S3 (raw CSV)
(daily prices)       Clean                RDS (structured)
                     Aggregate

Soil Health     →    Lambda ETL      →    S3 (partitioned)
Card (monthly)       Feature eng.         SageMaker (training)

                ↑
    EventBridge triggers daily at 2 AM IST
```

---

## SLIDE 9: Security & Compliance

✅ **No hardcoded credentials** — AWS Secrets Manager

✅ **IAM least privilege** — Each service has minimal permissions

✅ **HTTPS everywhere** — TLS 1.3 at ALB

✅ **Private subnets** — RDS not publicly accessible

✅ **JWT validation** — Cognito RS256 tokens

✅ **Rate limiting** — 60 req/min, 500 req/hr

✅ **Container security** — Non-root user, vulnerability scanning

✅ **Data encryption** — AES-256 at rest, TLS in transit

---

## SLIDE 10: Scalability

**Current capacity:**
- 2 ECS tasks → Auto-scales to 6
- RDS Multi-AZ → Read replicas on demand
- SageMaker → Auto-scaling to 0 when idle
- API Gateway → Millions of requests/day

**Scale to 1 million farmers:**
- ECS: Scale from 2→50 tasks automatically
- RDS: Enable read replicas (5 minutes)
- Bedrock: No capacity planning needed (managed)
- Cost: Linear scaling with farmer count

---

## SLIDE 11: Live Demo

**Demo Flow (3 minutes):**

1. **Login** as Ramesh Kumar, Pune farmer
2. **Input**: N=90, P=42, K=43, pH=6.5, Rain=800mm
3. **AI Results**:
   - 🌾 Rice — 87% confidence (top choice)
   - 📊 Yield: 4,350 kg/ha → 10,875 kg total
   - 💰 Price: ₹2,183/quintal → Rising trend (SELL)
   - ⚠️ Alert: Heavy rain in 72 hours
4. **Bedrock** explanation in Hindi

---

## SLIDE 12: Impact & Metrics

**Projected Impact (Year 1):**
- Target: 100,000 farmers across Maharashtra, Punjab, Telangana
- Crop selection accuracy: 60% → 87%
- Market timing improvement: Random → Data-driven
- Income increase: +15-20% per farmer
- Languages: 6 (Hindi, Marathi, Telugu, Kannada, Tamil, English)

**Technical Metrics:**
- API latency: < 300ms (p95)
- Model inference: < 100ms via SageMaker
- Bedrock explanation: < 2 seconds
- Uptime target: 99.9%

---

## SLIDE 13: Cost & Business Model

**AWS Monthly Cost (100K farmers):**
- ECS Fargate: ₹2,500
- RDS PostgreSQL: ₹4,500
- SageMaker endpoints: ₹8,000
- Bedrock API calls: ₹1,500
- **Total: ~₹19,000/month**

**Per farmer cost: ₹0.19/month** ← Extremely economical

**Revenue Model:**
- Government contract (PMKSY, Digital India)
- FPO (Farmer Producer Organization) subscriptions
- Agri-fintech partnerships (crop loan underwriting)

---

## SLIDE 14: Future Roadmap

**Phase 2 (3 months):**
- WhatsApp Bot (Twilio + Bedrock)
- SMS for feature phones
- NDVI satellite imagery (AWS Earth Observation)

**Phase 3 (6 months):**
- Offline PWA mode
- PM-KISAN scheme integration
- Crop disease detection (AWS Rekognition)

**Phase 4 (12 months):**
- Pan-India: All 28 states, 640+ districts
- Agri-fintech: Crop loan based on AI yield prediction
- International: Bangladesh, Nepal, Sri Lanka

---

## DEMO SCRIPT (5-7 Minutes)

### Opening (0:00-0:45)
> "700 million Indian farmers make billion-dollar decisions every season —
> what to plant, when to sell — based on outdated advice. AgroPulse AI
> changes that with real-time, hyper-local AI powered by AWS."

### Architecture (0:45-1:30)
> "Our system runs on 12 AWS services. The AI brain is Amazon SageMaker
> running 4 ML models, and Amazon Bedrock converting predictions into
> farmer-friendly explanations in 6 regional languages."

### Demo (1:30-4:30)

**Step 1: Login**
> "Meet Ramesh Kumar, a 2.5-hectare farmer from Pune, Maharashtra."
[Login with demo account]

**Step 2: Enter farm data**
> "Ramesh enters his soil NPK values from his Soil Health Card —
> nitrogen 90, phosphorus 42, potassium 43, pH 6.5, rainfall 800mm."
[Fill 3-step form]

**Step 3: Dashboard**
> "In under 2 seconds, our XGBoost model on SageMaker returns: Rice — 87% confidence.
> Our Gradient Boosting model predicts 4,350 kg per hectare yield.
> Prophet forecasts Rice prices rising — our market signal is SELL.
> The Isolation Forest detected heavy rainfall risk — Alert generated."

**Step 4: Bedrock Explanation**
> "But here's the magic: a farmer can't act on numbers alone.
> Amazon Bedrock takes all these outputs and generates this explanation
> [click Generate Explanation]... in plain Hindi, in 6 seconds."
[Show Hindi explanation]

### Technical Depth (4:30-5:30)
> "Under the hood: ECS Fargate runs our FastAPI backend —
> no server management. EventBridge triggers Lambda ETL daily —
> zero cost for scheduled jobs. IAM roles everywhere — no credentials in code.
> CI/CD via GitHub Actions automatically deploys to ECS + Amplify."

### Closing (5:30-6:00)
> "AgroPulse AI delivers hyper-local AI to the most underserved segment of India's
> economy — with zero infrastructure management, 6 languages, and a cost of
> 19 paise per farmer per month. This is AI that actually reaches Bharat."

---

## Key Talking Points for Judges

1. **Why AI?** Static advisories give generic advice. Our 4 ML models personalize for each farm's NPK + weather + location.

2. **Why AWS?** Bedrock removes GenAI infra burden. SageMaker scales inference. ECS Fargate eliminates server ops. This is a startup-friendly, production-ready stack.

3. **Why Bedrock specifically?** Converting model outputs to regional language explanations builds trust with rural farmers who can't interpret confidence scores.

4. **Scalability proof?** Auto-scaling ECS (2-50 tasks), SageMaker endpoint auto-scaling, RDS Multi-AZ — architecture handles 1M farmers with configuration changes only.

5. **Real-world impact?** 140M+ small/marginal farmers in India spend ₹2 lakh crore annually on wrong crops. A 15% improvement in decisions = ₹30,000 crore impact.
