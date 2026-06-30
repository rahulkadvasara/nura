import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.services.drug_safety.batch_validation_service import BatchValidationService
from app.services.drug_safety.validation_service import MedicationValidationService

@pytest.mark.asyncio
async def test_batch_validation_de_duplication():
    db = MagicMock()
    mock_val_service = AsyncMock(spec=MedicationValidationService)
    
    # Mock validation returns
    mock_val_service.validate_medications.return_value = {"decision": "ALLOW", "severity": "NONE"}
    
    batch_service = BatchValidationService(db, mock_val_service, max_concurrency=2)
    
    # We pass duplicate medication lists (the second is same as first, just shuffled and uppercase)
    med_lists = [
        ["Aspirin", "Warfarin"],
        ["Warfarin", "aspirin"],
        ["Lisinopril"]
    ]
    
    results = await batch_service.validate_medication_lists("pat-123", med_lists)
    
    assert len(results) == 3
    # validate_medications should only be called twice (for unique lists: ['ASPIRIN', 'WARFARIN'] and ['LISINOPRIL'])
    assert mock_val_service.validate_medications.call_count == 2

@pytest.mark.asyncio
async def test_batch_validation_historical():
    db = MagicMock()
    mock_val_service = AsyncMock(spec=MedicationValidationService)
    
    # Mock validate_and_update_patient_memory
    mock_val_service.validate_and_update_patient_memory.return_value = {"overall_severity": "LOW"}
    
    batch_service = BatchValidationService(db, mock_val_service, max_concurrency=3)
    
    patient_ids = ["pat-1", "pat-2", "pat-1", "pat-3"] # pat-1 is duplicate
    
    res = await batch_service.validate_patient_historical(patient_ids)
    
    assert res["success"] is True
    assert res["total_requested"] == 4
    assert res["total_unique"] == 3
    assert res["success_count"] == 3
    assert mock_val_service.validate_and_update_patient_memory.call_count == 3
