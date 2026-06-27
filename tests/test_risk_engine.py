import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.report_risk.risk_engine import RiskEngine


def test_calculate_score_and_severity_normal():
    mock_ai = MagicMock()
    engine = RiskEngine(ai_service=mock_ai)
    
    score, severity = engine.calculate_score_and_severity([], 0)
    assert score == 0.0
    assert severity == "NORMAL"


def test_calculate_score_and_severity_abnormal():
    mock_ai = MagicMock()
    engine = RiskEngine(ai_service=mock_ai)
    
    # 1. Medium finding
    findings_med = [{"rule_name": "Thyroid", "severity": "MEDIUM"}]
    score, severity = engine.calculate_score_and_severity(findings_med, 0)
    assert score == 15.0
    assert severity == "MEDIUM"

    # 2. Critical finding
    findings_crit = [{"rule_name": "Potassium Critical", "severity": "CRITICAL"}]
    score, severity = engine.calculate_score_and_severity(findings_crit, 0)
    assert score == 35.0
    assert severity == "CRITICAL"


@pytest.mark.asyncio
async def test_analyze_risks_llm_success():
    mock_ai = MagicMock()
    mock_res = MagicMock()
    mock_res.response = (
        '{"findings_explanations": ['
        '  {"finding_name": "Diabetes Indicator (HbA1c)", "explanation": "HbA1c of 7.2% is above limits."}'
        '], "confidence": 0.95}'
    )
    mock_ai.generate_json = AsyncMock(return_value=mock_res)

    engine = RiskEngine(ai_service=mock_ai)
    findings = [{"rule_name": "Diabetes Indicator (HbA1c)", "severity": "HIGH", "message": "HbA1c 7.2%"}]
    
    res = await engine.analyze_risks("HbA1c 7.2%", findings)
    
    assert len(res["findings_explanations"]) == 1
    assert res["findings_explanations"][0]["finding_name"] == "Diabetes Indicator (HbA1c)"
    assert res["findings_explanations"][0]["explanation"] == "HbA1c of 7.2% is above limits."
    assert res["confidence"] == 0.95


@pytest.mark.asyncio
async def test_analyze_risks_fallback():
    mock_ai = MagicMock()
    mock_ai.generate_json = AsyncMock(side_effect=Exception("API limit exceeded"))

    engine = RiskEngine(ai_service=mock_ai)
    findings = [{"rule_name": "Thyroid Rule", "severity": "LOW", "message": "TSH is 5.2"}]
    
    res = await engine.analyze_risks("TSH is 5.2", findings)
    
    assert len(res["findings_explanations"]) == 1
    assert res["findings_explanations"][0]["finding_name"] == "Thyroid Rule"
    assert "Thyroid Rule" in res["findings_explanations"][0]["explanation"]
    assert res["confidence"] == 0.70
