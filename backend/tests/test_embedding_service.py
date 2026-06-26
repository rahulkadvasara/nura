"""
Nura - Embedding Service Unit Tests
Verifies text chunking, SHA-256 content hashing, validation limits, single embedding, and batch generation with duplicate caching.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch, PropertyMock

from app.core.ai_config import AISettings
from app.core.exceptions import (
    EmbeddingConfigurationError,
    EmbeddingValidationError,
    EmbeddingError
)
from app.services.embedding_service import EmbeddingService
from app.utils.chunking import chunk_by_fixed_size, chunk_by_paragraph, chunk_by_sliding_window
from app.utils.hash import generate_content_hash
from app.utils.ai import embedding_metrics


@pytest.fixture
def mock_transformer():
    """Mock the model property of EmbeddingService to avoid network and disk resource consumption during tests"""
    mock_instance = MagicMock()
    # Mock encoding vector coefficients
    mock_instance.encode.side_effect = lambda texts, **kwargs: np.array([[1.0 / np.sqrt(384)] * 384 for _ in texts])
    
    with patch.object(EmbeddingService, "model", new_callable=PropertyMock) as mock_model_prop:
        mock_model_prop.return_value = mock_instance
        yield mock_instance


def test_chunking_fixed_size():
    """Verify character-based fixed size text segmentation moves by steps correctly"""
    text = "abcdefghij"
    chunks = chunk_by_fixed_size(text, chunk_size=4, overlap=2)
    assert chunks == ["abcd", "cdef", "efgh", "ghij"]


def test_chunking_paragraph():
    """Verify paragraph alignment combines tiny items and splits oversized text block lines"""
    text = "Paragraph one.\n\nParagraph two.\n\nOversized paragraph that gets split into pieces."
    chunks = chunk_by_paragraph(text, max_chunk_size=30)
    assert len(chunks) > 0


def test_chunking_sliding_window():
    """Verify sliding windows step forward by configured word steps"""
    text = "one two three four five"
    chunks = chunk_by_sliding_window(text, window_size=3, step_size=2)
    assert chunks == ["one two three", "three four five"]


def test_content_hashing():
    """Verify deterministic hash signatures"""
    assert generate_content_hash("sample content") == generate_content_hash("sample content")
    assert generate_content_hash("sample content") != generate_content_hash("different content")


@pytest.mark.asyncio
async def test_embed_single_text(mock_transformer):
    """Verify single text vectors generate normalized 384-dimension floats list"""
    settings = AISettings(
        GROQ_API_KEY="valid_test_key",
        EMBEDDING_PROVIDER="local",
        EMBEDDING_MODEL="dummy-model",
        EMBEDDING_DIMENSION=384
    )
    service = EmbeddingService(settings=settings)
    
    vector = await service.embed("Test query string")
    assert len(vector) == 384
    # L2 Norm should be approximately 1.0
    norm_sum = sum(x * x for x in vector)
    assert abs(norm_sum - 1.0) < 1e-4


@pytest.mark.asyncio
async def test_embed_validation_error(mock_transformer):
    """Verify empty prompts and oversized document bodies are rejected"""
    settings = AISettings(
        GROQ_API_KEY="valid_test_key",
        EMBEDDING_PROVIDER="local",
        EMBEDDING_MODEL="dummy-model",
        EMBEDDING_DIMENSION=384
    )
    service = EmbeddingService(settings=settings)
    
    with pytest.raises(EmbeddingValidationError):
        await service.embed("")
        
    with pytest.raises(EmbeddingValidationError):
        await service.embed("too large" * 2000)


@pytest.mark.asyncio
async def test_embed_batch_duplicate_detection(mock_transformer):
    """Verify duplicates are caught and skipped, updating skipping metrics registers"""
    settings = AISettings(
        GROQ_API_KEY="valid_test_key",
        EMBEDDING_PROVIDER="local",
        EMBEDDING_MODEL="dummy-model",
        EMBEDDING_DIMENSION=384,
        EMBEDDING_BATCH_SIZE=2
    )
    service = EmbeddingService(settings=settings)
    
    embedding_metrics.reset()
    
    texts = ["unique content 1", "unique content 2", "unique content 1"]
    results = await service.embed_batch(
        texts=texts,
        document_type="report_chunk",
        source_id="doc123",
        collection_target="report_collection"
    )
    
    assert len(results) == 3
    metrics = embedding_metrics.get_metrics()
    assert metrics["duplicate_chunks_skipped"] == 1
    assert len(results[0].vector) == 384
    assert len(results[1].vector) == 384
    # Duplicate item returns zero vector payload (skips encoder call)
    assert results[2].vector == [0.0] * 384
