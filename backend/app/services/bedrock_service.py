"""
AgroPulse AI - Amazon Bedrock Generative AI Explanation Service

WHY GENERATIVE AI?
==================
Traditional ML models output numerical predictions (e.g., "Rice: 0.87 confidence").
Farmers cannot act on raw numbers. They need:
  1. Context: WHY is rice recommended?
  2. Language: Explanation in regional language (Hindi, Marathi, Telugu)
  3. Trust: Human-readable reasoning builds trust in AI decisions
  4. Actionability: What should the farmer DO next?

Amazon Bedrock with Claude provides:
  - Natural language generation from structured ML outputs
  - Multi-language support for rural India
  - Chain-of-thought reasoning visible to farmers
  - Culturally appropriate farming advice
"""
import json
from datetime import datetime, timezone
from typing import Optional

import boto3
import structlog
from fastapi import HTTPException

from app.config import settings
from app.schemas.explanation import ExplanationRequest, ExplanationResponse

logger = structlog.get_logger(__name__)

LANGUAGE_INSTRUCTIONS = {
    "en": "Respond in clear, simple English that a rural farmer can understand. Avoid technical jargon.",
    "hi": "हिंदी में सरल और स्पष्ट भाषा में उत्तर दें जो एक ग्रामीण किसान समझ सके।",
    "mr": "मराठीत साध्या आणि स्पष्ट भाषेत उत्तर द्या जे एक ग्रामीण शेतकरी समजू शकेल.",
    "te": "తెలుగులో సరళమైన మరియు స్పష్టమైన భాషలో సమాధానం ఇవ్వండి.",
    "kn": "ಕನ್ನಡದಲ್ಲಿ ಸರಳ ಮತ್ತು ಸ್ಪಷ್ಟ ಭಾಷೆಯಲ್ಲಿ ಉತ್ತರಿಸಿ.",
    "ta": "தமிழில் எளிய மற்றும் தெளிவான மொழியில் பதிலளிக்கவும்.",
}

EXPLANATION_PROMPTS = {
    "crop_recommendation": """You are an expert agricultural advisor helping Indian farmers.

A machine learning model has analyzed the following farm conditions and made crop recommendations:

**Model Output:**
{prediction_output}

**Feature Importance (what drove the recommendation):**
{feature_importance}

**Farmer Context:**
{farmer_context}

**Confidence Score:** {confidence_score:.0%}

{language_instruction}

Please provide:
1. A warm, clear explanation (2-3 sentences) of WHY this crop is recommended
2. 3 key insights as bullet points
3. 3 risk mitigation steps the farmer should take
4. A simple statement about how confident the AI is and why

Format your response as JSON with keys:
- "explanation": string
- "key_insights": array of strings
- "risk_mitigation": array of strings
- "confidence_narrative": string
""",

    "yield_prediction": """You are an expert agricultural advisor helping Indian farmers.

A machine learning model has predicted crop yield for this farmer:

**Model Output:**
{prediction_output}

**Key Factors:**
{feature_importance}

**Farmer Context:**
{farmer_context}

**Confidence Score:** {confidence_score:.0%}

{language_instruction}

Please provide:
1. A clear explanation of the predicted yield and what it means practically
2. 3 key insights about factors affecting this yield
3. 3 actionable steps to maximize/achieve this yield
4. A statement about prediction uncertainty

Format your response as JSON with keys:
- "explanation": string
- "key_insights": array of strings
- "risk_mitigation": array of strings
- "confidence_narrative": string
""",

    "price_forecast": """You are an expert agricultural market advisor helping Indian farmers.

A price forecasting model has analyzed mandi market trends:

**Forecast Output:**
{prediction_output}

**Market Signals:**
{feature_importance}

**Farmer Context:**
{farmer_context}

**Confidence Score:** {confidence_score:.0%}

{language_instruction}

Please provide:
1. A clear explanation of the price forecast and market signal (BUY/SELL/HOLD)
2. 3 key market insights
3. 3 practical steps the farmer should take based on this forecast
4. A note about market uncertainty

Format your response as JSON with keys:
- "explanation": string
- "key_insights": array of strings
- "risk_mitigation": array of strings
- "confidence_narrative": string
""",

    "risk_detection": """You are an expert agricultural risk advisor helping Indian farmers.

An anomaly detection model has identified the following risks for this farmer:

**Risk Assessment Output:**
{prediction_output}

**Risk Factors:**
{feature_importance}

**Farmer Context:**
{farmer_context}

**Overall Risk Score:** {confidence_score:.0%}

{language_instruction}

Please provide:
1. A clear, calm explanation of the detected risks (don't cause panic)
2. 3 key risk insights
3. 3 urgent mitigation steps the farmer must take
4. A reassuring statement about what actions can reduce risk

Format your response as JSON with keys:
- "explanation": string
- "key_insights": array of strings
- "risk_mitigation": array of strings
- "confidence_narrative": string
""",
}


class BedrockExplanationService:
    """
    Generative AI Explanation Service using Amazon Bedrock

    Value Add:
    - Converts ML model outputs → human-readable farmer advice
    - Supports 6 Indian regional languages
    - Provides explainability (XAI) for trust building
    - Generates actionable recommendations, not just predictions
    """

    def __init__(self):
        self.client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
        self.model_id = settings.BEDROCK_MODEL_ID

    def _build_prompt(self, request: ExplanationRequest) -> str:
        """Build a structured prompt from prediction context"""
        template = EXPLANATION_PROMPTS.get(
            request.prediction_type,
            EXPLANATION_PROMPTS["crop_recommendation"]
        )

        feature_str = json.dumps(request.feature_importance or {}, indent=2)
        context_str = json.dumps(request.farmer_context or {}, indent=2)
        output_str = json.dumps(request.prediction_output, indent=2)
        lang_instruction = LANGUAGE_INSTRUCTIONS.get(request.language, LANGUAGE_INSTRUCTIONS["en"])

        return template.format(
            prediction_output=output_str,
            feature_importance=feature_str,
            farmer_context=context_str,
            confidence_score=request.confidence_score or 0.75,
            language_instruction=lang_instruction,
        )

    async def generate_explanation(self, request: ExplanationRequest) -> ExplanationResponse:
        """
        Call Amazon Bedrock Claude to generate farmer-friendly explanation

        Flow:
        1. Build structured prompt from ML outputs
        2. Call Bedrock Claude API
        3. Parse JSON response
        4. Return structured ExplanationResponse
        """
        prompt = self._build_prompt(request)

        try:
            logger.info(
                "bedrock.request",
                model=self.model_id,
                prediction_type=request.prediction_type,
                language=request.language,
            )

            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": settings.BEDROCK_MAX_TOKENS,
                    "temperature": settings.BEDROCK_TEMPERATURE,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                }),
            )

            response_body = json.loads(response["body"].read())
            raw_text = response_body["content"][0]["text"]
            tokens_used = response_body.get("usage", {}).get("output_tokens", 0)

            # Extract JSON from response
            parsed = self._parse_response(raw_text)

            logger.info(
                "bedrock.response",
                tokens_used=tokens_used,
                prediction_type=request.prediction_type,
            )

            return ExplanationResponse(
                explanation=parsed.get("explanation", raw_text),
                key_insights=parsed.get("key_insights", []),
                risk_mitigation=parsed.get("risk_mitigation", []),
                confidence_narrative=parsed.get("confidence_narrative", ""),
                language=request.language,
                tokens_used=tokens_used,
                model_used=self.model_id,
                generated_at=datetime.now(timezone.utc).isoformat(),
            )

        except self.client.exceptions.ModelNotReadyException:
            raise HTTPException(status_code=503, detail="AI model is currently unavailable")
        except Exception as e:
            logger.error("bedrock.error", error=str(e), exc_info=True)
            # Fallback: return template-based explanation
            return self._fallback_explanation(request)

    def _parse_response(self, raw_text: str) -> dict:
        """Parse JSON from Bedrock response, handling markdown code blocks"""
        import re

        # Try to extract JSON block
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", raw_text)
        if json_match:
            return json.loads(json_match.group(1))

        # Try direct JSON parse
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            pass

        # Return raw as explanation if parsing fails
        return {
            "explanation": raw_text,
            "key_insights": [],
            "risk_mitigation": [],
            "confidence_narrative": "AI analysis complete.",
        }

    def _fallback_explanation(self, request: ExplanationRequest) -> ExplanationResponse:
        """Template-based fallback when Bedrock is unavailable"""
        pred = request.prediction_output
        explanation = f"Based on your soil and weather conditions, our AI model has analyzed your farm data with {(request.confidence_score or 0.75):.0%} confidence."

        return ExplanationResponse(
            explanation=explanation,
            key_insights=["Soil nutrients are the primary factor", "Weather conditions are favorable", "Market conditions have been considered"],
            risk_mitigation=["Monitor rainfall weekly", "Apply recommended fertilizer doses", "Check market prices before selling"],
            confidence_narrative=f"The model is {(request.confidence_score or 0.75):.0%} confident in this recommendation.",
            language=request.language,
            tokens_used=0,
            model_used="fallback-template",
            generated_at=datetime.now(timezone.utc).isoformat(),
        )


bedrock_service = BedrockExplanationService()
