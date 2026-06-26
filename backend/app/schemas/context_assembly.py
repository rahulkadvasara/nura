"""
Nura - Context Assembly Schemas
Pydantic schemas for the context assembly service and endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ContextAssemblyRequest(BaseModel):
    """Request schema for context assembly"""
    query: str = Field(..., description="Query string for semantic search retrieval")
    patient_id: Optional[str] = Field(None, description="Optional patient ID to retrieve structured MongoDB context")
    token_budget: Optional[int] = Field(4000, description="Max token budget constraint for assembled context")
    collections: Optional[List[str]] = Field(None, description="Qdrant collections/document types to retrieve from")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional metadata filters for vector retrieval")


class ContextAssemblyResponse(BaseModel):
    """Response schema representing compiled prompt-ready context"""
    sections: Dict[str, str] = Field(..., description="Assembled text per category header")
    citations: Dict[str, Any] = Field(..., description="Mapping of citation ID to chunk source metadata")
    estimated_tokens: int = Field(..., description="Estimated token count of the final assembled context")
    compression_ratio: float = Field(..., description="Calculated compression ratio (assembled text size / original text size)")
    assembly_time: float = Field(..., description="Total execution duration of assembly process in milliseconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Operational and diagnostic metadata")


class ContextAssemblyStatisticsResponse(BaseModel):
    """Response schema for context assembly telemetry statistics"""
    assemblies_executed: int = Field(..., description="Total number of context assemblies run")
    failed_assemblies: int = Field(..., description="Total number of failed context assemblies")
    avg_latency_ms: float = Field(..., description="Average latency in milliseconds for assemblies")
    avg_compression_ratio: float = Field(..., description="Average compression ratio achieved")
    avg_tokens_assembled: float = Field(..., description="Average estimated tokens of assembled contexts")
    total_original_chunks: int = Field(..., description="Total count of original retrieved chunks")
    total_removed_chunks: int = Field(..., description="Total count of removed duplicate or pruned chunks")
    section_counts: Dict[str, int] = Field(default_factory=dict, description="Frequency counts of assembled sections")
