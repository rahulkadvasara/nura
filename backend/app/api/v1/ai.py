"""
Nura - AI API Router
Endpoints for monitoring and testing the AI infrastructure
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import require_role, get_ai_service, get_groq_service, get_embedding_service
from app.models import UserRole, UserInDB
from app.schemas.ai import AIHealthResponse, AITestRequest, AITestResponse, TokenUsage
from app.schemas.embedding import EmbeddingHealthResponse, EmbeddingTestRequest, EmbeddingTestResponse
from app.services.ai_service import AIService
from app.services.groq_service import GroqService
from app.services.embedding_service import EmbeddingService

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


@router.get(
    "/embeddings/health",
    response_model=EmbeddingHealthResponse,
    summary="Check Embedding Subsystem Health",
    description="Validates local or remote embedding engine availability and computes execution latency.",
)
async def get_embedding_health(
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> EmbeddingHealthResponse:
    """
    Embedding Health Check Endpoint.
    Publicly accessible endpoint for health monitors.
    """
    health_data = await embedding_service.health_check()
    return EmbeddingHealthResponse(
        provider=health_data["provider"],
        model=health_data["model"],
        dimensions=health_data["dimensions"],
        latency=health_data["latency"],
        status=health_data["status"]
    )


@router.post(
    "/embeddings/test",
    response_model=EmbeddingTestResponse,
    summary="Test Document Embedding Generation",
    description="Generates embedding vector and returns preview with computed metadata. Guarded: Admin Only.",
)
async def test_embedding_generation(
    request_data: EmbeddingTestRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> EmbeddingTestResponse:
    """
    Embedding Verification Playground Endpoint.
    Admin authorization restricted.
    """
    import time
    start_time = time.perf_counter()
    try:
        # Generate single vector
        vector = await embedding_service.embed(request_data.text)
        latency = (time.perf_counter() - start_time) * 1000.0
        
        # Preview first 5 elements
        preview = vector[:5]
        
        from app.utils.hash import generate_content_hash
        content_hash = generate_content_hash(request_data.text)
        
        metadata = {
            "content_hash": content_hash,
            "embedding_model": embedding_service.settings.EMBEDDING_MODEL,
            "embedding_version": embedding_service.settings.EMBEDDING_VERSION,
            "document_type": "admin_test",
            "source_id": "playground_test",
            "collection_target": "test_collection"
        }
        
        return EmbeddingTestResponse(
            dimensions=len(vector),
            vector_preview=preview,
            latency=latency,
            metadata=metadata
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding playground generation failed: {str(e)}"
        )
