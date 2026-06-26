"""
Nura - Vector Schemas
Pydantic schemas for vector database operations, collection management, and health checks
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class VectorMetadata(BaseModel):
    """Standardized metadata structure stored inside the vector database payload for every point"""
    source_id: str = Field(..., description="Document primary key or database link ID")
    patient_id: Optional[str] = Field(None, description="Optional patient link ID if patient-specific")
    document_type: str = Field(..., description="Type of document, e.g. report, clinical_note, chat_memory")
    collection: str = Field(..., description="Target Qdrant collection name")
    embedding_model: str = Field(..., description="Embedding model identifier used to encode the vector")
    embedding_version: str = Field(..., description="Version tag of the embedding generation schema")
    indexed_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when vector was indexed")
    content_hash: str = Field(..., description="SHA-256 fingerprint hash of original text content")
    tags: List[str] = Field(default_factory=list, description="List of filterable tags associated with point")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class VectorCollectionInfo(BaseModel):
    """Collection configurations and telemetry statistics info"""
    name: str = Field(..., description="Name of Qdrant collection")
    status: str = Field(..., description="Status (green, yellow, red or healthy/unhealthy)")
    vector_count: int = Field(..., description="Number of vector points in the collection")
    dimensions: int = Field(..., description="Vector dimensions count configured")
    distance: str = Field(..., description="Distance comparison metric (COSINE, DOT, EUCLID)")
    storage_bytes: Optional[int] = Field(None, description="Storage size on disk if available")
    last_update_time: Optional[datetime] = Field(None, description="Timestamp of last point write/deletion")


class VectorHealthResponse(BaseModel):
    """Overall vector database health and connectivity status"""
    connected: bool = Field(..., description="Is client connection successfully established")
    latency: float = Field(..., description="Client roundtrip health ping latency in milliseconds")
    collections: List[VectorCollectionInfo] = Field(..., description="List of health status for all five collections")


class VectorTestRequest(BaseModel):
    """Payload to trigger vector infrastructure execution verification tests"""
    collection: str = Field(..., description="Target collection name to perform test pipeline against")
    text: str = Field(..., min_length=1, description="Raw text query to generate vector and run search tests")


class VectorTestResultItem(BaseModel):
    """Single match item returned from test search nearest neighbors"""
    id: str = Field(..., description="Vector point ID")
    score: float = Field(..., description="Cosine similarity score calculated")
    payload: Dict[str, Any] = Field(..., description="Raw point metadata dictionary")


class VectorTestResponse(BaseModel):
    """Vector database CRUD pipeline verification outcome details"""
    latency: float = Field(..., description="Total processing latency in milliseconds")
    search_results: List[VectorTestResultItem] = Field(..., description="Returned near-neighbor points listing")
    similarity_scores: List[float] = Field(..., description="Similarity scores for matching results")
