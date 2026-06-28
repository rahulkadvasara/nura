"""
Nura - Parallel OCR and Embedding Processor
Bounded concurrency for parallel page OCR and chunk embedding using asyncio.Semaphore.
Wraps existing DocumentParser and EmbeddingService — no business logic duplication.
"""

import asyncio
import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger("nura.report_background.parallel")

# Default concurrency limits
DEFAULT_OCR_CONCURRENCY = 4
DEFAULT_EMBEDDING_CONCURRENCY = 8
DEFAULT_QDRANT_BATCH_SIZE = 50


class ParallelOCRProcessor:
    """
    Processes multiple document pages in parallel using a bounded semaphore.
    Wraps the existing DocumentParser's page processing logic.
    """

    def __init__(self, max_concurrency: int = DEFAULT_OCR_CONCURRENCY):
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self.max_concurrency = max_concurrency

    async def process_pages_parallel(
        self,
        page_tasks: List[Coroutine],
    ) -> List[Any]:
        """
        Run a list of page coroutines in parallel, bounded by `max_concurrency`.
        Returns results in original order.
        """

        async def bounded(coro):
            async with self._semaphore:
                return await coro

        results = await asyncio.gather(
            *[bounded(task) for task in page_tasks],
            return_exceptions=True,
        )
        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            logger.warning(f"ParallelOCRProcessor: {len(errors)}/{len(page_tasks)} pages failed")
        return results


class ParallelEmbeddingProcessor:
    """
    Generates embeddings for multiple text chunks in parallel.
    Wraps existing EmbeddingService — no re-implementation.
    """

    def __init__(
        self,
        embedding_service,
        max_concurrency: int = DEFAULT_EMBEDDING_CONCURRENCY,
        cache_service=None,
    ):
        self.embedding_service = embedding_service
        self.cache_service = cache_service
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def embed_chunks(self, chunks: List[str]) -> List[Optional[List[float]]]:
        """
        Embed a list of text chunks in parallel, respecting the concurrency limit.
        Returns a list of embedding vectors in original order.
        Cache is checked before invoking the embedding API.
        """

        async def embed_one(text: str) -> Optional[List[float]]:
            # Check cache first
            if self.cache_service:
                cached = self.cache_service.get_embedding(text)
                if cached is not None:
                    return cached

            async with self._semaphore:
                try:
                    vector = await self.embedding_service.embed_text(text)
                    if self.cache_service and vector:
                        self.cache_service.set_embedding(text, vector)
                    return vector
                except Exception as e:
                    logger.error(f"Embedding failed for chunk: {e}")
                    return None

        return await asyncio.gather(*[embed_one(chunk) for chunk in chunks])


class BatchQdrantUpserter:
    """
    Batches Qdrant point upserts for efficiency instead of one-by-one inserts.
    Wraps existing VectorService — no re-implementation.
    """

    def __init__(self, vector_service, batch_size: int = DEFAULT_QDRANT_BATCH_SIZE):
        self.vector_service = vector_service
        self.batch_size = batch_size

    async def upsert_batched(
        self,
        collection_name: str,
        points: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Split `points` into batches of `batch_size` and upsert each batch sequentially.
        Returns a summary with total_points, batches_sent, failures.
        """
        total = len(points)
        batches_sent = 0
        failures = 0

        for i in range(0, total, self.batch_size):
            batch = points[i : i + self.batch_size]
            try:
                await self.vector_service.upsert_points(collection_name, batch)
                batches_sent += 1
                logger.debug(
                    f"BatchQdrantUpserter: upserted batch {batches_sent} "
                    f"({len(batch)} points) into {collection_name}"
                )
            except Exception as e:
                failures += 1
                logger.error(f"Batch upsert failed (batch {batches_sent + 1}): {e}")

        return {
            "total_points": total,
            "batches_sent": batches_sent,
            "failures": failures,
        }
