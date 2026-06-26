"""
Nura - Unit tests for RetrievalEvaluationService
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.retrieval_evaluation_service import RetrievalEvaluationService

@pytest.fixture
def mock_retrieval_service():
    service = AsyncMock()
    # Mocking retrieval results:
    # 2 hits: 1 with score 0.85, 1 with score 0.65
    service.retrieve_multiple.return_value = {
        "results": [
            {
                "id": "pt1",
                "score": 0.85,
                "metadata": {
                    "document_id": "doc_abc",
                    "chunk_index": 0
                }
            },
            {
                "id": "pt2",
                "score": 0.65,
                "metadata": {
                    "document_id": "doc_xyz",
                    "chunk_index": 1
                }
            }
        ],
        "chunks_found": 3,
        "duplicates_removed": 1
    }
    return service

@pytest.fixture
def mock_context_assembly_service():
    service = AsyncMock()
    service.assemble.return_value = {
        "sections": {
            "section1": "content1",
            "section2": "content2"
        },
        "estimated_tokens": 1000
    }
    return service

@pytest.mark.asyncio
async def test_evaluate_query_metrics(mock_retrieval_service, mock_context_assembly_service):
    eval_service = RetrievalEvaluationService(
        retrieval_service=mock_retrieval_service,
        context_assembly_service=mock_context_assembly_service
    )

    # We set ground_truth_doc_ids to ["doc_abc"]
    # doc_abc is returned in results, doc_xyz is returned in results.
    # retrieved doc ids = {"doc_abc", "doc_xyz"}. Intersection is {"doc_abc"}. Overlap length = 1. Recall = 1/1 = 1.0.
    # relevant hits: hits with score >= 0.70. Only pt1 (0.85) is relevant. 1 relevant hit out of 2 total hits. Precision = 1/2 = 0.5.
    # citation quality: both hits have document_id and chunk_index. Quality = 2/2 = 1.0.
    # duplicate rate: duplicates_removed / (len(hits) + duplicates_removed) = 1 / (2 + 1) = 0.333.
    # context utilization: token_budget = 4000. assembled_tokens = 1000. utilization = 1000 / 4000 = 0.25.

    report = await eval_service.evaluate_query(
        query="diabetic options",
        patient_id="pat123",
        collections=["patient_reports"],
        ground_truth_doc_ids=["doc_abc"],
        top_k=5,
        score_threshold=0.3,
        token_budget=4000
      )

    metrics = report["metrics"]
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 1.0
    assert metrics["citation_quality"] == 1.0
    assert abs(metrics["duplicate_rate"] - 0.333) < 0.01
    assert metrics["context_utilization"] == 0.25
    assert metrics["chunk_relevance"] == 0.75  # (0.85 + 0.65) / 2 = 0.75

    mock_retrieval_service.retrieve_multiple.assert_called_once()
    mock_context_assembly_service.assemble.assert_called_once()
