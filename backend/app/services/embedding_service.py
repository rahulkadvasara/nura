"""
Nura - Embedding Service
Service for lazy-loading embedding models, validating inputs, processing batches, and checking engine health.
"""

import time
import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Any, Set
import logging

from app.core.ai_config import AISettings, ai_settings
from app.core.exceptions import (
    EmbeddingConfigurationError,
    EmbeddingValidationError,
    EmbeddingError
)
from app.schemas.embedding import EmbeddingResult, EmbeddingMetadata
from app.utils.ai import embedding_metrics
from app.utils.hash import generate_content_hash

logger = logging.getLogger("nura.ai.embeddings")


class EmbeddingService:
    """Service wrapper for generating document vector embeddings"""
    
    def __init__(self, settings: AISettings = ai_settings):
        self.settings = settings
        self.settings.validate_config()
        self._model = None
        self._global_seen_hashes: Set[str] = set()

    @property
    def model(self) -> Any:
        """Lazy load SentenceTransformer model to keep startup snappy"""
        if self._model is None:
            if self.settings.EMBEDDING_PROVIDER == "local":
                from sentence_transformers import SentenceTransformer
                try:
                    logger.info(f"Loading local SentenceTransformer model: {self.settings.EMBEDDING_MODEL}")
                    self._model = SentenceTransformer(self.settings.EMBEDDING_MODEL)
                except Exception as e:
                    logger.error(f"Failed to load embedding model: {str(e)}")
                    raise EmbeddingConfigurationError(f"Failed to initialize embedding model: {str(e)}") from e
            else:
                raise EmbeddingConfigurationError(f"Unsupported embedding provider: {self.settings.EMBEDDING_PROVIDER}")
        return self._model

    def validate_text(self, text: str) -> None:
        """Validate input text against validation constraints"""
        if not text or text.strip() == "":
            raise EmbeddingValidationError("Text content for embedding generation cannot be empty")
        
        # Enforce maximum text size (e.g. 10000 characters)
        MAX_TEXT_SIZE = 10000
        if len(text) > MAX_TEXT_SIZE:
            raise EmbeddingValidationError(
                f"Text content size ({len(text)} characters) exceeds maximum size of {MAX_TEXT_SIZE} characters"
            )

    def validate_vector(self, vector: List[float]) -> bool:
        """Confirm generated vector dimensions match settings profile"""
        if not vector or not isinstance(vector, list):
            raise EmbeddingValidationError("Generated vector is empty or is not a list of floats")
        if len(vector) != self.settings.EMBEDDING_DIMENSIONS:
            raise EmbeddingValidationError(
                f"Embedding vector dimension mismatch. Expected {self.settings.EMBEDDING_DIMENSIONS}, got {len(vector)}"
            )
        return True

    def normalize_vector(self, vector: List[float]) -> List[float]:
        """Normalize embedding vector using L2 normalization"""
        import math
        norm = math.sqrt(sum(x * x for x in vector))
        if norm == 0.0:
            return vector
        return [x / norm for x in vector]

    async def embed(self, text: str) -> List[float]:
        """Generate normalized vector embedding for a single text string"""
        self.validate_text(text)
        
        # Check Cache
        from app.services.rag_cache_service import get_rag_cache_service
        cache_svc = get_rag_cache_service()
        cached = cache_svc.get_embedding(text)
        if cached is not None:
            return cached

        start_time = time.perf_counter()
        try:
            vectors = await self._generate_embeddings([text])
            vector = vectors[0]
            self.validate_vector(vector)
            
            latency = (time.perf_counter() - start_time) * 1000.0
            embedding_metrics.record_success(count=1, latency_ms=latency, batch_size=1)
            
            cache_svc.set_embedding(text, vector)
            return vector
        except Exception as e:
            embedding_metrics.record_failure(count=1)
            if not isinstance(e, EmbeddingValidationError):
                raise EmbeddingError(f"Embedding generation failed: {str(e)}") from e
            raise e

    async def embed_batch(
        self,
        texts: List[str],
        document_type: str,
        source_id: str,
        collection_target: str,
        patient_id: Optional[str] = None,
        batch_size: Optional[int] = None,
        progress_callback: Optional[Any] = None
    ) -> List[EmbeddingResult]:
        """Generate batch embeddings with duplicate detection, automatic splitting and retries"""
        if not texts:
            return []

        target_batch_size = batch_size or self.settings.EMBEDDING_BATCH_SIZE
        results: List[Optional[EmbeddingResult]] = [None] * len(texts)
        
        # Perform preprocessing, input validation, and duplicate filtering
        unique_texts_to_process: List[str] = []
        unique_text_indices: List[int] = []
        
        from app.services.rag_cache_service import get_rag_cache_service
        cache_svc = get_rag_cache_service()
        
        for idx, text in enumerate(texts):
            try:
                self.validate_text(text)
            except EmbeddingValidationError as e:
                # Track failed item and propagate error
                embedding_metrics.record_failure(count=1)
                raise e

            # Check Embedding Cache First
            cached_vector = cache_svc.get_embedding(text)
            if cached_vector is not None:
                metadata = EmbeddingMetadata(
                    content_hash=generate_content_hash(text),
                    embedding_model=self.settings.EMBEDDING_MODEL,
                    embedding_version=self.settings.EMBEDDING_VERSION,
                    indexed_at=datetime.now(timezone.utc),
                    document_type=document_type,
                    source_id=source_id,
                    patient_id=patient_id,
                    collection_target=collection_target
                )
                results[idx] = EmbeddingResult(
                    vector=cached_vector,
                    text=text,
                    metadata=metadata
                )
                continue

            content_hash = generate_content_hash(text)
            
            # Check for duplicate
            if content_hash in self._global_seen_hashes:
                embedding_metrics.record_duplicate()
                metadata = EmbeddingMetadata(
                    content_hash=content_hash,
                    embedding_model=self.settings.EMBEDDING_MODEL,
                    embedding_version=self.settings.EMBEDDING_VERSION,
                    indexed_at=datetime.now(timezone.utc),
                    document_type=document_type,
                    source_id=source_id,
                    patient_id=patient_id,
                    collection_target=collection_target
                )
                results[idx] = EmbeddingResult(
                    vector=[0.0] * self.settings.EMBEDDING_DIMENSIONS,
                    text=text,
                    metadata=metadata
                )
            else:
                self._global_seen_hashes.add(content_hash)
                unique_texts_to_process.append(text)
                unique_text_indices.append(idx)

        # Process the unique texts in batches
        processed_count = 0
        for i in range(0, len(unique_texts_to_process), target_batch_size):
            batch_texts = unique_texts_to_process[i:i + target_batch_size]
            
            start_time = time.perf_counter()
            retries = 3
            success = False
            batch_vectors = []
            
            while retries > 0 and not success:
                try:
                    # Timeout handling is integrated into model parameters or asyncio
                    batch_vectors = await asyncio.wait_for(
                        self._generate_embeddings(batch_texts),
                        timeout=self.settings.TIMEOUT_SECONDS
                    )
                    success = True
                except Exception as e:
                    retries -= 1
                    if retries == 0:
                        embedding_metrics.record_failure(count=len(batch_texts))
                        raise EmbeddingError(f"Batch embedding generation failed after retries: {str(e)}") from e
                    await asyncio.sleep(1.0)
            
            latency = (time.perf_counter() - start_time) * 1000.0
            embedding_metrics.record_success(count=len(batch_texts), latency_ms=latency, batch_size=len(batch_texts))

            # Map the generated vectors back
            for j, vector in enumerate(batch_vectors):
                global_idx = unique_text_indices[i + j]
                txt = batch_texts[j]
                norm_vector = self.normalize_vector(vector)
                self.validate_vector(norm_vector)
                
                cache_svc.set_embedding(txt, norm_vector)
                
                content_hash = generate_content_hash(txt)
                metadata = EmbeddingMetadata(
                    content_hash=content_hash,
                    embedding_model=self.settings.EMBEDDING_MODEL,
                    embedding_version=self.settings.EMBEDDING_VERSION,
                    indexed_at=datetime.now(timezone.utc),
                    document_type=document_type,
                    source_id=source_id,
                    patient_id=patient_id,
                    collection_target=collection_target
                )
                
                results[global_idx] = EmbeddingResult(
                    vector=norm_vector,
                    text=txt,
                    metadata=metadata
                )
                
            processed_count += len(batch_texts)
            if progress_callback:
                progress_callback(processed_count + (len(texts) - len(unique_texts_to_process)), len(texts))

        return results

    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Run encoding inside threadpool to keep event loop free, wrapped in a circuit breaker"""
        from app.utils.circuit_breaker import get_circuit_breaker
        
        def fallback_embeddings(texts_list: List[str]) -> List[List[float]]:
            logger.error("Embedding circuit breaker fallback triggered. Returning dummy vectors.")
            return [[0.0] * self.settings.EMBEDDING_DIMENSIONS for _ in texts_list]

        cb = get_circuit_breaker("embedding_service", fallback_func=fallback_embeddings)
        
        async def do_generate():
            loop = asyncio.get_running_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self.model.encode(texts, normalize_embeddings=True)
            )
            return [v.tolist() for v in embeddings]

        return await cb.execute_async(do_generate, texts)

    async def health_check(self) -> dict:
        """Health check validation of embedding engine"""
        import time
        from datetime import datetime, timezone
        
        start_time = time.perf_counter()
        try:
            self.settings.validate_config()
            # Direct generation check
            vector = await self.embed("health check")
            latency = (time.perf_counter() - start_time) * 1000.0
            return {
                "provider": self.settings.EMBEDDING_PROVIDER,
                "model": self.settings.EMBEDDING_MODEL,
                "dimensions": self.settings.EMBEDDING_DIMENSIONS,
                "latency": latency,
                "status": "healthy"
            }
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"Embedding health check failed: {str(e)}")
            return {
                "provider": self.settings.EMBEDDING_PROVIDER,
                "model": self.settings.EMBEDDING_MODEL,
                "dimensions": self.settings.EMBEDDING_DIMENSIONS,
                "latency": latency,
                "status": "unhealthy",
                "error": str(e)
            }


# Singleton reference cache
_embedding_service_instance: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Retrieve singleton instance of EmbeddingService"""
    global _embedding_service_instance
    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService(settings=ai_settings)
    return _embedding_service_instance
