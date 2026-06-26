"""
Nura - Retrieval Schemas
Pydantic response and request models for semantic vector retrieval endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class RetrievalRequest(BaseModel):
    """Schema representing a request to query vector database collections semantically"""
    query: str = Field(..., min_length=1, description="Raw query string text for semantic search")
    collection: Optional[str] = Field(None, description="Single target collection name or document type category")
    collections: List[str] = Field(default_factory=list, description="Target collection names or document type categories")
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters to apply to search results")
    top_k: Optional[int] = Field(5, description="Maximum number of hits to return per collection query")
    score_threshold: Optional[float] = Field(None, description="Minimum score threshold for returned hits (range: [0.0, 1.0])")
    patient_id: Optional[str] = Field(None, description="Optional patient ID to target user clinical histories")
    intent: Optional[str] = Field(None, description="Optional intent category to override deterministic detection")


class RetrievalMatch(BaseModel):
    """Schema representing a single matched text chunk hit from the vector database"""
    collection: str = Field(..., description="Target Qdrant collection name where the point resides")
    id: str = Field(..., description="Unique point record uuid or string ID")
    score: float = Field(..., description="Normalized similarity score in range [0.0, 1.0]")
    content: str = Field(..., description="Raw text content of the chunk segment")
    metadata: Dict[str, Any] = Field(..., description="Standardized metadata dictionary of the chunk")
    document_type: str = Field(..., description="Unified document type mapping tag (e.g. REPORT)")
    patient_id: Optional[str] = Field(None, description="Optional patient ID if patient-specific link exists")
    report_id: Optional[str] = Field(None, description="Optional report ID link")
    citations: Dict[str, Any] = Field(default_factory=dict, description="Metadata attributes parsed for reference citations")


class RetrievalResponse(BaseModel):
    """Schema representing structured output results returned by semantic search"""
    results: List[RetrievalMatch] = Field(..., description="Ranked and merged retrieval results list")
    retrieval_time: float = Field(..., description="Consolidated query execution duration in milliseconds")
    collections_queried: List[str] = Field(..., description="List of Qdrant collections queried")
    chunks_found: int = Field(..., description="Aggregated count of vector chunks found before deduplication")
    duplicates_removed: int = Field(..., description="Count of duplicate chunks discarded during result ranking")


class RetrievalStatisticsResponse(BaseModel):
    """Schema representing aggregated metrics from the retrieval engine"""
    searches_executed: int = Field(..., description="Total count of searches executed")
    failed_searches: int = Field(..., description="Count of searches that failed or errored out")
    avg_latency_ms: float = Field(..., description="Average latency of searches in milliseconds")
    avg_score: float = Field(..., description="Average similarity score of returned hits")
    duplicate_chunks_removed: int = Field(..., description="Total count of duplicate chunks discarded")
    timeout_count: int = Field(..., description="Total count of search timeout occurrences")


class RetrievalPackage(BaseModel):
    """Schema representing the standard response package returned by the Retrieval Agent"""
    intent: str = Field(..., description="Detected retrieval intent category")
    collections_used: List[str] = Field(..., description="Collections queried for this retrieval session")
    retrieved_chunks: List[RetrievalMatch] = Field(..., description="Raw matching chunks retrieved before deduplication/ranking")
    context: str = Field(..., description="Assembled and ranked token-budgeted prompt context string")
    citations: Dict[str, Any] = Field(..., description="Citations mapping badge index keys to source metadata")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata for the retrieval process")
    latency: Dict[str, float] = Field(..., description="Latencies breakdown in milliseconds (retrieval, ranking, context, total)")
    scores: Dict[str, float] = Field(..., description="Map of chunk point IDs to similarity scores")
    cache_status: str = Field(..., description="Cache status of the request (hit or miss)")


class RetrievalAgentStatisticsResponse(BaseModel):
    """Schema representing aggregated metrics from the Retrieval Agent"""
    requests: int = Field(..., description="Total requests processed by the agent")
    failures: int = Field(..., description="Count of requests that failed or errored out")
    cache_hits: int = Field(..., description="Total cache hit count")
    cache_misses: int = Field(..., description="Total cache miss count")
    cache_hit_ratio: float = Field(..., description="Cache hit ratio in range [0.0, 1.0]")
    avg_retrieval_latency_ms: float = Field(..., description="Average collection retrieval latency in ms")
    avg_ranking_latency_ms: float = Field(..., description="Average chunk ranking latency in ms")
    avg_context_latency_ms: float = Field(..., description="Average context assembly latency in ms")
    avg_latency_ms: float = Field(..., description="Average total processing latency in ms")
    intent_counts: Dict[str, int] = Field(..., description="Intent counts distribution mapping")
    collection_usage: Dict[str, int] = Field(..., description="Collection query counts mapping")
