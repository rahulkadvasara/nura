"""
Nura - Embedding Schemas
Pydantic schemas representing embedding metadata, generation results, and test interfaces
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EmbeddingMetadata(BaseModel):
    """Structured metadata to be stored alongside generated embeddings inside the vector database"""
    content_hash: str = Field(..., description="Deterministically calculated SHA-256 hash of text block")
    embedding_model: str = Field(..., description="The name of the embedding model used")
    embedding_version: str = Field(..., description="Versioning identifier for incremental reindexing schema checks")
    indexed_at: datetime = Field(..., description="UTC creation timestamp")
    document_type: str = Field(..., description="Category of file, e.g. report, chat, clinical_note")
    source_id: str = Field(..., description="Document database primary key ID link")
    patient_id: Optional[str] = Field(None, description="Patient link if context is patient-specific")
    collection_target: str = Field(..., description="Target vector index collection name inside database")


class EmbeddingResult(BaseModel):
    """Consolidated response wrapper containing generated vector dimensions and standardized metadata"""
    vector: List[float] = Field(..., description="High-dimensional float vector coefficients list")
    text: str = Field(..., description="The original chunk text content representation")
    metadata: EmbeddingMetadata = Field(..., description="Standardized metadata associated with index chunk")


class EmbeddingHealthResponse(BaseModel):
    """Health check status details of the embedding subsystem"""
    provider: str = Field(..., description="Configured provider (local, openai, etc)")
    model: str = Field(..., description="Monitored embedding model identifier")
    dimensions: int = Field(..., description="Active embedding vector count resolution")
    latency: float = Field(..., description="Roundtrip processing check time in milliseconds")
    status: str = Field(..., description="General status (healthy or unhealthy)")


class EmbeddingTestRequest(BaseModel):
    """Payload to trigger embedding generation admin playground checks"""
    text: str = Field(..., min_length=1, description="Raw block to calculate vector representation")


class EmbeddingTestResponse(BaseModel):
    """Abridged playground results designed to prevent huge console payload logs"""
    dimensions: int = Field(..., description="Generated vector dimensional resolution")
    vector_preview: List[float] = Field(..., description="First few vector items representing the signature coefficients")
    latency: float = Field(..., description="Roundtrip execution speed in milliseconds")
    metadata: Dict[str, Any] = Field(..., description="Generated metadata structure logs")
