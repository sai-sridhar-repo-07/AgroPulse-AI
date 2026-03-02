"""
AgroPulse AI - EventBridge-triggered Lambda ETL Orchestrator
Triggered daily by Amazon EventBridge to run data ingestion pipelines

EventBridge Rule:
  Schedule: cron(0 2 * * ? *)  ← Runs at 2 AM IST daily
  Target: This Lambda function

Pipeline Order:
  1. Weather data ingestion (OpenWeatherMap → S3 → RDS)
  2. Market data ingestion (AGMARKNET → S3 → RDS)
  3. Soil data ingestion (SHC → S3)  ← Monthly only
"""
import json
import os
import sys
import logging
from datetime import datetime, timezone

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
SNS_ALERT_TOPIC = os.getenv("SNS_ALERT_TOPIC_ARN", "")


def run_weather_pipeline():
    """Run weather data ingestion"""
    logger.info("Starting weather ETL pipeline")
    try:
        # Import and run pipeline
        sys.path.insert(0, "/opt/python")
        from etl.weather_ingestion import run_pipeline
        result = run_pipeline()
        logger.info(f"Weather ETL complete: {result}")
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Weather ETL failed: {e}")
        return {"status": "error", "error": str(e)}


def run_market_pipeline():
    """Run market data ingestion"""
    logger.info("Starting market data ETL pipeline")
    try:
        from etl.market_data_ingestion import run_pipeline
        result = run_pipeline()
        logger.info(f"Market ETL complete: {result}")
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Market ETL failed: {e}")
        return {"status": "error", "error": str(e)}


def run_soil_pipeline(force: bool = False):
    """Run soil data ingestion (monthly)"""
    now = datetime.now(timezone.utc)
    # Only run on 1st of month unless forced
    if now.day != 1 and not force:
        logger.info("Skipping soil ETL (not 1st of month)")
        return {"status": "skipped", "reason": "monthly schedule"}

    logger.info("Starting soil ETL pipeline")
    try:
        from etl.soil_data_ingestion import run_pipeline
        result = run_pipeline()
        logger.info(f"Soil ETL complete: {result}")
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Soil ETL failed: {e}")
        return {"status": "error", "error": str(e)}


def send_alert(message: str, subject: str = "AgroPulse ETL Alert"):
    """Send SNS notification on pipeline failure"""
    if not SNS_ALERT_TOPIC:
        return
    try:
        sns = boto3.client("sns", region_name=AWS_REGION)
        sns.publish(TopicArn=SNS_ALERT_TOPIC, Subject=subject, Message=message)
    except Exception as e:
        logger.error(f"SNS alert failed: {e}")


def lambda_handler(event, context):
    """
    Lambda entry point — triggered by EventBridge
    event example: {"pipeline": "all"} or {"pipeline": "weather"}
    """
    start_time = datetime.now(timezone.utc)
    pipeline = event.get("pipeline", "all")
    force_soil = event.get("force_soil", False)

    logger.info(json.dumps({
        "event": "etl_pipeline_start",
        "pipeline": pipeline,
        "timestamp": start_time.isoformat(),
        "invocation_id": context.aws_request_id if context else "local",
    }))

    results = {}

    if pipeline in ("all", "weather"):
        results["weather"] = run_weather_pipeline()

    if pipeline in ("all", "market"):
        results["market"] = run_market_pipeline()

    if pipeline in ("all", "soil"):
        results["soil"] = run_soil_pipeline(force=force_soil)

    # Check for failures
    failures = [k for k, v in results.items() if v.get("status") == "error"]
    if failures:
        error_msg = f"ETL pipelines failed: {failures}\n\nDetails:\n{json.dumps(results, indent=2)}"
        send_alert(error_msg, "AgroPulse ETL Failure Alert")
        logger.error(f"ETL failures: {failures}")

    end_time = datetime.now(timezone.utc)
    duration_sec = (end_time - start_time).total_seconds()

    response = {
        "statusCode": 200 if not failures else 207,
        "body": json.dumps({
            "executed_at": start_time.isoformat(),
            "duration_seconds": duration_sec,
            "pipeline": pipeline,
            "results": results,
            "failures": failures,
        })
    }

    logger.info(json.dumps({
        "event": "etl_pipeline_complete",
        "duration_seconds": duration_sec,
        "failures": failures,
    }))

    return response


if __name__ == "__main__":
    # Local testing
    result = lambda_handler({"pipeline": "all", "force_soil": True}, None)
    print(json.dumps(json.loads(result["body"]), indent=2))
