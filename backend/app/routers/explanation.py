"""
AgroPulse AI - GenAI Explanation Router
POST /generate-explanation

This is the CORE DIFFERENTIATOR of AgroPulse AI:
- Converts ML model outputs into human-readable farmer advice
- Uses Amazon Bedrock (Claude) for natural language generation
- Supports 6 Indian languages
- Provides explainable AI (XAI) for rural trust building
"""
from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas.explanation import ExplanationRequest, ExplanationResponse
from app.services.bedrock_service import bedrock_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/generate-explanation",
    response_model=ExplanationResponse,
    summary="AI-Powered Explanation (Amazon Bedrock)",
    description="""
    ## Amazon Bedrock Generative AI Explanation

    **Why is this critical?**

    Traditional ML models return numbers. Farmers need:
    1. **Context**: "Why is rice recommended over wheat?"
    2. **Language**: Explanation in Hindi, Marathi, Telugu, Kannada
    3. **Trust**: Transparent reasoning builds confidence in AI decisions
    4. **Action**: Clear next steps based on AI recommendation

    **How Bedrock adds value:**
    - Converts technical outputs → simple farmer-friendly language
    - Provides cultural context (Indian farming seasons, practices)
    - Generates risk mitigation advice automatically
    - Supports multi-lingual output (en/hi/mr/te/kn/ta)

    **Bedrock Model:** Claude Sonnet (anthropic.claude-3-sonnet-20240229-v1:0)
    """,
)
@limiter.limit("20/minute")
async def generate_explanation(
    request: Request,
    payload: ExplanationRequest,
):
    """
    Generate farmer-friendly AI explanation using Amazon Bedrock.

    Input: ML model outputs + feature importance + farmer context
    Output: Human-readable explanation in requested language
    """
    return await bedrock_service.generate_explanation(payload)
