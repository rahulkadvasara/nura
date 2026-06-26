"""
Nura - Unit tests for RAGBenchmarkService
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.rag_benchmark_service import RAGBenchmarkService

@pytest.fixture
def mock_evaluation_service():
    service = AsyncMock()
    # Mocking evaluation results return payload
    service.evaluate_query.return_value = {
        "query": "mocked query",
        "metrics": {
            "precision": 0.8,
            "recall": 0.6,
            "latency_ms": 120.0,
            "citation_quality": 0.9,
            "chunk_relevance": 0.75,
            "duplicate_rate": 0.1,
            "context_utilization": 0.3
        }
    }
    return service

@pytest.mark.asyncio
async def test_execute_benchmarks(mock_evaluation_service):
    benchmark_service = RAGBenchmarkService(evaluation_service=mock_evaluation_service)

    # Trigger benchmarks execution
    report = await benchmark_service.execute_benchmarks(
        patient_id="pat123",
        token_budget=4000,
        score_threshold=0.3
    )

    assert "total_queries_run" in report
    assert report["total_queries_run"] > 0
    assert report["avg_precision"] == pytest.approx(0.8)
    assert report["avg_recall"] == pytest.approx(0.6)
    assert report["avg_citation_quality"] == pytest.approx(0.9)
    assert report["avg_duplicate_rate"] == pytest.approx(0.1)
    assert report["avg_context_utilization"] == pytest.approx(0.3)

    # Check categories breakdown presence
    assert "Medical" in report["categories"]
    assert "Reports" in report["categories"]
    assert "Drug" in report["categories"]
    assert report["categories"]["Medical"]["intent"] == "medical_question"
    assert len(report["categories"]["Medical"]["query_details"]) == 4

    # Ensure get_query was called the correct number of times (7 datasets * 4 queries each = 28 times)
    assert mock_evaluation_service.evaluate_query.call_count == 28
