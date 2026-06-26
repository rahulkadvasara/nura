"""
Nura - AI API Router
Endpoints for monitoring and testing the AI infrastructure
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import require_role, get_ai_service, get_groq_service
from app.models import UserRole, UserInDB
from app.schemas.ai import AIHealthResponse, AITestRequest, AITestResponse, TokenUsage
from app.services.ai_service import AIService
from app.services.groq_service import GroqService

router = APIRouter()


@router.get(
    "/health",
    response_model=AIHealthResponse,
    summary="Check AI Infrastructure Health",
    description="Validates Groq API configuration and connectivity by issuing a minimal request, recording response latency.",
)
async def get_ai_health(
    groq_service: GroqService = Depends(get_groq_service)
) -> AIHealthResponse:
    """
    AI Health Check Endpoint.
    Does not require authentication to allow public monitoring/deployment checks.
    """
    health_data = await groq_service.health_check()
    return AIHealthResponse(
        reachable=health_data["reachable"],
        model=health_data["model"],
        latency_ms=health_data["latency_ms"],
        status=health_data["status"],
        timestamp=health_data["timestamp"]
    )


@router.post(
    "/test",
    response_model=AITestResponse,
    summary="Test LLM Text Generation",
    description="Submits a direct prompt payload to the configured Groq LLM model and returns telemetry. Guarded: Admin Only.",
)
async def test_ai_generation(
    request_data: AITestRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    ai_service: AIService = Depends(get_ai_service)
) -> AITestResponse:
    """
    AI Infrastructure Test Playground Endpoint.
    Restricted to platform administrator accounts only.
    """
    try:
        service_response = await ai_service.generate(prompt=request_data.prompt)
        
        token_usage_obj = TokenUsage(
            prompt_tokens=service_response.prompt_tokens,
            completion_tokens=service_response.completion_tokens,
            total_tokens=service_response.total_tokens
        )
        
        return AITestResponse(
            response=service_response.response,
            model=service_response.model,
            token_usage=token_usage_obj,
            latency=service_response.latency_ms,
            finish_reason=service_response.finish_reason
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI playground request failed: {str(e)}"
        )
