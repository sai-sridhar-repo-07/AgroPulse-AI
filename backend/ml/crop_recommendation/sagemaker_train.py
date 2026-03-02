"""
AgroPulse AI - SageMaker Training Job Script
Submit crop recommendation training to SageMaker

Usage:
    python sagemaker_train.py --bucket agropulse-model-artifacts --region ap-south-1
"""
import argparse
import boto3
import sagemaker
from sagemaker.sklearn.estimator import SKLearn
from sagemaker.xgboost.estimator import XGBoost


def submit_training_job(bucket: str, region: str, role_arn: str):
    session = sagemaker.Session(boto3.Session(region_name=region))

    estimator = XGBoost(
        entry_point="train.py",
        source_dir=".",
        role=role_arn,
        instance_count=1,
        instance_type="ml.m5.xlarge",
        framework_version="1.7-1",
        py_version="py3",
        output_path=f"s3://{bucket}/models/crop-recommendation/",
        code_location=f"s3://{bucket}/code/",
        hyperparameters={
            "n-estimators": 200,
            "max-depth": 6,
            "learning-rate": 0.1,
        },
    )

    # Input data from S3
    train_input = sagemaker.inputs.TrainingInput(
        f"s3://{bucket}/data/processed/crop_recommendation/",
        content_type="text/csv",
    )

    print(f"Submitting SageMaker training job...")
    estimator.fit({"train": train_input}, wait=True)

    print(f"Training complete. Model artifact: {estimator.model_data}")
    return estimator


def deploy_endpoint(estimator, endpoint_name: str = "agropulse-crop-recommendation-v1"):
    """Deploy trained model to SageMaker endpoint"""
    print(f"Deploying to endpoint: {endpoint_name}")
    predictor = estimator.deploy(
        initial_instance_count=1,
        instance_type="ml.t2.medium",
        endpoint_name=endpoint_name,
    )
    print(f"Endpoint active: {endpoint_name}")
    return predictor


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--region", default="ap-south-1")
    parser.add_argument("--role-arn", required=True, help="SageMaker execution role ARN")
    parser.add_argument("--deploy", action="store_true")
    args = parser.parse_args()

    estimator = submit_training_job(args.bucket, args.region, args.role_arn)

    if args.deploy:
        deploy_endpoint(estimator)
