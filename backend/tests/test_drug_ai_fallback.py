import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.drug_ai.fallback_service import DrugExplanationFallbackService
from app.services.drug_ai.explanation_service import DrugExplanationService
from app.services.drug_ai.telemetry import get_drug_ai_telemetry
from app.services.groq_service import GroqService

@pytest.fixture(autouse=True)
def reset_telemetry():
    telemetry = get_drug_ai_telemetry()
    telemetry.reset()
    yield
    telemetry.reset()

def test_fallback_service_explanations():
    patient_exp = DrugExplanationFallbackService.generate_patient_explanation(
        "HIGH", ["Avoid medication combination."]
    )
    assert "Interaction Severity: HIGH" in patient_exp
    assert "Avoid medication combination." in patient_exp
    assert "Disclaimer:" in patient_exp or "informational purposes only" in patient_exp

    doctor_exp = DrugExplanationFallbackService.generate_doctor_explanation(
        "HIGH", ["Avoid medication combination."], [{"drug_a": "A", "drug_b": "B", "severity": "HIGH", "description": "Interacts."}]
    )
    assert "Clinical Interaction Report" in doctor_exp
    assert "A and B (HIGH): Interacts" in doctor_exp

    summary = DrugExplanationFallbackService.generate_summary(
        "HIGH", ["A", "B"], [{"drug_a": "A", "drug_b": "B", "severity": "HIGH"}]
    )
    assert "Deterministic HIGH interaction detected" in summary

    precautions = DrugExplanationFallbackService.generate_precautions("HIGH")
    assert "Avoid taking these medications together." in precautions


@pytest.mark.asyncio
async def test_explanation_service_fallback_on_exception():
    mock_groq = MagicMock(spec=GroqService)
    # Mock generation failure
    mock_groq.generate = AsyncMock(side_effect=Exception("Timeout or API limits exceeded"))

    service = DrugExplanationService(groq_service=mock_groq)

    meds = ["A", "B"]
    severity = "HIGH"
    recommendations = ["Avoid medication combination."]
    interactions = [{"drug_a": "A", "drug_b": "B", "severity": "HIGH", "description": "Interacts."}]

    res = await service.explain_safety(meds, severity, recommendations, interactions)

    assert res["fallback_used"] is True
    assert "Interaction Severity: HIGH" in res["patient_explanation"]
    assert "Clinical Interaction Report" in res["doctor_explanation"]
    assert "Interacts" in res["doctor_explanation"]
    assert "Deterministic HIGH interaction" in res["summary"]
    assert "Avoid taking these medications together" in res["precautions"]

    telemetry = get_drug_ai_telemetry().get_statistics()
    assert telemetry["explanation_requests"] == 1
    assert telemetry["successful_generations"] == 0
    assert telemetry["fallback_executions"] == 1
