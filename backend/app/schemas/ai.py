"""
Nura - AI Schemas
Pydantic response and request models for AI health and playground test endpoints
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class AIHealthResponse(BaseModel):
    """Schema representing AI infrastructure connectivity health status"""
    reachable: bool = Field(..., description="Indicates if the Groq API service is reachable")
    model: str = Field(..., description="The currently configured default model name")
    latency_ms: float = Field(..., description="Response latency of connectivity check in milliseconds")
    status: str = Field(..., description="General health state (healthy or unhealthy)")
    timestamp: str = Field(..., description="ISO 8601 formatted UTC check timestamp")


class AITestRequest(BaseModel):
    """Schema for requesting a direct AI prompt generation verification test"""
    prompt: str = Field(..., min_length=1, description="Raw prompt text payload to run against the LLM")


class TokenUsage(BaseModel):
    """Token accounting details for a request execution"""
    prompt_tokens: int = Field(..., description="Tokens utilized in the input prompt request")
    completion_tokens: int = Field(..., description="Tokens generated in the response completion payload")
    total_tokens: int = Field(..., description="Aggregated total tokens processed")


class AITestResponse(BaseModel):
    """Orchestrated response metrics for prompt generation testing"""
    response: str = Field(..., description="LLM generated string response text")
    model: str = Field(..., description="Specific model utilized during prompt processing")
    token_usage: TokenUsage = Field(..., description="Detailed token consumption figures")
    latency: float = Field(..., description="Roundtrip processing time in milliseconds")
    finish_reason: str = Field(..., description="Execution boundary completion condition (e.g. stop, length)")


class AIExecutionSession(BaseModel):
    """Telemetry log session tracking AI orchestrator query details"""
    request_id: str = Field(..., description="Unique trace identifier")
    user_id: Optional[str] = Field(None, description="Request caller user ID")
    patient_id: Optional[str] = Field(None, description="Target patient user ID context")
    model: str = Field(..., description="Configured model name utilized")
    start_time: datetime = Field(..., description="Pipeline execution start timestamp")
    end_time: datetime = Field(..., description="Pipeline execution end timestamp")
    duration: float = Field(..., description="Total elapsed pipeline execution duration in milliseconds")
    tokens: int = Field(..., description="Total token consumption count")
    cost: float = Field(..., description="Computed financial cost in USD")
    status: str = Field(..., description="Final status: success or failed")
    errors: Optional[str] = Field(None, description="Detailed stacktrace/message if failed")


class AIPlaygroundChatRequest(BaseModel):
    """Request query payload for AI integration chat testing"""
    prompt: str = Field(..., min_length=1, description="User query text")
    patient_id: Optional[str] = Field(None, description="Optional target patient ID for context compilation")
    model: Optional[str] = Field(None, description="Override LLM model name")
    temperature: Optional[float] = Field(None, description="LLM temperature override parameter")
    max_tokens: Optional[int] = Field(None, description="LLM max tokens limit parameter")


class AIPlaygroundChatResponse(BaseModel):
    """Response payload containing LLM output, execution session telemetry, and trace prompts details"""
    response: str = Field(..., description="Output content completed by the model")
    execution_session: AIExecutionSession = Field(..., description="Telemetry details of execution pipeline run")
    prompt_template: str = Field(..., description="Final compiled prompt payload sent to LLM")
    patient_context_sections: List[str] = Field(default_factory=list, description="List of patient context sections loaded")


class AIPlaygroundHealthResponse(BaseModel):
    """Consolidated health report checks mapping all AI infrastructure components"""
    groq: Dict[str, Any] = Field(..., description="Groq API connection status details")
    embedding: Dict[str, Any] = Field(..., description="Embedding engine status details")
    vector: Dict[str, Any] = Field(..., description="Vector database client health details")
    prompt_registry: Dict[str, Any] = Field(..., description="Prompt templates file configuration status details")
    context_builder: Dict[str, Any] = Field(..., description="Context compiler DB connectivity details")


class DocumentIndexRequest(BaseModel):
    """Request model for indexing a document"""
    document_id: str = Field(..., description="MongoDB ID of the parent document")
    document_type: str = Field(..., description="String category (e.g. REPORT, MEDICAL_ARTICLE, DRUG_DATASET, DOCTOR_PROFILE, CHAT_MEMORY)")
    content: str = Field(..., min_length=1, description="Raw text content of the document")
    chunking_strategy: Optional[str] = Field("fixed", description="Chunking strategy: fixed, paragraph, sliding_window")
    chunk_size: Optional[int] = Field(1000, description="Chunk characters size limit")
    overlap: Optional[int] = Field(100, description="Overlap characters size limit")
    patient_id: Optional[str] = Field(None, description="Patient user ID link")
    report_id: Optional[str] = Field(None, description="Report ID link")
    page_number: Optional[int] = Field(1, description="Page number of document chunk")
    section: Optional[str] = Field("content", description="Section label of chunk")
    source: Optional[str] = Field("mongodb", description="Source system identifier")
    language: Optional[str] = Field("en", description="Locale language label")
    created_by: Optional[str] = Field("system", description="Identifier of creation agent")


class DocumentIndexResponse(BaseModel):
    """Response model representing indexing outcome of a document"""
    success: bool = Field(..., description="Indicates if indexing was successful or skipped")
    document_id: str = Field(..., description="The ID of the indexed document")
    status: str = Field(..., description="The outcome status: 'indexed', 'skipped', or 'failed'")
    chunks_count: int = Field(..., description="Number of chunks successfully indexed in Qdrant")
    skipped_count: Optional[int] = Field(0, description="Number of chunks skipped due to duplicates")
    latency_ms: Optional[float] = Field(0.0, description="Processing duration in milliseconds")
    message: Optional[str] = Field(None, description="Detailed explanation of the outcome")
    error: Optional[str] = Field(None, description="Error message if status is 'failed'")


class BatchDocumentIndexRequest(BaseModel):
    """Request model for indexing multiple documents in a batch"""
    documents: List[DocumentIndexRequest] = Field(..., description="List of documents to index")


class BatchDocumentIndexResponse(BaseModel):
    """Response model containing batch outcomes"""
    results: List[DocumentIndexResponse] = Field(..., description="Outcomes for all documents processed in batch")


class IndexingStatisticsResponse(BaseModel):
    """Response model containing metrics of the indexing pipeline"""
    indexed_documents: int = Field(..., description="Total count of successfully indexed documents")
    indexed_chunks: int = Field(..., description="Total count of vectorized chunks in vector store")
    duplicate_documents_skipped: int = Field(..., description="Count of duplicate documents skipped")
    avg_chunk_size: float = Field(..., description="Average character count of generated text chunks")
    embedding_version: str = Field(..., description="Currently active embedding model configuration version")
    index_version: int = Field(..., description="Currently active vector index structure version")
    schema_version: int = Field(..., description="Currently active collection database schema layout version")


class IndexDeletionResponse(BaseModel):
    """Response model indicating completion of a deletion operation"""
    success: bool = Field(..., description="Indicates if the delete operation completed successfully")
    message: Optional[str] = Field(None, description="Detailed explanation of the outcome")


class SyncStatusResponse(BaseModel):
    """Active queue status monitoring telemetry details"""
    running: bool = Field(..., description="Queue worker thread pool execution status")
    queue_size: int = Field(..., description="Number of items currently queued in memory")
    dlq_count: int = Field(..., description="Total size count of dead-letter jobs failures")


class SyncPatientResponse(BaseModel):
    """Outcomes detailed report generated from individual patient rebuild execution"""
    success: bool = Field(..., description="Whether synchronization was completed successfully")
    patient_id: str = Field(..., description="Target patient ID context")
    rebuilt_mongodb: bool = Field(..., description="Indicates if MongoDB patient summary was recalculated and updated")
    regenerated_qdrant: bool = Field(..., description="Indicates if vectors were recalculated and upserted to Qdrant")
    summary_version: int = Field(..., description="The summary version number mapped to this synchronization run")
    latency_ms: float = Field(..., description="Computed execution duration time in milliseconds")


class SyncRebuildResponse(BaseModel):
    """Consolidated report metrics of triggering background full platform synchronization rebuild"""
    success: bool = Field(..., description="Trigger status of global synchronization rebuild pipeline")
    triggered_count: int = Field(..., description="Total number of active patient summaries queued for background update")
    patient_ids: List[str] = Field(..., description="List of target patient user IDs queued for processing")


class SyncStatisticsResponse(BaseModel):
    """Response mapping telemetry metrics matching MemorySyncMetricsTracker"""
    sync_count: int = Field(..., description="Total completed synchronization runs count")
    failures: int = Field(..., description="Total counted sync task failures")
    retries: int = Field(..., description="Number of task execution retry attempts")
    dead_letters: int = Field(..., description="Total number of jobs transferred to dead-letter queue")
    avg_latency_ms: float = Field(..., description="Average processing runtime duration in milliseconds")
    rebuilt_summaries: int = Field(..., description="Count of updated MongoDB summary documents")
    vectors_regenerated: int = Field(..., description="Count of updated/regenerated collections vectors")
    vectors_skipped: int = Field(..., description="Count of skips utilizing content hash matches")


class DrugMasterModel(BaseModel):
    """Schema representing a drug entry in the drug master catalog"""
    drug_name: str = Field(..., description="Display/canonical name of the drug")
    normalized_name: str = Field(..., description="Cleaned, lowercase normalized name")
    aliases: List[str] = Field(default_factory=list, description="Alternative names mapping to this drug")
    source_dataset: str = Field(..., description="Source of the drug data (e.g. ddinter)")


class DrugLookupResponse(BaseModel):
    """Response schema for drug lookup queries"""
    exists: bool = Field(..., description="Indicates if the drug exists in catalog")
    matched_drug: Optional[DrugMasterModel] = Field(None, description="Detailed drug catalog info if found")
    normalized_name: str = Field(..., description="Cleaned, normalized version of lookup query")
    lookup_source: str = Field(..., description="Source of lookup: database, cache, or none")
    confidence: float = Field(..., description="Confidence score of resolution: 1.0 (exact), 0.9 (alias), 0.0 (not found)")
    latency_ms: float = Field(..., description="Internal lookup execution time in milliseconds")


class DrugNormalizeRequest(BaseModel):
    """Request schema to normalize a drug string"""
    drug_name: str = Field(..., min_length=1, description="Raw drug string to normalize")


class DrugNormalizeResponse(BaseModel):
    """Response schema containing the normalized drug string"""
    normalized_name: str = Field(..., description="Normalized drug string output")


class DrugTelemetryResponse(BaseModel):
    """Response schema for drug safety lookup telemetry stats"""
    total_lookups: int = Field(..., description="Total lookups executed")
    cache_hits: int = Field(..., description="Cache hits counted")
    cache_misses: int = Field(..., description="Cache misses counted")
    cache_hit_ratio: float = Field(..., description="Cache hits over total lookups ratio")
    avg_latency_ms: float = Field(..., description="Running average lookup latency in milliseconds")
    unknown_drug_count: int = Field(..., description="Count of unknown drug lookups")
    normalization_count: int = Field(..., description="Count of normalizations executed")
    
    # Interaction stats
    interaction_checks: int = Field(..., description="Count of interaction checks executed")
    pairs_evaluated: int = Field(..., description="Count of medication pairs evaluated")
    interaction_avg_latency_ms: float = Field(..., description="Running average interaction check latency in milliseconds")
    severity_distribution: Dict[str, int] = Field(..., description="Frequency counts of overall severity levels detected")
    
    # Validation stats
    validation_checks: int = Field(..., description="Count of validation queries executed")
    validation_avg_latency_ms: float = Field(..., description="Running average validation check latency in milliseconds")
    reminder_validations: int = Field(..., description="Count of validations from reminders")
    prescription_validations: int = Field(..., description="Count of validations from prescriptions")
    report_validations: int = Field(..., description="Count of validations from clinical reports")
    patient_memory_validations: int = Field(..., description="Count of validations from patient memory summary builds")
    other_validations: int = Field(..., description="Count of validations from other sources")
    allow_decisions: int = Field(..., description="Count of ALLOW decisions returned")
    warning_decisions: int = Field(..., description="Count of WARNING decisions returned")
    blocked_decisions: int = Field(..., description="Count of BLOCK decisions returned")


from app.services.drug_safety.models import DrugCheckRequest, DrugCheckResponse, InteractionPairDetail


class MedicationValidateRequest(BaseModel):
    """Request schema to validate incoming medications against a patient's context"""
    patient_id: str = Field(..., description="Patient identifier to evaluate against")
    incoming_medications: List[str] = Field(..., description="List of raw medication names to validate")


class MedicationValidateResponse(BaseModel):
    """Response schema containing validation results and interactions"""
    collected_medications: List[str] = Field(..., description="List of currently active patient medications")
    detected_interactions: List[InteractionPairDetail] = Field(..., description="Matched drug-drug interactions")
    severity: str = Field(..., description="Overall severity of the validation check")
    decision: str = Field(..., description="Evaluation decision: ALLOW, WARNING, or BLOCK")
    recommendations: List[str] = Field(..., description="Actionable health recommendations")
    latency_ms: float = Field(..., description="Validation query execution time in milliseconds")


class DrugAIExplanationTokenUsage(BaseModel):
    """Token usage metrics"""
    prompt_tokens: int = Field(..., description="Number of prompt tokens")
    completion_tokens: int = Field(..., description="Number of completion tokens")
    total_tokens: int = Field(..., description="Total tokens used")


class DrugAIExplanationResponse(BaseModel):
    """Response schema for drug safety explanations generated by AI"""
    severity: str = Field(..., description="Highest detected interaction severity")
    deterministic_recommendation: List[str] = Field(..., description="Predefined safety recommendations")
    patient_explanation: str = Field(..., description="Simple, patient-friendly narrative explanation")
    doctor_explanation: str = Field(..., description="Professional clinical narrative explanation")
    precautions: str = Field(..., description="Bullet list of medication precautions")
    summary: str = Field(..., description="Concise interaction summary statement")
    citations: Optional[List[str]] = Field(None, description="Citations or reference sources")
    fallback_used: bool = Field(..., description="Indicates if deterministic fallback was triggered")
    latency_ms: float = Field(..., description="Total pipeline execution latency in milliseconds")
    token_usage: DrugAIExplanationTokenUsage = Field(..., description="AI model token usage details")
    estimated_cost: float = Field(..., description="Estimated cost of AI inference in USD")


class DrugAITelemetryResponse(BaseModel):
    """Response schema for Drug AI explanation telemetry metrics"""
    explanation_requests: int = Field(..., description="Total generation requests triggered")
    successful_generations: int = Field(..., description="Successful AI generations completed")
    fallback_executions: int = Field(..., description="Fallback generations completed due to exceptions")
    prompt_tokens: int = Field(..., description="Prompt tokens consumed")
    completion_tokens: int = Field(..., description="Completion tokens consumed")
    total_tokens: int = Field(..., description="Total tokens consumed")
    estimated_cost: float = Field(..., description="Total cumulative API cost in USD")
    avg_latency_ms: float = Field(..., description="Running average generation latency in milliseconds")
    model_usage: Dict[str, int] = Field(..., description="Distribution of models used")


class DrugPatientSafetyResponse(BaseModel):
    """Response schema for patient drug safety view"""
    active_medications: List[str] = Field(..., description="List of patient active medications")
    interactions: List[Dict[str, Any]] = Field(..., description="Detected interaction details")
    severity: str = Field(..., description="Overall safety severity level")
    patient_explanation: str = Field(..., description="AI patient-friendly explanation")


class DrugDoctorSafetyResponse(BaseModel):
    """Response schema for doctor drug safety view"""
    interaction_details: List[Dict[str, Any]] = Field(..., description="Details of detected interactions")
    doctor_explanation: str = Field(..., description="AI clinician-focused explanation")
    monitoring_advice: str = Field(..., description="Precautions and clinical monitoring indicators")
    recommendations: List[str] = Field(..., description="Actionable health recommendations")


class DrugValidationHistoryItem(BaseModel):
    """Schema representing an item in validation history log"""
    id: str = Field(..., description="History item ID")
    patient_id: str = Field(..., description="Target patient ID")
    incoming_medications: List[str] = Field(default_factory=list, description="Incoming medications tested")
    collected_medications: List[str] = Field(default_factory=list, description="Baseline medications at test time")
    decision: str = Field(..., description="Validation decision outcome: ALLOW, WARNING, BLOCK")
    severity: str = Field(..., description="Detected severity classification")
    recommendations: List[str] = Field(default_factory=list)
    detected_interactions: List[Dict[str, Any]] = Field(default_factory=list)
    source: str = Field(..., description="Validation origin source (api, reminder, prescription, sync)")
    override_reason: Optional[str] = None
    overridden_by: Optional[str] = None
    latency_ms: float = Field(0.0)
    created_at: datetime


class DrugDashboardStatisticsResponse(BaseModel):
    """Response schema for drug safety dashboard stats"""
    validations: int = Field(..., description="Total validation checks executed")
    active_warnings: int = Field(..., description="Total warning decisions recorded")
    blocked_interactions: int = Field(..., description="Total block decisions recorded")
    overrides: int = Field(..., description="Total overrides authorized")
    highest_severity_distribution: Dict[str, int] = Field(..., description="Distribution of high/medium/low severity levels")
    avg_latency_ms: float = Field(..., description="Average latency of validation operations")









