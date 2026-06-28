import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.report_ai.report_understanding_service import ReportUnderstandingService


@pytest.mark.asyncio
async def test_generate_report_summary_success():
    # 1. Mock Repository
    mock_repo = MagicMock()
    mock_report = MagicMock()
    mock_report.id = "rep-123"
    mock_report.patient_id = "pat-123"
    mock_report.structured_data = {"patient_information": {"patient_name": "Charlie"}}
    mock_report.laboratory_results = []
    mock_report.medications = []
    mock_report.risk_findings = []
    mock_report.recommendations = []
    mock_repo.get = AsyncMock(return_value=mock_report)
    mock_repo.collection = MagicMock()
    mock_repo.collection.update_one = AsyncMock()
    mock_repo.collection.find_one = MagicMock(return_value={"_id": "rep-123"})

    # 2. Mock AIService
    mock_ai = MagicMock()
    mock_ai_res = MagicMock()
    mock_ai_res.response = (
        '{"ai_summary": "Exec summary", "patient_summary": "Friendly summary", '
        '"doctor_summary": "Doc summary", "key_findings": ["F1"], '
        '"clinical_insights": ["I1"], "followup_questions": ["Q1"], '
        '"confidence": 0.95}'
    )
    mock_ai_res.model = "groq-test"
    mock_ai_res.prompt_tokens = 100
    mock_ai_res.completion_tokens = 50
    mock_ai_res.estimated_cost = 0.002
    mock_ai.generate_json = AsyncMock(return_value=mock_ai_res)

    # 3. Mock ReportAnalysisAgent
    mock_agent = MagicMock()
    mock_agent_res = MagicMock()
    mock_agent_res.success = True
    mock_agent_res.response = MagicMock(summary="Historical notes", trend_analysis=["Lipids stable"])
    mock_agent.run = AsyncMock(return_value=mock_agent_res)

    # 4. Mock Loader
    mock_loader = MagicMock()
    mock_loader.render = MagicMock(return_value="rendered-prompt")

    # 5. Mock helper services
    mock_sum_service = MagicMock()
    mock_ins_service = MagicMock()

    service = ReportUnderstandingService(
        report_repository=mock_repo,
        ai_service=mock_ai,
        report_analysis_agent=mock_agent,
        prompt_loader=mock_loader,
        summary_service=mock_sum_service,
        insight_service=mock_ins_service
    )

    res = await service.generate_report_summary("rep-123")
    
    assert res is not None
    mock_repo.get.assert_called_with("rep-123")
    mock_agent.run.assert_called_once()
    mock_ai.generate_json.assert_called_once()
    mock_repo.collection.update_one.assert_called_once()
