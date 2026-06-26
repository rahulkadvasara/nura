"""
Nura - AI API Router
Endpoints for monitoring and testing the AI infrastructure
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import (
    require_role,
    get_ai_service,
    get_groq_service,
    get_embedding_service,
    get_vector_collection_service,
    get_vector_service,
    get_patient_context_service,
    require_exact_patient,
    get_current_user,
    get_doctor_profile_service
)
from app.models import UserRole, UserInDB
from app.schemas.ai import AIHealthResponse, AITestRequest, AITestResponse, TokenUsage
from app.schemas.embedding import EmbeddingHealthResponse, EmbeddingTestRequest, EmbeddingTestResponse
from app.schemas.vector import (
    VectorHealthResponse,
    VectorCollectionInfo,
    VectorTestRequest,
    VectorTestResponse,
    VectorTestResultItem
)
from app.schemas.patient_context import PatientContextResponse
from app.services.ai_service import AIService
from app.services.groq_service import GroqService
from app.services.embedding_service import EmbeddingService
from app.services.vector_collection_service import VectorCollectionService
from app.services.vector_service import VectorService
from app.services.patient_context_service import PatientContextService

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


@router.get(
    "/vector/health",
    response_model=VectorHealthResponse,
    summary="Check Vector Subsystem Health",
    description="Calculates connection check latency and monitors status statistics of all 5 collections. Guarded: Admin Only.",
)
async def get_vector_health(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    vector_service: VectorService = Depends(get_vector_service),
    collection_service: VectorCollectionService = Depends(get_vector_collection_service)
) -> VectorHealthResponse:
    """
    Vector DB Connection and Collections health status dashboard API endpoint.
    Admin authorized only.
    """
    import time
    start_time = time.perf_counter()
    try:
        health_data = await vector_service.health()
        latency = (time.perf_counter() - start_time) * 1000.0
        
        # Retrieve stats for the five collections
        from app.core.constants import QDRANT_COLLECTIONS
        collections_info = []
        for col_name in QDRANT_COLLECTIONS.values():
            try:
                stats = await collection_service.get_collection_stats(col_name)
                collections_info.append(
                    VectorCollectionInfo(
                        name=stats["name"],
                        status=stats["status"],
                        vector_count=stats["vector_count"],
                        dimensions=stats["dimensions"],
                        distance=stats["distance"],
                        storage_bytes=stats["storage_bytes"]
                    )
                )
            except Exception as ex:
                # If stats query fails (e.g. collection not found/error), provide default offline values
                collections_info.append(
                    VectorCollectionInfo(
                        name=col_name,
                        status="unhealthy",
                        vector_count=0,
                        dimensions=vector_service.settings.QDRANT_DEFAULT_VECTOR_SIZE,
                        distance=vector_service.settings.QDRANT_DEFAULT_DISTANCE.upper(),
                        storage_bytes=0
                    )
                )
                
        return VectorHealthResponse(
            connected=health_data.get("connected", False),
            latency=health_data.get("latency", latency),
            collections=collections_info
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector health query failed: {str(e)}"
        )


@router.get(
    "/vector/collections",
    response_model=List[VectorCollectionInfo],
    summary="List Vector Database Collections configurations",
    description="Returns configuration stats, point counts, dimensions, and distances parameters for all collections. Guarded: Admin Only.",
)
async def get_vector_collections(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    collection_service: VectorCollectionService = Depends(get_vector_collection_service)
) -> List[VectorCollectionInfo]:
    """
    Retrieves list of collection specs configurations.
    Admin authorized only.
    """
    from app.core.constants import QDRANT_COLLECTIONS
    collections_info = []
    for col_name in QDRANT_COLLECTIONS.values():
        try:
            stats = await collection_service.get_collection_stats(col_name)
            collections_info.append(
                VectorCollectionInfo(
                    name=stats["name"],
                    status=stats["status"],
                    vector_count=stats["vector_count"],
                    dimensions=stats["dimensions"],
                    distance=stats["distance"],
                    storage_bytes=stats["storage_bytes"]
                )
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to query collections specs for '{col_name}': {str(e)}"
            )
    return collections_info


@router.post(
    "/vector/test",
    response_model=VectorTestResponse,
    summary="Verify Semantic Search Pipeline connectivity",
    description="Generates embedding, upserts temporary test vector, executes near-neighbor search, and cleans up point. Guarded: Admin Only.",
)
async def test_vector_pipeline(
    request_data: VectorTestRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    vector_service: VectorService = Depends(get_vector_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> VectorTestResponse:
    """
    E2E Vector database verification pipeline.
    Admin authorized only.
    """
    import time
    import uuid
    from datetime import datetime, timezone
    from app.utils.hash import generate_content_hash
    
    start_time = time.perf_counter()
    point_id = str(uuid.uuid4())
    
    try:
        # 1. Generate text embedding
        vector = await embedding_service.embed(request_data.text)
        
        # 2. Map standard vector metadata payload
        content_hash = generate_content_hash(request_data.text)
        payload = {
            "source_id": "vector_playground_test",
            "patient_id": None,
            "document_type": "admin_test",
            "collection": request_data.collection,
            "embedding_model": embedding_service.settings.EMBEDDING_MODEL,
            "embedding_version": embedding_service.settings.EMBEDDING_VERSION,
            "indexed_at": datetime.now(timezone.utc).isoformat(),
            "content_hash": content_hash,
            "tags": ["temp", "playground"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # 3. Upsert temporary test point
        await vector_service.upsert(
            collection_name=request_data.collection,
            id=point_id,
            vector=vector,
            payload=payload
        )
        
        # 4. Query nearest neighbors (limit to 5)
        search_hits = await vector_service.search(
            collection_name=request_data.collection,
            query_vector=vector,
            limit=5
        )
        
        # 5. Cleanup the temporary point
        await vector_service.delete(
            collection_name=request_data.collection,
            ids=[point_id]
        )
        
        latency = (time.perf_counter() - start_time) * 1000.0
        
        # Format results items
        result_items = [
            VectorTestResultItem(
                id=hit["id"],
                score=hit["score"],
                payload=hit["payload"]
            )
            for hit in search_hits
        ]
        
        similarity_scores = [hit["score"] for hit in search_hits]
        
        return VectorTestResponse(
            latency=latency,
            search_results=result_items,
            similarity_scores=similarity_scores
        )
        
    except Exception as e:
        # Attempt cleanup if query fails but point was created
        try:
            await vector_service.delete(
                collection_name=request_data.collection,
                ids=[point_id]
            )
        except Exception:
            pass
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector playground verification pipeline failed: {str(e)}"
        )


@router.get(
    "/context/me",
    response_model=PatientContextResponse,
    summary="Get Authenticated Patient Context",
    description="Assembles the complete structured context profile for the logged-in patient user. Guarded: Patient Only.",
)
async def get_patient_context_me(
    current_user: UserInDB = Depends(require_exact_patient),
    context_service: PatientContextService = Depends(get_patient_context_service)
) -> PatientContextResponse:
    """Assembles patient context for the current active patient user"""
    return await context_service.assemble_context(patient_id=current_user.id)


@router.get(
    "/context/{patient_id}",
    response_model=PatientContextResponse,
    summary="Get Patient Context by ID",
    description="Assembles the complete structured context profile for the specified patient ID. Guarded: Admin, Verified Doctor. Verified Doctors are restricted to patients they have treated.",
)
async def get_patient_context_by_id(
    patient_id: str,
    current_user: UserInDB = Depends(get_current_user),
    context_service: PatientContextService = Depends(get_patient_context_service),
    doctor_profile_service = Depends(get_doctor_profile_service)
) -> PatientContextResponse:
    """Assembles patient context for a specified patient ID with strict authorization validation"""
    # 1. Admin bypasses all checks
    if current_user.role == UserRole.ADMIN:
        return await context_service.assemble_context(patient_id=patient_id)
        
    # 2. Doctors validation
    if current_user.role == UserRole.DOCTOR:
        # Check verified status of doctor
        from app.models.doctor import DoctorProfileStatus
        profile = await doctor_profile_service.get_profile_by_user_id(current_user.id)
        if not profile or profile.profile_status != DoctorProfileStatus.VERIFIED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor profile must be verified to retrieve patient context"
            )
            
        # Verify doctor treated the patient (exists in appointments or consultations)
        has_treated = await context_service.appointment_repository.exists({
            "patient_id": patient_id,
            "doctor_id": profile.id
        }) or await context_service.consultation_repository.exists({
            "patient_id": patient_id,
            "doctor_id": profile.id
        })
        
        if not has_treated:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Doctor has not treated this patient"
            )
            
        return await context_service.assemble_context(patient_id=patient_id)
        
    # 3. Deny all other roles
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions to access patient context"
    )
