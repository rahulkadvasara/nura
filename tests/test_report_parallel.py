"""
Tests for ParallelOCRProcessor, ParallelEmbeddingProcessor, BatchQdrantUpserter.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.report_background.parallel_processor import (
    ParallelOCRProcessor,
    ParallelEmbeddingProcessor,
    BatchQdrantUpserter,
)


# ─────────────────────────────────────────────────────────────────────────────
# ParallelOCRProcessor
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_parallel_ocr_all_pages_processed():
    """All coroutines passed to process_pages_parallel are awaited and results returned."""
    call_count = 0

    async def fake_page_task(page_num):
        nonlocal call_count
        call_count += 1
        return {"page": page_num, "text": f"text from page {page_num}"}

    processor = ParallelOCRProcessor(max_concurrency=4)
    tasks = [fake_page_task(i) for i in range(8)]
    results = await processor.process_pages_parallel(tasks)

    assert len(results) == 8
    assert call_count == 8


@pytest.mark.asyncio
async def test_parallel_ocr_handles_partial_failures():
    """Exceptions in individual page tasks are captured, not propagated to caller."""

    async def good_task():
        return "ok"

    async def bad_task():
        raise RuntimeError("OCR hardware timeout")

    processor = ParallelOCRProcessor(max_concurrency=2)
    tasks = [good_task(), bad_task(), good_task()]
    results = await processor.process_pages_parallel(tasks)

    # All results are returned (exceptions wrapped)
    assert len(results) == 3
    errors = [r for r in results if isinstance(r, Exception)]
    assert len(errors) == 1


@pytest.mark.asyncio
async def test_parallel_ocr_respects_concurrency_limit():
    """At most max_concurrency tasks run simultaneously."""
    concurrent_peak = 0
    current_running = 0

    async def tracked_task():
        nonlocal concurrent_peak, current_running
        current_running += 1
        concurrent_peak = max(concurrent_peak, current_running)
        await asyncio.sleep(0.02)
        current_running -= 1
        return "done"

    max_conc = 3
    processor = ParallelOCRProcessor(max_concurrency=max_conc)
    tasks = [tracked_task() for _ in range(9)]
    await processor.process_pages_parallel(tasks)

    assert concurrent_peak <= max_conc


# ─────────────────────────────────────────────────────────────────────────────
# ParallelEmbeddingProcessor
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_parallel_embedding_all_chunks_embedded():
    """All text chunks are embedded and returned in original order."""
    mock_embedding_service = MagicMock()
    call_count = 0

    async def fake_embed(text):
        nonlocal call_count
        call_count += 1
        return [float(ord(c)) for c in text[:3]]

    mock_embedding_service.embed_text = fake_embed

    processor = ParallelEmbeddingProcessor(
        embedding_service=mock_embedding_service,
        max_concurrency=8,
        cache_service=None,
    )
    chunks = ["chunk A", "chunk B", "chunk C", "chunk D"]
    results = await processor.embed_chunks(chunks)

    assert len(results) == 4
    assert call_count == 4


@pytest.mark.asyncio
async def test_parallel_embedding_uses_cache_on_hit():
    """If cache returns a vector, embedding_service is not called for that chunk."""
    mock_service = MagicMock()
    mock_service.embed_text = AsyncMock()

    mock_cache = MagicMock()
    mock_cache.get_embedding = MagicMock(return_value=[0.5, 0.5, 0.5])
    mock_cache.set_embedding = MagicMock()

    processor = ParallelEmbeddingProcessor(
        embedding_service=mock_service,
        max_concurrency=4,
        cache_service=mock_cache,
    )
    results = await processor.embed_chunks(["cached text chunk"])

    # Cache hit — embedding service should not be called
    mock_service.embed_text.assert_not_called()
    assert results[0] == [0.5, 0.5, 0.5]


@pytest.mark.asyncio
async def test_parallel_embedding_stores_result_in_cache():
    """Newly computed embedding is stored in cache after computation."""
    vector = [0.1, 0.2, 0.3]

    mock_service = MagicMock()
    mock_service.embed_text = AsyncMock(return_value=vector)

    mock_cache = MagicMock()
    mock_cache.get_embedding = MagicMock(return_value=None)  # miss
    mock_cache.set_embedding = MagicMock()

    processor = ParallelEmbeddingProcessor(
        embedding_service=mock_service,
        max_concurrency=4,
        cache_service=mock_cache,
    )
    await processor.embed_chunks(["uncached text"])
    mock_cache.set_embedding.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# BatchQdrantUpserter
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_batch_qdrant_upserter_sends_correct_batches():
    """BatchQdrantUpserter splits points into correct batch sizes."""
    mock_vector_service = MagicMock()
    mock_vector_service.upsert_points = AsyncMock()

    upserter = BatchQdrantUpserter(vector_service=mock_vector_service, batch_size=3)
    points = [{"id": i, "vector": [float(i)]} for i in range(7)]
    result = await upserter.upsert_batched("patient_reports", points)

    # 7 points with batch_size=3 → 3 batches (3+3+1)
    assert mock_vector_service.upsert_points.call_count == 3
    assert result["total_points"] == 7
    assert result["batches_sent"] == 3
    assert result["failures"] == 0


@pytest.mark.asyncio
async def test_batch_qdrant_upserter_records_failures():
    """Upsert failures are counted but do not abort remaining batches."""
    mock_vector_service = MagicMock()
    call_count = 0

    async def failing_upsert(col, batch):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("Qdrant connection reset")

    mock_vector_service.upsert_points = failing_upsert

    upserter = BatchQdrantUpserter(vector_service=mock_vector_service, batch_size=5)
    points = [{"id": i} for i in range(10)]
    result = await upserter.upsert_batched("patient_reports", points)

    assert result["failures"] == 1
    assert result["batches_sent"] == 1  # second batch succeeded
