# AgroPulse AI - Production Deployment Guide

## Pre-Deployment Checklist

### AWS Account Setup
- [ ] AWS account with Bedrock model access enabled (ap-south-1)
- [ ] IAM user with AdministratorAccess for initial setup
- [ ] S3 bucket for Terraform state: `agropulse-terraform-state`
- [ ] DynamoDB table for Terraform locks: `agropulse-terraform-locks`
- [ ] Domain registered (e.g., agropulse.ai) in Route53

### API Keys Required
- [ ] OpenWeatherMap API key (free tier: 60 calls/min)
- [ ] [Optional] AGMARKNET API key (data.gov.in registration)

---

## Step-by-Step Deployment

### 1. Clone Repository
```bash
git clone https://github.com/your-org/agropulse-ai.git
cd agropulse-ai
```

### 2. Create Terraform State Infrastructure
```bash
# Create S3 bucket for state (one-time)
aws s3 mb s3://agropulse-terraform-state --region ap-south-1
aws s3api put-bucket-versioning \
  --bucket agropulse-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB for state locking
aws dynamodb create-table \
  --table-name agropulse-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-south-1
```

### 3. Deploy AWS Infrastructure
```bash
cd infrastructure/terraform

# Initialize Terraform (downloads providers)
terraform init

# Review the plan (~40 AWS resources)
terraform plan \
  -var="db_password=SecureAgroPass123!" \
  -var="environment=production" \
  -out=tfplan

# Apply (takes ~15 minutes for RDS + ECS)
terraform apply tfplan

# Save outputs
terraform output > ../terraform-outputs.txt
cat ../terraform-outputs.txt
```

### 4. Enable Amazon Bedrock Model Access
```bash
# Via AWS Console:
# 1. Go to Amazon Bedrock → Model Access
# 2. Request access to: anthropic.claude-3-sonnet-20240229-v1:0
# 3. Wait for approval (usually instant for Claude Sonnet)

# Verify via CLI:
aws bedrock list-foundation-models \
  --by-provider anthropic \
  --region ap-south-1 \
  --query 'modelSummaries[].modelId'
```

### 5. Store Secrets
```bash
# OpenWeatherMap API key
aws secretsmanager put-secret-value \
  --secret-id agropulse/api-keys \
  --secret-string '{"openweather": "your_owm_api_key_here"}' \
  --region ap-south-1

# Verify
aws secretsmanager get-secret-value \
  --secret-id agropulse/api-keys \
  --region ap-south-1
```

### 6. Build and Push Docker Image
```bash
cd backend

# Get ECR URL from Terraform output
ECR_URL=$(terraform -chdir=../infrastructure/terraform output -raw ecr_repository_url)
echo "ECR: $ECR_URL"

# Login to ECR
aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin $ECR_URL

# Build production image (linux/amd64 for Fargate)
docker buildx build \
  --platform linux/amd64 \
  --tag $ECR_URL:latest \
  --push \
  .

echo "Image pushed: $ECR_URL:latest"
```

### 7. Initialize Database
```bash
# Get RDS endpoint from Terraform
RDS_ENDPOINT=$(terraform -chdir=../infrastructure/terraform output -raw rds_endpoint)

# Connect via bastion host OR AWS RDS Data API
# For initial setup, temporarily allow access from your IP:
psql "postgresql://agropulse:SecureAgroPass123!@${RDS_ENDPOINT}:5432/agropulse" \
  -f backend/scripts/init_db.sql

echo "Database initialized"
```

### 8. Deploy to ECS
```bash
# Update ECS service with new image
ECS_CLUSTER=$(terraform -chdir=infrastructure/terraform output -raw ecs_cluster_name)

aws ecs update-service \
  --cluster $ECS_CLUSTER \
  --service agropulse-backend-service \
  --force-new-deployment \
  --region ap-south-1

# Wait for deployment
aws ecs wait services-stable \
  --cluster $ECS_CLUSTER \
  --services agropulse-backend-service \
  --region ap-south-1

echo "ECS deployment complete!"
```

### 9. Train and Deploy ML Models

#### Option A: SageMaker Training (Production)
```bash
cd backend

SAGEMAKER_ROLE=$(terraform -chdir=../infrastructure/terraform output -raw sagemaker_role_arn)
S3_MODELS=$(terraform -chdir=../infrastructure/terraform output -raw s3_models_bucket)

# Train and deploy crop recommendation model
python ml/crop_recommendation/sagemaker_train.py \
  --bucket $S3_MODELS \
  --region ap-south-1 \
  --role-arn $SAGEMAKER_ROLE \
  --deploy

echo "Crop recommendation endpoint deployed"
```

#### Option B: Local Training (Development/Demo)
```bash
cd backend
pip install -r requirements.txt

python ml/crop_recommendation/train.py
python ml/yield_prediction/train.py
python ml/price_forecasting/train.py
python ml/risk_detection/train.py

echo "All models trained locally"
```

### 10. Deploy Frontend to AWS Amplify

#### Via AWS Console (Recommended):
1. Go to AWS Amplify Console
2. Click "New App" → "Host web app"
3. Connect your GitHub repository
4. Select `main` branch
5. Build settings (auto-detected for React):
   ```yaml
   version: 1
   frontend:
     phases:
       preBuild:
         commands:
           - cd frontend && npm ci
       build:
         commands:
           - npm run build
     artifacts:
       baseDirectory: frontend/build
       files:
         - '**/*'
     cache:
       paths:
         - frontend/node_modules/**/*
   ```
6. Set environment variables:
   - `REACT_APP_API_BASE_URL`: `https://api.agropulse.ai`
7. Click "Save and Deploy"

#### Via CLI:
```bash
AMPLIFY_APP_ID=$(aws amplify create-app \
  --name agropulse-frontend \
  --query 'app.appId' --output text)

aws amplify create-branch \
  --app-id $AMPLIFY_APP_ID \
  --branch-name main

aws amplify start-job \
  --app-id $AMPLIFY_APP_ID \
  --branch-name main \
  --job-type RELEASE
```

### 11. Configure ETL Lambda
```bash
# Package Lambda
cd backend
zip -r lambda_package.zip lambda/ etl/ requirements.txt

# Deploy Lambda
aws lambda create-function \
  --function-name agropulse-etl-trigger \
  --runtime python3.11 \
  --role arn:aws:iam::<ACCOUNT>:role/agropulse-ecs-task-role \
  --handler lambda.etl_trigger.lambda_handler \
  --zip-file fileb://lambda_package.zip \
  --timeout 300 \
  --memory-size 512 \
  --environment "Variables={S3_BUCKET_DATA=agropulse-data-lake,DATABASE_URL=<db_url>}"

# Setup EventBridge daily trigger (2 AM IST = 20:30 UTC)
aws events put-rule \
  --name agropulse-etl-daily \
  --schedule-expression "cron(30 20 * * ? *)" \
  --state ENABLED

aws events put-targets \
  --rule agropulse-etl-daily \
  --targets '[{"Id":"ETLTrigger","Arn":"arn:aws:lambda:ap-south-1:<ACCOUNT>:function:agropulse-etl-trigger"}]'
```

### 12. Setup DNS (Route53)
```bash
# Get ALB DNS name
ALB_DNS=$(terraform -chdir=infrastructure/terraform output -raw alb_dns_name)
echo "ALB DNS: $ALB_DNS"

# In Route53 Console:
# Create A record: api.agropulse.ai → ALB (Alias)
# Amplify handles: agropulse.ai → Amplify domain
```

---

## Verification Checklist

```bash
# 1. Health check
curl -f https://api.agropulse.ai/health
# Expected: {"status": "healthy", ...}

# 2. Crop prediction
curl -X POST https://api.agropulse.ai/predict/crop \
  -H "Content-Type: application/json" \
  -d '{"soil":{"nitrogen":90,"phosphorus":42,"potassium":43,"ph":6.5},"location":{"state":"Maharashtra","district":"Pune"},"rainfall_mm":800,"temperature_celsius":25,"humidity_percent":65}'

# 3. Bedrock explanation
curl -X POST https://api.agropulse.ai/generate-explanation \
  -H "Content-Type: application/json" \
  -d '{"prediction_type":"crop_recommendation","prediction_output":{"top_crop":"rice","confidence":0.87},"language":"en"}'

# 4. Frontend accessible
curl -I https://agropulse.ai
# Expected: 200 OK
```

---

## Monitoring Setup

```bash
# View ECS logs in CloudWatch
aws logs tail /agropulse/backend --follow --region ap-south-1

# View ECS service events
aws ecs describe-services \
  --cluster agropulse-cluster \
  --services agropulse-backend-service \
  --region ap-south-1 \
  --query 'services[0].events[:5]'

# Check RDS performance
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=agropulse-postgres \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

---

## Rollback Procedure

```bash
# Rollback ECS to previous task definition
PREV_TASK_DEF=$(aws ecs describe-task-definition \
  --task-definition agropulse-backend:$(( $(aws ecs list-task-definitions \
    --family-prefix agropulse-backend --query 'length(taskDefinitionArns)' --output text) - 1 )) \
  --query 'taskDefinition.taskDefinitionArn' --output text)

aws ecs update-service \
  --cluster agropulse-cluster \
  --service agropulse-backend-service \
  --task-definition $PREV_TASK_DEF

echo "Rollback initiated"
```

---

## Teardown (Cleanup)

```bash
# WARNING: This destroys all infrastructure
terraform -chdir=infrastructure/terraform destroy \
  -var="db_password=SecureAgroPass123!"

# Delete ECR images first (prevents destroy error)
aws ecr batch-delete-image \
  --repository-name agropulse-backend \
  --image-ids "$(aws ecr list-images --repository-name agropulse-backend --query 'imageIds[*]' --output json)" \
  --region ap-south-1
```
