import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.drug_ai.explanation_service import DrugExplanationService, get_drug_explanation_service
from app.services.drug_ai.telemetry import get_drug_ai_telemetry
from app.services.groq_service import GroqService

@pytest.fixture(autouse=True)
def reset_telemetry():
    telemetry = get_drug_ai_telemetry()
    telemetry.reset()
    yield
    telemetry.reset()

@pytest.mark.asyncio
async def test_drug_explanation_service_success():
    # Mock GroqService
    mock_groq = MagicMock(spec=GroqService)
    
    mock_res = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "AI Generated Narrative Explanation content details"
    mock_choice.finish_reason = "stop"
    mock_res.choices = [mock_choice]
    mock_res.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    mock_res.model = "llama3-70b"
    
    mock_groq.generate = AsyncMock(return_value=mock_res)
    
    service = DrugExplanationService(groq_service=mock_groq)
    
    meds = ["Aspirin", "Warfarin"]
    severity = "HIGH"
    recommendations = ["Avoid combination. Consult doctor."]
    interactions = [
        {"drug_a": "Aspirin", "drug_a_normalized": "aspirin", "drug_b": "Warfarin", "drug_b_normalized": "warfarin", "severity": "HIGH", "description": "High bleeding risk."}
    ]
    
    res = await service.explain_safety(meds, severity, recommendations, interactions)
    
    assert res["patient_explanation"] == "AI Generated Narrative Explanation content details"
    assert res["doctor_explanation"] == "AI Generated Narrative Explanation content details"
    assert res["summary"] == "AI Generated Narrative Explanation content details"
    assert res["precautions"] == "AI Generated Narrative Explanation content details"
    assert res["fallback_used"] is False
    assert res["prompt_tokens"] == 40
    assert res["completion_tokens"] == 80
    assert res["model_used"] == "llama3-70b"
    
    telemetry = get_drug_ai_telemetry().get_statistics()
    assert telemetry["explanation_requests"] == 1
    assert telemetry["successful_generations"] == 1
    assert telemetry["fallback_executions"] == 0
    assert telemetry["prompt_tokens"] == 40
    assert telemetry["completion_tokens"] == 80


@pytest.mark.asyncio
async def test_drug_explanation_service_loader():
    service = get_drug_explanation_service()
    assert service.loader is not None
    assert service.loader.get_template("drug_system", is_system=True) is not None
