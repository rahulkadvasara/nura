import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
from unittest.mock import AsyncMock, MagicMock

try:
    from app.services.report_extraction.laboratory_parser import LaboratoryParser
    from app.services.report_extraction.medication_parser import MedicationParser
except ImportError:
    from backend.app.services.report_extraction.laboratory_parser import LaboratoryParser
    from backend.app.services.report_extraction.medication_parser import MedicationParser


@pytest.mark.asyncio
async def test_laboratory_parser_llm_and_dedup():
    mock_ai = MagicMock()
    mock_res = MagicMock()
    mock_res.response = (
        '{"laboratory_results": ['
        '  {"test_name": "Hemoglobin", "value": 14.5, "unit": "g/dL", "reference_range": "13.0 - 17.0", "status": "NORMAL"},'
        '  {"test_name": "hemoglobin", "value": 14.5, "unit": "g/dL", "reference_range": "13.0 - 17.0", "status": "NORMAL"}'
        ']}'
    )
    mock_ai.generate_json = AsyncMock(return_value=mock_res)

    parser = LaboratoryParser(ai_service=mock_ai)
    labs = await parser.parse_labs("Hemoglobin: 14.5")
    
    # Should deduplicate case-insensitively
    assert len(labs) == 1
    assert labs[0]["test_name"] == "Hemoglobin"
    assert labs[0]["value"] == 14.5


@pytest.mark.asyncio
async def test_medication_parser_llm_and_dedup():
    mock_ai = MagicMock()
    mock_res = MagicMock()
    mock_res.response = (
        '{"medications": ['
        '  {"medicine": "Aspirin", "dosage": "75mg", "frequency": "Once daily", "duration": "30 days", "route": "Oral"},'
        '  {"medicine": "aspirin", "dosage": "75mg", "frequency": "Once daily", "duration": "30 days", "route": "Oral"}'
        ']}'
    )
    mock_ai.generate_json = AsyncMock(return_value=mock_res)

    parser = MedicationParser(ai_service=mock_ai)
    meds = await parser.parse_medications("Take Aspirin 75mg")
    
    # Should deduplicate case-insensitively
    assert len(meds) == 1
    assert meds[0]["medicine"] == "Aspirin"
    assert meds[0]["dosage"] == "75mg"
