"""
Nura - Unit tests for ReportAnalysisAgent
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.healthcare.report_analysis_agent import ReportAnalysisAgent
from app.agents.base.context import AgentContext
from app.agents.healthcare.schemas import ReportAnalysisAgentResponse
from app.agents.base.response import AgentResponse


@pytest.fixture
def mock_retrieval_agent():
    agent = MagicMock()
    mock_res = AgentResponse(
        success=True,
        message="Retrieval completed",
        response={
            "context": "Lipid panel show abnormal cholesterol levels.",
            "retrieved_chunks": [
                {"text": "Lipid panel findings", "score": 0.95, "metadata": {"source": "report_1", "document_id": "doc-1"}}
            ],
            "collections_used": ["patient_reports"]
        },
        execution_time=10.0,
        agent_name="RetrievalAgent"
    )
    agent.run = AsyncMock(return_value=mock_res)
    return agent


@pytest.fixture
def mock_patient_context_service():
    service = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.patient_profile = {"full_name": "John Doe", "location": "New York"}
    mock_ctx.medical_summary = "Pre-diabetic condition history."
    mock_ctx.current_conditions = ["Hypertension"]
    mock_ctx.current_medications = []
    mock_ctx.medication_allergies = []
    mock_ctx.past_medical_history = []
    service.assemble_context = AsyncMock(return_value=mock_ctx)
    return service


@pytest.fixture
def mock_report_repository():
    repo = MagicMock()
    mock_report = MagicMock()
    mock_report.id = "rep-123"
    mock_report.report_type = "LIPID_PANEL"
    mock_report.created_at = MagicMock()
    mock_report.created_at.isoformat.return_value = "2026-06-27T10:00:00"
    mock_report.risk_level = "MEDIUM"
    mock_report.ai_summary = "Slightly elevated LDL"
    repo.get_by_patient_id = AsyncMock(return_value=[mock_report])
    return repo


@pytest.fixture
def mock_ai_service():
    service = MagicMock()
    mock_res = MagicMock()
    mock_res.response = """
    {
      "summary": "Lipid panel results review shows slightly elevated LDL.",
      "key_findings": ["Elevated LDL cholesterol of 130 mg/dL"],
      "abnormal_values": [
        {
          "metric": "LDL Cholesterol",
          "value": "130 mg/dL",
          "normal_range": "< 100 mg/dL",
          "status": "high"
        }
      ],
      "trend_analysis": ["LDL increased from 110 mg/dL to 130 mg/dL"],
      "recommendations": ["Follow a low-cholesterol diet and retest in 3 months."]
    }
    """
    mock_res.prompt_tokens = 200
    mock_res.completion_tokens = 100
    mock_res.total_tokens = 300
    mock_res.estimated_cost = 0.005
    service.generate = AsyncMock(return_value=mock_res)
    return service


@pytest.mark.asyncio
async def test_report_analysis_agent_execution(
    mock_retrieval_agent,
    mock_patient_context_service,
    mock_report_repository,
    mock_ai_service
):
    agent = ReportAnalysisAgent(
        retrieval_agent=mock_retrieval_agent,
        patient_context_service=mock_patient_context_service,
        report_repository=mock_report_repository,
        ai_service=mock_ai_service
    )
    
    ctx = AgentContext(patient_id="patient-123")
    res = await agent.run("explain my lipid panel report?", ctx)
    
    assert res.success is True
    assert isinstance(res.response, ReportAnalysisAgentResponse)
    assert "elevated LDL" in res.response.summary
    assert len(res.response.abnormal_values) == 1
    assert res.response.abnormal_values[0]["metric"] == "LDL Cholesterol"
    assert len(res.response.citations) == 1
    assert res.response.citations[0]["source"] == "report_1"
    
    mock_retrieval_agent.run.assert_called_once()
    mock_patient_context_service.assemble_context.assert_called_with("patient-123")
    mock_report_repository.get_by_patient_id.assert_called_with("patient-123", limit=20)
    mock_ai_service.generate.assert_called_once()
