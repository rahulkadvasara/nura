import pytest
from unittest.mock import AsyncMock, patch
from app.services.prescription_service import PrescriptionService
from app.schemas.appointment import PrescriptionCreateSchema, MedicationSchema
from app.models.appointment import PrescriptionInDB

@pytest.mark.asyncio
async def test_create_prescription_interaction_block_without_reason():
    """Test that a prescription fails to be created if interactions exist and no override reason is provided"""
    mock_pres_repo = AsyncMock()
    mock_pres_repo.get_by_consultation_id = AsyncMock(return_value=None)
    mock_consult_repo = AsyncMock()
    
    mock_consultation = AsyncMock()
    mock_consultation.patient_id = "patient_123"
    mock_consult_repo.get = AsyncMock(return_value=mock_consultation)

    mock_event_dispatcher = AsyncMock()

    mock_val_service = AsyncMock()
    mock_val_service.validate_medications = AsyncMock(return_value={
        "decision": "BLOCK",
        "severity": "CRITICAL",
        "recommendations": ["Aspirin + Warfarin bleeding risk"]
    })

    service = PrescriptionService(
        prescription_repository=mock_pres_repo,
        consultation_repository=mock_consult_repo,
        event_dispatcher=mock_event_dispatcher
    )

    schema = PrescriptionCreateSchema(
        consultation_id="consult_1",
        patient_id="patient_123",
        doctor_id="doc_1",
        medications=[
            MedicationSchema(drug_name="Aspirin", dosage="100mg", frequency="daily", duration="1 week"),
            MedicationSchema(drug_name="Warfarin", dosage="5mg", frequency="daily", duration="1 week")
        ],
        override=True
    )

    with patch("app.core.dependencies.get_medication_validation_service", return_value=mock_val_service):
        with pytest.raises(ValueError) as exc:
            await service.create_prescription(
                consultation_id="consult_1",
                doctor_profile_id="doc_1",
                doctor_user_id="doc_user_1",
                schema=schema,
                user_repository=AsyncMock()
            )
        assert "An override reason is required" in str(exc.value)


@pytest.mark.asyncio
async def test_create_prescription_override_success():
    """Test that a prescription with critical interactions is successfully created when override reason is supplied"""
    mock_pres_repo = AsyncMock()
    mock_pres_repo.get_by_consultation_id = AsyncMock(return_value=None)
    mock_pres_repo.collection = AsyncMock()
    mock_pres_repo.collection.insert_one = AsyncMock(return_value=AsyncMock(inserted_id="pres_1"))

    mock_db_prescription = {
        "_id": "pres_1",
        "consultation_id": "consult_1",
        "patient_id": "patient_123",
        "doctor_id": "doc_1",
        "medications": [
            {"drug_name": "Aspirin", "dosage": "100mg", "frequency": "daily", "duration": "1 week"},
            {"drug_name": "Warfarin", "dosage": "5mg", "frequency": "daily", "duration": "1 week"}
        ],
        "override_reason": "Clinically indicated under monitoring"
    }
    mock_pres_repo.collection.find_one = AsyncMock(return_value=mock_db_prescription)

    mock_consult_repo = AsyncMock()
    mock_consultation = AsyncMock()
    mock_consultation.patient_id = "patient_123"
    mock_consult_repo.get = AsyncMock(return_value=mock_consultation)

    mock_event_dispatcher = AsyncMock()
    mock_user_repo = AsyncMock()
    mock_user_repo.get = AsyncMock(return_value=AsyncMock(full_name="Dr. House"))

    mock_val_service = AsyncMock()
    mock_val_service.validate_medications = AsyncMock(return_value={
        "decision": "BLOCK",
        "severity": "CRITICAL",
        "recommendations": ["Aspirin + Warfarin bleeding risk"]
    })
    mock_val_service.validate_and_update_patient_memory = AsyncMock()

    service = PrescriptionService(
        prescription_repository=mock_pres_repo,
        consultation_repository=mock_consult_repo,
        event_dispatcher=mock_event_dispatcher
    )

    schema = PrescriptionCreateSchema(
        consultation_id="consult_1",
        patient_id="patient_123",
        doctor_id="doc_1",
        medications=[
            MedicationSchema(drug_name="Aspirin", dosage="100mg", frequency="daily", duration="1 week"),
            MedicationSchema(drug_name="Warfarin", dosage="5mg", frequency="daily", duration="1 week")
        ],
        override=True,
        override_reason="Clinically indicated under monitoring"
    )

    with patch("app.core.dependencies.get_medication_validation_service", return_value=mock_val_service):
        pres = await service.create_prescription(
            consultation_id="consult_1",
            doctor_profile_id="doc_1",
            doctor_user_id="doc_user_1",
            schema=schema,
            user_repository=mock_user_repo
        )
        assert pres.id == "pres_1"
        assert pres.override_reason == "Clinically indicated under monitoring"
        mock_val_service.validate_and_update_patient_memory.assert_called_once_with("patient_123")
