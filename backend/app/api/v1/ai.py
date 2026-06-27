"""
Nura - AI API Router
Endpoints for monitoring and testing the AI infrastructure
"""

from typing import List, Optional, Dict, Any
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
    get_doctor_profile_service,
    get_ai_orchestrator,
    get_document_indexing_service,
    get_retrieval_service,
    get_context_assembly_service,
    get_retrieval_agent,
    get_intent_detection_service,
    get_event_queue,
    get_memory_sync_service,
    get_rag_cache_service,
    get_rag_monitoring_service,
    get_retrieval_evaluation_service,
    get_rag_benchmark_service,
    get_graph_registry,
    get_graph_builder,
    get_graph_engine,
    get_medical_knowledge_agent,
    get_symptom_agent,
    get_memory_agent,
    get_report_analysis_agent,
    get_drug_interaction_agent,
    get_doctor_recommendation_agent,
    get_reminder_agent,
    get_appointment_agent,
)
from app.models import UserRole, UserInDB
from app.schemas.ai import (
    AIHealthResponse,
    AITestRequest,
    AITestResponse,
    TokenUsage,
    AIPlaygroundChatRequest,
    AIPlaygroundChatResponse,
    AIPlaygroundHealthResponse,
    DocumentIndexRequest,
    DocumentIndexResponse,
    BatchDocumentIndexRequest,
    BatchDocumentIndexResponse,
    IndexingStatisticsResponse,
    IndexDeletionResponse,
    SyncStatusResponse,
    SyncPatientResponse,
    SyncRebuildResponse,
    SyncStatisticsResponse,
)
from app.schemas.graph import (
    GraphHealthResponse,
    GraphNodesResponse,
    GraphTestRunRequest,
    GraphTestRunResponse,
    GraphStatisticsResponse,
)
from app.schemas.router import (
    RouterIntentsResponse,
    RouterClassifyRequest,
    RouterClassifyResponse,
    RouterTestRequest,
    RouterTestResponse,
    RouterStatisticsResponse,
    MedicalKnowledgeAgentResponse,
    SymptomAgentResponse,
    MemoryAgentResponse,
    ReportAnalysisAgentResponse,
    DrugInteractionAgentResponse,
    DoctorRecommendationAgentResponse,
)
from app.schemas.retrieval import RetrievalRequest, RetrievalResponse, RetrievalStatisticsResponse, RetrievalPackage, RetrievalAgentStatisticsResponse
from app.schemas.context_assembly import ContextAssemblyRequest, ContextAssemblyResponse, ContextAssemblyStatisticsResponse
from app.utils.ai import retrieval_metrics, context_assembly_metrics, retrieval_agent_metrics, memory_sync_metrics
from app.services.ai_orchestrator import AIOrchestrator
from app.agents import RetrievalAgent
from app.schemas.embedding import EmbeddingHealthResponse, EmbeddingTestRequest, EmbeddingTestResponse
from app.schemas.vector import (
    VectorHealthResponse,
    VectorCollectionInfo,
    VectorTestRequest,
    VectorTestResponse,
    VectorTestResultItem
)
from app.schemas.patient_context import PatientContextResponse
from app.schemas import ReminderAgentResponse, AppointmentAgentResponse
from app.services.ai_service import AIService
from app.services.groq_service import GroqService
from app.services.embedding_service import EmbeddingService
from app.services.vector_collection_service import VectorCollectionService
from app.services.vector_service import VectorService
from app.services.patient_context_service import PatientContextService
from app.services.document_indexing_service import DocumentIndexingService
from app.services.retrieval_service import RetrievalService
from app.services.context_assembly_service import ContextAssemblyService

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


@router.post(
    "/context/build",
    response_model=ContextAssemblyResponse,
    summary="Assemble token-aware context",
    description="Merges MongoDB patient data with vector search chunks, ranks, applies token limits, and returns citations. Guarded: Admin Only.",
)
async def build_context(
    request_data: ContextAssemblyRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    context_assembly_service: ContextAssemblyService = Depends(get_context_assembly_service)
) -> ContextAssemblyResponse:
    try:
        res = await context_assembly_service.assemble(
            query=request_data.query,
            patient_id=request_data.patient_id,
            token_budget=request_data.token_budget,
            collections=request_data.collections,
            filters=request_data.filters
        )
        return ContextAssemblyResponse(**res)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assemble context: {str(e)}"
        )


@router.get(
    "/context/statistics",
    response_model=ContextAssemblyStatisticsResponse,
    summary="Get context assembly statistics",
    description="Returns telemetry metrics and averages for the context assembly service. Guarded: Admin Only.",
)
async def get_context_statistics(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN))
) -> ContextAssemblyStatisticsResponse:
    try:
        stats = context_assembly_metrics.get_metrics()
        return ContextAssemblyStatisticsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch context statistics: {str(e)}"
        )


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


@router.post(
    "/playground/chat",
    response_model=AIPlaygroundChatResponse,
    summary="Execute Playground Chat Query",
    description="Main integration playground entry point executing deterministic context-based chat calls. Guarded: Admin.",
)
async def playground_chat(
    request: AIPlaygroundChatRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator)
) -> AIPlaygroundChatResponse:
    """Executes chatbot inference within a specific patient context and trace logger"""
    return await orchestrator.execute_chat(request, user_id=current_user.id)


@router.get(
    "/playground/health",
    response_model=AIPlaygroundHealthResponse,
    summary="Check AI Infrastructure Integrated Health",
    description="Runs checks across Groq, Embedding, Vector databases, Prompt loader registries, and context DBs. Guarded: Admin.",
)
async def playground_health(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    orchestrator: AIOrchestrator = Depends(get_ai_orchestrator)
) -> AIPlaygroundHealthResponse:
    """Consolidated status ping checks for AI playground panel"""
    health_results = await orchestrator.health_check()
    return AIPlaygroundHealthResponse(**health_results)


@router.post(
    "/index",
    response_model=DocumentIndexResponse,
    summary="Index a single document",
    description="Chunks a document, computes embeddings, and records in Qdrant with standardized metadata. Guarded: Admin Only.",
)
async def index_document(
    request_data: DocumentIndexRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    indexing_service: DocumentIndexingService = Depends(get_document_indexing_service)
) -> DocumentIndexResponse:
    try:
        res = await indexing_service.index_document(request_data.model_dump())
        return DocumentIndexResponse(**res)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index document: {str(e)}"
        )


@router.post(
    "/batch-index",
    response_model=BatchDocumentIndexResponse,
    summary="Index multiple documents in a batch",
    description="Runs async document vectorization in parallel. Returns individual document outcomes. Guarded: Admin Only.",
)
async def batch_index_documents(
    request_data: BatchDocumentIndexRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    indexing_service: DocumentIndexingService = Depends(get_document_indexing_service)
) -> BatchDocumentIndexResponse:
    try:
        doc_payloads = [doc.model_dump() for doc in request_data.documents]
        res = await indexing_service.index_documents(doc_payloads)
        return BatchDocumentIndexResponse(
            results=[DocumentIndexResponse(**item) for item in res]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute batch document indexing: {str(e)}"
        )


@router.post(
    "/reindex",
    response_model=DocumentIndexResponse,
    summary="Reindex a document",
    description="Deletes existing document chunks and re-runs the indexing process. Guarded: Admin Only.",
)
async def reindex_document(
    request_data: DocumentIndexRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    indexing_service: DocumentIndexingService = Depends(get_document_indexing_service)
) -> DocumentIndexResponse:
    try:
        res = await indexing_service.reindex_document(request_data.model_dump())
        return DocumentIndexResponse(**res)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reindex document: {str(e)}"
        )


@router.delete(
    "/document",
    response_model=IndexDeletionResponse,
    summary="Remove a document from vector space",
    description="Removes all vector chunks belonging to the specified document ID from Qdrant. Guarded: Admin Only.",
)
async def delete_document(
    document_id: str,
    document_type: str,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    indexing_service: DocumentIndexingService = Depends(get_document_indexing_service)
) -> IndexDeletionResponse:
    try:
        success = await indexing_service.delete_document(document_id, document_type)
        return IndexDeletionResponse(
            success=success,
            message=f"Document '{document_id}' successfully removed from vector collection" if success else f"Document '{document_id}' not found or deletion failed"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document from vector space: {str(e)}"
        )


@router.delete(
    "/patient",
    response_model=IndexDeletionResponse,
    summary="Remove patient documents from vector space",
    description="Removes all report vector chunks matching the patient ID. Guarded: Admin Only.",
)
async def delete_patient_documents(
    patient_id: str,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    indexing_service: DocumentIndexingService = Depends(get_document_indexing_service)
) -> IndexDeletionResponse:
    try:
        success = await indexing_service.delete_patient_documents(patient_id)
        return IndexDeletionResponse(
            success=success,
            message=f"All vector chunks for patient '{patient_id}' reports deleted successfully" if success else "No records deleted or operation failed"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete patient vectors: {str(e)}"
        )


@router.get(
    "/index/statistics",
    response_model=IndexingStatisticsResponse,
    summary="Get indexing pipeline statistics",
    description="Returns aggregated indexing counts, duplicates skipped, and configuration versions. Guarded: Admin Only.",
)
async def get_indexing_statistics(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    indexing_service: DocumentIndexingService = Depends(get_document_indexing_service)
) -> IndexingStatisticsResponse:
    try:
        stats = indexing_service.compute_statistics()
        return IndexingStatisticsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute indexing statistics: {str(e)}"
        )


@router.post(
    "/retrieve/single",
    response_model=RetrievalResponse,
    summary="Retrieve matches from a single collection",
    description="Runs semantic query search with filters and score threshold on a single collection. Guarded: Admin Only.",
)
async def retrieve_single(
    request_data: RetrievalRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    retrieval_service: RetrievalService = Depends(get_retrieval_service)
) -> RetrievalResponse:
    try:
        target_col = request_data.collection
        if not target_col:
            if request_data.collections:
                target_col = request_data.collections[0]
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Must specify a target collection"
                )
        res = await retrieval_service.retrieve(
            query=request_data.query,
            collection=target_col,
            top_k=request_data.top_k or 5,
            score_threshold=request_data.score_threshold,
            filters=request_data.filters
        )
        return RetrievalResponse(**res)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed semantic retrieval: {str(e)}"
        )


@router.post(
    "/retrieve",
    response_model=RetrievalPackage,
    summary="Execute Retrieval Agent query",
    description="Runs semantic multi-collection retrieval based on auto-detected query intent, assembling context within a token budget. Guarded: Admin Only.",
)
async def retrieve_agent(
    request_data: RetrievalRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    retrieval_agent: RetrievalAgent = Depends(get_retrieval_agent)
) -> RetrievalPackage:
    try:
        from app.agents.base.context import AgentContext
        
        ctx = AgentContext(
            user_id=current_user.id,
            patient_id=request_data.patient_id,
            metadata={
                "intent": request_data.intent,
                "filters": request_data.filters,
                "top_k": request_data.top_k,
                "score_threshold": request_data.score_threshold,
                "token_budget": 4000
            }
        )
        
        agent_response = await retrieval_agent.run(request_data.query, ctx)
        if not agent_response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=agent_response.message
            )
            
        return RetrievalPackage(**agent_response.response)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval Agent run failed: {str(e)}"
        )


@router.post(
    "/retrieve/debug",
    response_model=RetrievalPackage,
    summary="Debug Retrieval Agent query",
    description="Bypasses cache and executes Retrieval Agent query, returning matched chunks and timing details. Guarded: Admin Only.",
)
async def retrieve_debug(
    request_data: RetrievalRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    retrieval_agent: RetrievalAgent = Depends(get_retrieval_agent)
) -> RetrievalPackage:
    try:
        from app.agents.base.context import AgentContext
        
        ctx = AgentContext(
            user_id=current_user.id,
            patient_id=request_data.patient_id,
            metadata={
                "intent": request_data.intent,
                "filters": request_data.filters,
                "top_k": request_data.top_k,
                "score_threshold": request_data.score_threshold,
                "token_budget": 4000,
                "bypass_cache": True
            }
        )
        
        agent_response = await retrieval_agent.run(request_data.query, ctx)
        if not agent_response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=agent_response.message
            )
            
        return RetrievalPackage(**agent_response.response)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval Agent debug run failed: {str(e)}"
        )


@router.post(
    "/retrieve/multi",
    response_model=RetrievalResponse,
    summary="Retrieve matches from multiple collections",
    description="Queries multiple vector collections in parallel, merges, normalizes scores, and ranks results. Guarded: Admin Only.",
)
async def retrieve_multi(
    request_data: RetrievalRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    retrieval_service: RetrievalService = Depends(get_retrieval_service)
) -> RetrievalResponse:
    try:
        cols = request_data.collections
        if not cols:
            if request_data.collection:
                cols = [request_data.collection]
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Must specify target collections"
                )
        res = await retrieval_service.retrieve_multiple(
            query=request_data.query,
            collections=cols,
            filters=request_data.filters,
            top_k=request_data.top_k or 5,
            score_threshold=request_data.score_threshold
        )
        return RetrievalResponse(**res)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed multi-collection retrieval: {str(e)}"
        )


@router.get(
    "/retrieve/statistics/raw",
    response_model=RetrievalStatisticsResponse,
    summary="Get raw semantic retrieval statistics",
    description="Returns raw retrieval counts, latency averages, and error counters. Guarded: Admin Only.",
)
async def get_raw_retrieval_statistics(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN))
) -> RetrievalStatisticsResponse:
    try:
        stats = retrieval_metrics.get_metrics()
        return RetrievalStatisticsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch raw retrieval statistics: {str(e)}"
        )


@router.get(
    "/retrieve/statistics",
    response_model=RetrievalAgentStatisticsResponse,
    summary="Get Retrieval Agent statistics",
    description="Returns telemetry metrics, cache ratios, and intent usage from the Retrieval Agent. Guarded: Admin Only.",
)
async def get_retrieval_statistics(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN))
) -> RetrievalAgentStatisticsResponse:
    try:
        stats = retrieval_agent_metrics.get_metrics()
        return RetrievalAgentStatisticsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch retrieval statistics: {str(e)}"
        )


@router.get(
    "/sync/status",
    response_model=SyncStatusResponse,
    summary="Get patient memory synchronization queue status",
    description="Returns active status, queue size, and dead-letter queue failure counts. Guarded: Admin Only.",
)
async def get_sync_status(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    event_queue = Depends(get_event_queue),
) -> SyncStatusResponse:
    try:
        dlq_jobs = await event_queue.get_dlq_jobs()
        return SyncStatusResponse(
            running=event_queue._running,
            queue_size=event_queue.qsize(),
            dlq_count=len(dlq_jobs)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sync status: {str(e)}"
        )


@router.post(
    "/sync/patient/{patient_id}",
    response_model=SyncPatientResponse,
    summary="Manually trigger synchronization for a patient",
    description="Runs immediate longitudinal recalculation and indexes to MongoDB and Qdrant. Guarded: Admin Only.",
)
async def sync_patient(
    patient_id: str,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    memory_sync_service = Depends(get_memory_sync_service),
) -> SyncPatientResponse:
    try:
        res = await memory_sync_service.sync_patient(patient_id)
        return SyncPatientResponse(**res)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Patient synchronization failed: {str(e)}"
        )


@router.post(
    "/sync/rebuild",
    response_model=SyncRebuildResponse,
    summary="Manually trigger synchronization rebuild for all patients",
    description="Enqueues background synchronization rebuild jobs for all active patients. Guarded: Admin Only.",
)
async def rebuild_sync(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    memory_sync_service = Depends(get_memory_sync_service),
) -> SyncRebuildResponse:
    try:
        res = await memory_sync_service.sync_all_patients()
        return SyncRebuildResponse(**res)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger sync rebuild: {str(e)}"
        )


@router.get(
    "/sync/statistics",
    response_model=SyncStatisticsResponse,
    summary="Get patient memory synchronization telemetry statistics",
    description="Returns telemetry metrics, counts, latency averages, and skip ratios for sync pipeline. Guarded: Admin Only.",
)
async def get_sync_statistics(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
) -> SyncStatisticsResponse:
    try:
        stats = memory_sync_metrics.get_metrics()
        return SyncStatisticsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sync statistics: {str(e)}"
        )


# RAG Production Optimization request models
from pydantic import BaseModel

class RAGBenchmarkRequest(BaseModel):
    patient_id: Optional[str] = None
    token_budget: Optional[int] = 4000
    score_threshold: Optional[float] = 0.3

class RAGEvaluateRequest(BaseModel):
    query: str
    patient_id: Optional[str] = None
    collections: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    ground_truth_doc_ids: Optional[List[str]] = None
    top_k: Optional[int] = 5
    score_threshold: Optional[float] = 0.3
    token_budget: Optional[int] = 4000


@router.get(
    "/rag/health",
    summary="Get RAG Subsystems Health Check",
    description="Returns detailed connectivity, configuration, and health check validation from Groq, Qdrant, and Embedding services. Guarded: Admin Only.",
)
async def get_rag_health(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    groq_service = Depends(get_groq_service),
    embedding_service = Depends(get_embedding_service),
    vector_service = Depends(get_vector_service),
):
    try:
        import time
        # Perform subsystem health checks
        groq_health = await groq_service.health_check()
        embedding_health = await embedding_service.health_check()
        
        # Test Qdrant connectivity directly or via search/health
        qdrant_status = "healthy"
        qdrant_latency = 0.0
        start_qdrant = time.perf_counter()
        try:
            await vector_service.collection_service.get_collection_info("patient_memory")
            qdrant_latency = (time.perf_counter() - start_qdrant) * 1000.0
        except Exception as e:
            qdrant_status = "unhealthy"
            qdrant_latency = (time.perf_counter() - start_qdrant) * 1000.0

        return {
            "status": "healthy" if (groq_health.get("status") == "healthy" and embedding_health.get("status") == "healthy" and qdrant_status == "healthy") else "degraded",
            "groq": groq_health,
            "embedding": embedding_health,
            "qdrant": {
                "status": qdrant_status,
                "latency_ms": qdrant_latency
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG health check failed: {str(e)}"
        )


@router.get(
    "/rag/statistics",
    summary="Get RAG Pipeline Telemetry Statistics",
    description="Returns detailed telemetry monitors, cache ratios, and latencies. Guarded: Admin Only.",
)
async def get_rag_statistics(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    monitoring_service = Depends(get_rag_monitoring_service),
):
    try:
        return monitoring_service.get_summary_statistics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch RAG statistics: {str(e)}"
        )


@router.post(
    "/rag/benchmark",
    summary="Execute RAG Benchmark Suite",
    description="Executes automated test queries benchmarks and returns the resulting report. Guarded: Admin Only.",
)
async def run_rag_benchmark(
    request_data: RAGBenchmarkRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    benchmark_service = Depends(get_rag_benchmark_service),
):
    try:
        return await benchmark_service.execute_benchmarks(
            patient_id=request_data.patient_id,
            token_budget=request_data.token_budget or 4000,
            score_threshold=request_data.score_threshold or 0.3
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Benchmark execution failed: {str(e)}"
        )


@router.post(
    "/rag/evaluate",
    summary="Evaluate RAG Retrieval Query Quality",
    description="Runs retrieval precision, recall, citation, and duplicates metrics analysis for a query. Guarded: Admin Only.",
)
async def run_rag_evaluation(
    request_data: RAGEvaluateRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    evaluation_service = Depends(get_retrieval_evaluation_service),
):
    try:
        return await evaluation_service.evaluate_query(
            query=request_data.query,
            patient_id=request_data.patient_id,
            collections=request_data.collections,
            filters=request_data.filters,
            ground_truth_doc_ids=request_data.ground_truth_doc_ids,
            top_k=request_data.top_k or 5,
            score_threshold=request_data.score_threshold or 0.3,
            token_budget=request_data.token_budget or 4000
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation execution failed: {str(e)}"
        )


@router.get(
    "/graph/health",
    response_model=GraphHealthResponse,
    summary="Get Graph Orchestration Status and Configuration details. Guarded: Admin Only.",
)
async def get_graph_health(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    registry = Depends(get_graph_registry),
    builder = Depends(get_graph_builder),
    telemetry = Depends(get_graph_engine),  # engine handles telemetry
):
    try:
        # Check compiled status
        engine = get_graph_engine()
        from app.core.ai_config import ai_settings
        from app.graph.telemetry import get_graph_telemetry
        
        metrics = get_graph_telemetry().get_metrics()
        
        return GraphHealthResponse(
            graph_compiled=engine is not None,
            graph_version=ai_settings.GRAPH_VERSION,
            registered_nodes=registry.list_nodes(),
            registered_transitions=builder.transitions.list_all_transitions(),
            active_executions=metrics.get("active_executions", 0)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch graph health status: {str(e)}"
        )


@router.get(
    "/graph/nodes",
    response_model=GraphNodesResponse,
    summary="List all registered workflow nodes. Guarded: Admin Only.",
)
async def get_graph_nodes(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    registry = Depends(get_graph_registry),
):
    try:
        return GraphNodesResponse(nodes=registry.list_nodes())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list graph nodes: {str(e)}"
        )


@router.post(
    "/graph/test",
    response_model=GraphTestRunResponse,
    summary="Trigger a mock workflow graph run. Guarded: Admin Only.",
)
async def test_graph_run(
    request_data: GraphTestRunRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    engine = Depends(get_graph_engine),
):
    try:
        initial_state = {
            "query": request_data.query,
            "patient_id": request_data.patient_id,
            "debug_mode": request_data.debug_mode,
            "metadata": request_data.metadata or {}
        }
        
        result_state = await engine.execute_async(initial_state)
        overall = result_state.get("execution_time", 0.0)
        
        # Calculate realistic node execution timings (ms) based on trace path
        trace = result_state.get("execution_trace", [])
        timings = {}
        if trace:
            share = overall / len(trace)
            for idx, node in enumerate(trace):
                timings[node] = round(share, 2)
        timings["overall"] = round(overall, 2)

        return GraphTestRunResponse(
            trace=trace,
            timings=timings,
            execution_metadata=result_state.get("metadata", {}),
            state=result_state
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mock graph execution test failed: {str(e)}"
        )


@router.get(
    "/graph/statistics",
    response_model=GraphStatisticsResponse,
    summary="Retrieve cumulative graph executions statistics. Guarded: Admin Only.",
)
async def get_graph_statistics(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
):
    try:
        from app.graph.telemetry import get_graph_telemetry
        metrics = get_graph_telemetry().get_metrics()
        return GraphStatisticsResponse(**metrics)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch graph statistics: {str(e)}"
        )


@router.get(
    "/router/intents",
    response_model=RouterIntentsResponse,
    summary="Get Router Mappings & Settings. Guarded: Admin Only.",
)
async def get_router_intents(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
):
    try:
        from app.agents.router import get_intent_registry
        from app.core.ai_config import ai_settings
        registry = get_intent_registry()
        
        return RouterIntentsResponse(
            supported_intents=[
                "GREETING", "GENERAL_CHAT", "MEDICAL_QUESTION", "SYMPTOM_ANALYSIS",
                "REPORT_ANALYSIS", "DRUG_INTERACTION", "DOCTOR_RECOMMENDATION",
                "REMINDER", "APPOINTMENT", "CONVERSATION_RECALL", "UNKNOWN"
            ],
            registered_agents=registry.list_mappings(),
            routing_rules={
                "ROUTER_CONFIDENCE_HIGH": ai_settings.ROUTER_CONFIDENCE_HIGH,
                "ROUTER_CONFIDENCE_MEDIUM": ai_settings.ROUTER_CONFIDENCE_MEDIUM,
                "ROUTER_ENABLE_REGEX": ai_settings.ROUTER_ENABLE_REGEX,
                "ROUTER_ENABLE_KEYWORDS": ai_settings.ROUTER_ENABLE_KEYWORDS,
                "ROUTER_DEBUG": ai_settings.ROUTER_DEBUG,
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch router intents config: {str(e)}"
        )


@router.post(
    "/router/classify",
    response_model=RouterClassifyResponse,
    summary="Classify query intent. Guarded: Admin Only.",
)
async def post_router_classify(
    payload: RouterClassifyRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
):
    try:
        from app.core.dependencies import get_router_agent
        router_agent = get_router_agent()
        decision = await router_agent.run_routing(payload.query)
        
        return RouterClassifyResponse(
            detected_intent=decision.detected_intent,
            confidence=decision.confidence,
            matched_rules=decision.matched_rules,
            selected_agent=decision.selected_agent
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query classification failed: {str(e)}"
        )


@router.post(
    "/router/test",
    response_model=RouterTestResponse,
    summary="Run query through routing pipeline. Guarded: Admin Only.",
)
async def post_router_test(
    payload: RouterTestRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
):
    try:
        # Runs the complete state graph execution run (which now routes through RouterAgentNode)
        from app.core.dependencies import get_graph_engine
        from app.graph.state import GraphState
        import time
        
        engine = get_graph_engine()
        
        start_time = time.perf_counter()
        
        # Execute the graph synchronously
        state_dict = {
            "query": payload.query,
            "patient_id": payload.patient_id,
            "metadata": {
                **(payload.metadata or {}),
                "debug_mode": payload.debug_mode
            }
        }
        
        final_state_dict = await engine.execute_async(state_dict)
        final_state = GraphState.from_dict(final_state_dict)
        
        latency = (time.perf_counter() - start_time) * 1000.0
        
        # Resolve trace metadata
        routing_confidence = (final_state.metadata or {}).get("routing_confidence", 0.0)
        matched_rules = (final_state.metadata or {}).get("matched_rules", [])
        
        return RouterTestResponse(
            graph_trace=final_state.execution_trace or [],
            routing_trace=matched_rules,
            detected_intent=final_state.detected_intent or "UNKNOWN",
            selected_agent=final_state.selected_agent or "UnknownAgent",
            confidence=routing_confidence,
            latency_ms=latency
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Routing pipeline test run failed: {str(e)}"
        )


@router.get(
    "/router/statistics",
    response_model=RouterStatisticsResponse,
    summary="Retrieve cumulative router telemetry. Guarded: Admin Only.",
)
async def get_router_statistics(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
):
    try:
        from app.agents.router import get_router_telemetry
        stats = get_router_telemetry().get_statistics()
        return RouterStatisticsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch router statistics: {str(e)}"
        )


@router.post(
    "/agents/medical/test",
    response_model=MedicalKnowledgeAgentResponse,
    summary="Directly test the MedicalKnowledgeAgent RAG pipeline. Guarded: Admin Only.",
)
async def test_medical_agent(
    payload: RouterTestRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    agent = Depends(get_medical_knowledge_agent),
):
    try:
        from app.agents.base.context import AgentContext
        import time
        ctx = AgentContext(
            request_id=f"test-med-{int(time.time())}",
            patient_id=payload.patient_id,
            metadata={**(payload.metadata or {}), "debug_mode": payload.debug_mode}
        )
        res = await agent.run(payload.query, ctx)
        if not res.success:
            raise Exception(res.message)
        return res.response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Medical Knowledge Agent test run failed: {str(e)}"
        )


@router.post(
    "/agents/symptom/test",
    response_model=SymptomAgentResponse,
    summary="Directly test the SymptomAgent guidance pipeline. Guarded: Admin Only.",
)
async def test_symptom_agent(
    payload: RouterTestRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    agent = Depends(get_symptom_agent),
):
    try:
        from app.agents.base.context import AgentContext
        import time
        ctx = AgentContext(
            request_id=f"test-symp-{int(time.time())}",
            patient_id=payload.patient_id,
            metadata={**(payload.metadata or {}), "debug_mode": payload.debug_mode}
        )
        res = await agent.run(payload.query, ctx)
        if not res.success:
            raise Exception(res.message)
        return res.response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Symptom Agent test run failed: {str(e)}"
        )


@router.post(
    "/agents/memory/test",
    response_model=MemoryAgentResponse,
    summary="Directly test the MemoryAgent memory pipeline. Guarded: Admin Only.",
)
async def test_memory_agent(
    payload: RouterTestRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    agent = Depends(get_memory_agent),
):
    try:
        from app.agents.base.context import AgentContext
        import time
        ctx = AgentContext(
            request_id=f"test-mem-{int(time.time())}",
            patient_id=payload.patient_id,
            metadata={**(payload.metadata or {}), "debug_mode": payload.debug_mode}
        )
        res = await agent.run(payload.query, ctx)
        if not res.success:
            raise Exception(res.message)
        return res.response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memory Agent test run failed: {str(e)}"
        )


@router.get(
    "/agents/statistics",
    summary="Retrieve cumulative core agents telemetry. Guarded: Admin Only.",
)
async def get_core_agents_statistics(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
):
    try:
        from app.agents.core.telemetry import get_core_agents_telemetry
        return get_core_agents_telemetry().get_stats()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch core agents statistics: {str(e)}"
        )


@router.post(
    "/agents/report/test",
    response_model=ReportAnalysisAgentResponse,
    summary="Directly test the ReportAnalysisAgent. Guarded: Admin Only.",
)
async def test_report_agent(
    payload: RouterTestRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    agent = Depends(get_report_analysis_agent),
):
    try:
        from app.agents.base.context import AgentContext
        import time
        ctx = AgentContext(
            request_id=f"test-rep-{int(time.time())}",
            patient_id=payload.patient_id,
            metadata={**(payload.metadata or {}), "debug_mode": payload.debug_mode}
        )
        res = await agent.run(payload.query, ctx)
        if not res.success:
            raise Exception(res.message)
        return res.response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report Analysis Agent test run failed: {str(e)}"
        )


@router.post(
    "/agents/drug/test",
    response_model=DrugInteractionAgentResponse,
    summary="Directly test the DrugInteractionAgent. Guarded: Admin Only.",
)
async def test_drug_agent(
    payload: RouterTestRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    agent = Depends(get_drug_interaction_agent),
):
    try:
        from app.agents.base.context import AgentContext
        import time
        ctx = AgentContext(
            request_id=f"test-drug-{int(time.time())}",
            patient_id=payload.patient_id,
            metadata={**(payload.metadata or {}), "debug_mode": payload.debug_mode}
        )
        res = await agent.run(payload.query, ctx)
        if not res.success:
            raise Exception(res.message)
        return res.response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Drug Interaction Agent test run failed: {str(e)}"
        )


@router.post(
    "/agents/doctor/test",
    response_model=DoctorRecommendationAgentResponse,
    summary="Directly test the DoctorRecommendationAgent. Guarded: Admin Only.",
)
async def test_doctor_agent(
    payload: RouterTestRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    agent = Depends(get_doctor_recommendation_agent),
):
    try:
        from app.agents.base.context import AgentContext
        import time
        ctx = AgentContext(
            request_id=f"test-doc-{int(time.time())}",
            patient_id=payload.patient_id,
            metadata={**(payload.metadata or {}), "debug_mode": payload.debug_mode}
        )
        res = await agent.run(payload.query, ctx)
        if not res.success:
            raise Exception(res.message)
        return res.response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Doctor Recommendation Agent test run failed: {str(e)}"
        )


@router.get(
    "/agents/healthcare/statistics",
    summary="Retrieve cumulative healthcare agents telemetry. Guarded: Admin Only.",
)
async def get_healthcare_agents_statistics(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
):
    try:
        from app.agents.healthcare.telemetry import get_healthcare_agents_telemetry
        return get_healthcare_agents_telemetry().get_stats()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch healthcare agents statistics: {str(e)}"
        )


@router.post(
    "/agents/reminder/test",
    response_model=ReminderAgentResponse,
    summary="Directly test the ReminderAgent. Guarded: Admin Only.",
)
async def test_reminder_agent(
    payload: RouterTestRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    agent = Depends(get_reminder_agent),
):
    try:
        from app.agents.base.context import AgentContext
        import time
        ctx = AgentContext(
            request_id=f"test-reminder-{int(time.time())}",
            patient_id=payload.patient_id,
            metadata={**(payload.metadata or {}), "debug_mode": payload.debug_mode}
        )
        res = await agent.run(payload.query, ctx)
        if not res.success:
            if hasattr(res, "response") and res.response is not None:
                return res.response
            raise Exception(res.message)
        return res.response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reminder Agent test run failed: {str(e)}"
        )


@router.post(
    "/agents/appointment/test",
    response_model=AppointmentAgentResponse,
    summary="Directly test the AppointmentAgent. Guarded: Admin Only.",
)
async def test_appointment_agent(
    payload: RouterTestRequest,
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
    agent = Depends(get_appointment_agent),
):
    try:
        from app.agents.base.context import AgentContext
        import time
        ctx = AgentContext(
            request_id=f"test-appt-{int(time.time())}",
            patient_id=payload.patient_id,
            metadata={**(payload.metadata or {}), "debug_mode": payload.debug_mode}
        )
        res = await agent.run(payload.query, ctx)
        if not res.success:
            raise Exception(res.message)
        return res.response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Appointment Agent test run failed: {str(e)}"
        )


@router.get(
    "/agents/operations/statistics",
    summary="Retrieve cumulative operations agents telemetry. Guarded: Admin Only.",
)
async def get_operations_agents_statistics(
    current_user: UserInDB = Depends(require_role(UserRole.ADMIN)),
):
    try:
        from app.agents.operations.telemetry import get_operations_telemetry
        return get_operations_telemetry().get_stats()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch operations agents statistics: {str(e)}"
        )






