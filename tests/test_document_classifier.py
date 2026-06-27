import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
from unittest.mock import AsyncMock, MagicMock

try:
    from app.services.report_extraction.document_classifier import DocumentClassifier
except ImportError:
    from backend.app.services.report_extraction.document_classifier import DocumentClassifier


@pytest.mark.asyncio
async def test_document_classifier_llm_success():
    # Mock AIService
    mock_ai = MagicMock()
    mock_res = MagicMock()
    mock_res.response = '{"document_type": "CBC", "confidence": 0.98}'
    mock_ai.generate_json = AsyncMock(return_value=mock_res)

    classifier = DocumentClassifier(ai_service=mock_ai)
    res = await classifier.classify("Hemoglobin 14.5 WBC 7.2 Platelets 250")
    
    assert res["document_type"] == "CBC"
    assert res["confidence"] == 0.98
    assert res["method"] == "llm_groq"


@pytest.mark.asyncio
async def test_document_classifier_fallback_rules():
    # Mock AIService to throw exception (offline / key missing simulation)
    mock_ai = MagicMock()
    mock_ai.generate_json = AsyncMock(side_effect=Exception("API Key Missing"))

    classifier = DocumentClassifier(ai_service=mock_ai)
    
    # 1. Lipid profile match
    res_lipid = await classifier.classify("Total Cholesterol 195 LDL 120 Triglycerides")
    assert res_lipid["document_type"] == "Lipid Profile"
    assert res_lipid["method"] == "rule_fallback"

    # 2. CBC match
    res_cbc = await classifier.classify("patient hemoglobin levels are low, white blood cells count")
    assert res_cbc["document_type"] == "CBC"
    
    # 3. Prescription match
    res_rx = await classifier.classify("Take 1 tablet of Metformin daily. Rx strength")
    assert res_rx["document_type"] == "Prescription"
