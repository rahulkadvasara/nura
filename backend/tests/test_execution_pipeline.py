"""
Nura - Unit tests for LangGraph End-to-End dynamic execution pipeline
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.graph.engine import get_graph_engine
from app.graph.state import GraphState
from app.graph.constants import START_NODE, FINISH_NODE


@pytest.mark.asyncio
async def test_end_to_end_graph_compilation_and_traversal(monkeypatch):
    # Mock services and agents to avoid live external Groq calls
    mock_router = MagicMock()
    mock_decision = MagicMock()
    mock_decision.detected_intent = "MEDICAL_KNOWLEDGE"
    mock_decision.selected_agent = "MedicalKnowledgeAgent"
    mock_decision.confidence = 0.95
    mock_decision.matched_rules = ["is_medical_question"]
    mock_router.run_routing = AsyncMock(return_value=mock_decision)
    monkeypatch.setattr("app.core.dependencies.get_router_agent", lambda: mock_router)

    mock_patient_context = MagicMock()
    mock_patient_context.assemble_context = AsyncMock(return_value=MagicMock(
        patient_profile={"full_name": "John Doe"},
        medical_summary="Healthy patient.",
        current_conditions=[],
        current_medications=[],
        medication_allergies=[],
        metadata=MagicMock(sections_returned=["profile", "summary"])
    ))
    monkeypatch.setattr("app.core.dependencies.get_patient_context_service", lambda: mock_patient_context)

    mock_retrieval_agent = MagicMock()
    mock_retrieval_res = MagicMock()
    mock_retrieval_res.success = True
    mock_retrieval_res.response = {
        "context": "Retrieved medical facts.",
        "retrieved_chunks": [{"text": "Retrieved medical facts.", "score": 0.9, "metadata": {"source": "facts_doc"}}],
        "collections_used": ["knowledge"]
    }
    mock_retrieval_agent.run = AsyncMock(return_value=mock_retrieval_res)
    monkeypatch.setattr("app.core.dependencies.get_retrieval_agent", lambda: mock_retrieval_agent)

    mock_med_agent = MagicMock()
    mock_response = MagicMock()
    mock_response.answer = "Answer to your question."
    mock_response.citations = [{"source": "facts_doc", "text": "facts text", "score": 0.9}]
    mock_response.usage = {"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80}
    mock_med_res = MagicMock()
    mock_med_res.success = True
    mock_med_res.response = mock_response
    mock_med_res.metadata = {"model": "llama-3-groq-70b-tool-use-preview"}
    mock_med_agent.run = AsyncMock(return_value=mock_med_res)
    monkeypatch.setattr("app.core.dependencies.get_medical_knowledge_agent", lambda: mock_med_agent)

    mock_sync_service = MagicMock()
    mock_sync_service.sync_patient = AsyncMock(return_value={"success": True})
    monkeypatch.setattr("app.core.dependencies.get_memory_sync_service", lambda: mock_sync_service)

    # Initialize dynamic graph engine instance
    engine = get_graph_engine()

    state_dict = {
        "request_id": "test-pipeline-req",
        "patient_id": "patient-123",
        "query": "What is diabetes?",
        "debug_mode": True
    }

    # Run execution pipeline
    updated_state_dict = await engine.execute_async(state_dict)
    updated_state = GraphState.from_dict(updated_state_dict)

    # Verify traversal steps trace
    trace = updated_state.execution_trace
    assert trace[0] == START_NODE
    assert "initialize_state" in trace
    assert "router_agent" in trace
    assert "intent_detection" in trace
    assert "patient_context_builder" in trace
    assert "retrieval_agent" in trace
    assert "MedicalKnowledgeAgent" in trace
    assert "response_validation" in trace
    assert "memory_update" in trace
    assert "telemetry" in trace
    assert trace[-1] == FINISH_NODE

    # Verify context assembly, retrieval injections, and answers
    assert "John Doe" in updated_state.patient_context
    assert "diabetes" in updated_state.query
    assert updated_state.response == "Answer to your question."
    assert len(updated_state.citations) == 1
    assert updated_state.citations[0]["source"] == "facts_doc"
    assert updated_state.error is None
