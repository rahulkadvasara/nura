import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.report_extraction.medical_entity_extractor import MedicalEntityExtractor


@pytest.mark.asyncio
async def test_entity_extractor_llm_success():
    mock_ai = MagicMock()
    mock_res = MagicMock()
    mock_res.response = (
        '{"patient_information": {"patient_name": "Alice Smith", "age": 28, "gender": "Female", "date_of_birth": "1996-05-12", "patient_id": "P100"}, '
        '"hospital_information": {"hospital": "City Hospital", "laboratory": "Core Lab", "doctor": "Dr. House", "department": "Cardiology", "report_date": "2024-06-20"}, '
        '"entities": [{"text": "Diabetes", "category": "diagnoses", "confidence": 0.95, "page": 1, "position": "line 2"}], '
        '"confidence": 0.96}'
    )
    mock_ai.generate_json = AsyncMock(return_value=mock_res)

    extractor = MedicalEntityExtractor(ai_service=mock_ai)
    res = await extractor.extract_entities("Alice Smith is a 28 year old female diagnosed with Diabetes")
    
    assert res["patient_information"]["patient_name"] == "Alice Smith"
    assert res["hospital_information"]["hospital"] == "City Hospital"
    assert len(res["entities"]) == 1
    assert res["entities"][0]["text"] == "Diabetes"
    assert res["entities"][0]["category"] == "diagnoses"
    assert res["method"] == "llm_groq"


@pytest.mark.asyncio
async def test_entity_extractor_fallback():
    mock_ai = MagicMock()
    mock_ai.generate_json = AsyncMock(side_effect=Exception("Timeout"))

    extractor = MedicalEntityExtractor(ai_service=mock_ai)
    ocr_text = "PATIENT NAME: Bob Jones\nAGE: 45\nGENDER: Male\nREPORT DATE: 12 Jan 2024\nDIAGNOSIS: Diabetes"
    
    res = await extractor.extract_entities(ocr_text)
    
    assert res["patient_information"]["patient_name"] == "Bob Jones"
    assert res["patient_information"]["age"] == 45
    assert res["patient_information"]["gender"] == "Male"
    assert res["hospital_information"]["report_date"] == "12 Jan 2024"
    assert res["method"] == "rule_fallback"
    
    # Check that diagnoses/symptoms entities got matched
    assert len(res["entities"]) > 0
    assert any(ent["text"] == "Diabetes" for ent in res["entities"])
