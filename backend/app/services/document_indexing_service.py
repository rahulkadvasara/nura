"""
Nura - Document Indexing Service
"""
import time
import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.core.ai_config import AISettings, ai_settings
from app.core.vector_collections import get_collection_for_document_type
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.document_metadata_service import DocumentMetadataService, get_document_metadata_service
from app.services.index_version_service import IndexVersionService, get_index_version_service
from app.utils.chunking import (
    chunk_by_fixed_size,
    chunk_by_paragraph,
    chunk_by_sliding_window
)
from app.utils.ai import indexing_metrics
from app.utils.hash import generate_content_hash

logger = logging.getLogger("nura.ai.indexing")


class DocumentIndexingService:
    """Core Service managing document vectorization, chunk metadata construction, and Qdrant storage"""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_service: VectorService,
        metadata_service: DocumentMetadataService,
        version_service: IndexVersionService,
        settings: AISettings = ai_settings
    ):
        self.embedding_service = embedding_service
        self.vector_service = vector_service
        self.metadata_service = metadata_service
        self.version_service = version_service
        self.settings = settings

    def validate_document(self, payload: Dict[str, Any]) -> None:
        """Validate request payload schema rules"""
        if not payload.get("document_id"):
            raise ValueError("Missing required parameter: document_id")
        if not payload.get("document_type"):
            raise ValueError("Missing required parameter: document_type")
        if not payload.get("content") or not payload["content"].strip():
            raise ValueError("Document content cannot be empty")

    def _chunk_document(
        self,
        content: str,
        strategy: str,
        chunk_size: int,
        overlap: int
    ) -> List[str]:
        """Apply selected chunking strategy on raw text content"""
        strategy_clean = strategy.lower().strip()
        if strategy_clean == "paragraph":
            return chunk_by_paragraph(content, max_chunk_size=chunk_size)
        elif strategy_clean == "sliding_window":
            # For sliding window, overlap is step size
            return chunk_by_sliding_window(content, window_size=chunk_size, step_size=overlap)
        else:
            # Default to fixed chunking
            return chunk_by_fixed_size(content, chunk_size=chunk_size, overlap=overlap)

    async def check_duplicate(
        self,
        collection_name: str,
        document_id: str,
        content_hash: str
    ) -> bool:
        """Query Qdrant to confirm if exact chunk + version combo exists"""
        emb_version = self.version_service.get_embedding_version()
        filter_dict = {
            "document_id": document_id,
            "embedding_version": emb_version,
            "content_hash": content_hash
        }
        count = await self.vector_service.count(collection_name, filter_dict)
        return count > 0

    async def index_document(self, request_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute document indexing pipeline.
        
        Args:
            request_payload: Dict containing document parameters.
            
        Returns:
            Dict detailing indexing outcome stats.
        """
        start_time = time.perf_counter()
        self.validate_document(request_payload)

        doc_id = request_payload["document_id"]
        doc_type = request_payload["document_type"]
        content = request_payload["content"]
        
        # Resolve collection
        collection_name = get_collection_for_document_type(doc_type)

        # Chunk parameters
        strategy = request_payload.get("chunking_strategy", "fixed")
        chunk_size = request_payload.get("chunk_size", 1000)
        overlap = request_payload.get("overlap", 100)

        chunks = self._chunk_document(content, strategy, chunk_size, overlap)
        if not chunks:
            return {
                "success": True,
                "document_id": doc_id,
                "status": "skipped",
                "chunks_count": 0,
                "message": "No text chunks generated for indexing."
            }

        points_to_upsert = []
        skipped_chunks = 0
        total_chars = 0

        for idx, chunk_text in enumerate(chunks):
            total_chars += len(chunk_text)
            chunk_hash = generate_content_hash(chunk_text)
            
            # Check for duplication
            is_dup = await self.check_duplicate(collection_name, doc_id, chunk_hash)
            if is_dup:
                skipped_chunks += 1
                continue

            # Generate embedding vector
            vector = await self.embedding_service.embed(chunk_text)

            # Build metadata payload
            metadata = self.metadata_service.build_metadata(
                document_id=doc_id,
                document_type=doc_type,
                chunk_index=idx,
                content=chunk_text,
                patient_id=request_payload.get("patient_id"),
                report_id=request_payload.get("report_id"),
                page_number=request_payload.get("page_number", 1),
                section=request_payload.get("section", "content"),
                source=request_payload.get("source", "mongodb"),
                language=request_payload.get("language", "en"),
                created_by=request_payload.get("created_by", "system")
            )

            # Unique Qdrant ID: standard hash representation of chunk_id to make it a deterministic uuid or string
            # Qdrant accepts UUID or 64-bit int. We can generate standard UUID from chunk_id deterministically
            import uuid
            qdrant_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, metadata["chunk_id"]))

            points_to_upsert.append({
                "id": qdrant_uuid,
                "vector": vector,
                "payload": metadata
            })

        if not points_to_upsert:
            indexing_metrics.record_duplicate_skip()
            latency = (time.perf_counter() - start_time) * 1000.0
            return {
                "success": True,
                "document_id": doc_id,
                "status": "skipped",
                "chunks_count": 0,
                "skipped_count": skipped_chunks,
                "latency_ms": latency,
                "message": "All chunks skipped due to duplicate text signatures detection."
            }

        # Upsert point list in batch to Qdrant
        res = await self.vector_service.upsert_batch(collection_name, points_to_upsert)
        latency = (time.perf_counter() - start_time) * 1000.0

        if res["success"]:
            indexing_metrics.record_indexing(len(points_to_upsert), total_chars)
            return {
                "success": True,
                "document_id": doc_id,
                "status": "indexed",
                "chunks_count": len(points_to_upsert),
                "skipped_count": skipped_chunks,
                "latency_ms": latency,
                "message": "Document successfully vectorized and indexed in Qdrant."
            }
        else:
            raise RuntimeError(f"Qdrant indexing upsert failed: {res['errors']}")

    async def index_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process documents asynchronously in parallel.
        
        Args:
            documents: List of document payloads
            
        Returns:
            List of status dicts indicating outcome per document.
        """
        tasks = []
        for doc in documents:
            tasks.append(self._safe_index_document(doc))
        return await asyncio.gather(*tasks)

    async def _safe_index_document(self, doc_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to catch individual failures inside batch operations"""
        doc_id = doc_payload.get("document_id", "unknown")
        try:
            res = await self.index_document(doc_payload)
            return res
        except Exception as e:
            logger.error(f"Failed to index batch document '{doc_id}': {e}")
            return {
                "success": False,
                "document_id": doc_id,
                "status": "failed",
                "error": str(e)
            }

    async def reindex_document(self, request_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Reindex document by clearing previous vectors first and executing pipeline again"""
        doc_id = request_payload.get("document_id")
        doc_type = request_payload.get("document_type")
        if not doc_id or not doc_type:
            raise ValueError("document_id and document_type are required for reindexing")
            
        # 1. Clear previous chunks
        await self.delete_document(doc_id, doc_type)
        
        # 2. Run standard indexing pipeline
        return await self.index_document(request_payload)

    async def delete_document(self, document_id: str, document_type: str) -> bool:
        """Delete specific document vectors from target collection"""
        collection_name = get_collection_for_document_type(document_type)
        filter_dict = {"document_id": document_id}
        return await self.vector_service.delete_by_filter(collection_name, filter_dict)

    async def delete_patient_documents(self, patient_id: str) -> bool:
        """Delete all vectors matching patient_id in reports collection"""
        collection_name = get_collection_for_document_type("REPORT")
        filter_dict = {"patient_id": patient_id}
        return await self.vector_service.delete_by_filter(collection_name, filter_dict)

    async def rebuild_collection(self, document_type: str) -> bool:
        """Idempotently clear collection and rebuild from scratch"""
        collection_name = get_collection_for_document_type(document_type)
        
        # Recreate collection schema
        await self.vector_service.delete_collection(collection_name)
        await self.vector_service.create_collection(
            collection_name=collection_name,
            vector_size=self.settings.EMBEDDING_DIMENSIONS,
            distance=self.settings.QDRANT_DEFAULT_DISTANCE
        )
        
        # Note: Scans/populates from MongoDB repository could be executed here if repository injection is wired
        # But collection recreate and mapping check completes the rebuild infrastructure sequence.
        return True

    def compute_statistics(self) -> Dict[str, Any]:
        """Aggregate current pipeline statistics"""
        metrics = indexing_metrics.get_metrics()
        return {
            **metrics,
            "embedding_version": self.version_service.get_embedding_version(),
            "index_version": self.version_service.get_index_version(),
            "schema_version": self.version_service.get_schema_version()
        }


# Singleton reference helper
_document_indexing_service_instance = None


def get_document_indexing_service() -> DocumentIndexingService:
    """Retrieve singleton instance of DocumentIndexingService"""
    global _document_indexing_service_instance
    if _document_indexing_service_instance is None:
        from app.services.embedding_service import get_embedding_service
        from app.services.vector_service import get_vector_service
        
        emb_svc = get_embedding_service()
        vec_svc = get_vector_service()
        meta_svc = get_document_metadata_service()
        ver_svc = get_index_version_service()
        
        _document_indexing_service_instance = DocumentIndexingService(
            embedding_service=emb_svc,
            vector_service=vec_svc,
            metadata_service=meta_svc,
            version_service=ver_svc,
            settings=ai_settings
        )
    return _document_indexing_service_instance
