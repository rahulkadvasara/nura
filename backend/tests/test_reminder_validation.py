import pytest
from unittest.mock import AsyncMock, patch
from app.services.reminder_service import ReminderService
from app.schemas.reminder import ReminderCreateSchema, ReminderUpdateSchema
from app.models.reminder import ReminderType, ReminderStatus, ReminderSourceType

@pytest.mark.asyncio
async def test_create_reminder_safety_block_failure():
    """Test that a medication reminder creation is BLOCKED if validation fails without override"""
    mock_user_repo = AsyncMock()
    mock_user_repo.get = AsyncMock(return_value={"id": "patient_1", "role": "patient"})

    mock_reminder_repo = AsyncMock()
    mock_event_dispatcher = AsyncMock()

    mock_val_service = AsyncMock()
    mock_val_service.validate_medications = AsyncMock(return_value={
        "decision": "BLOCK",
        "severity": "CRITICAL",
        "recommendations": ["Critical interaction risk"]
    })

    service = ReminderService(
        reminder_repository=mock_reminder_repo,
        user_repository=mock_user_repo,
        event_dispatcher=mock_event_dispatcher
    )

    schema = ReminderCreateSchema(
        patient_id="patient_1",
        reminder_type=ReminderType.MEDICATION,
        title="Take Warfarin",
        scheduled_time="09:00",
        recurrence="daily",
        status=ReminderStatus.ACTIVE,
        source_type=ReminderSourceType.MANUAL
    )

    with patch("app.core.dependencies.get_medication_validation_service", return_value=mock_val_service):
        with pytest.raises(ValueError) as exc:
            await service.create_reminder(schema)
        assert "blocked due to critical interaction" in str(exc.value)


@pytest.mark.asyncio
async def test_create_reminder_safety_block_override_success():
    """Test that a medication reminder creation succeeds with a doctor override"""
    mock_user_repo = AsyncMock()
    mock_user_repo.get = AsyncMock(return_value={"id": "patient_1", "role": "patient"})

    mock_reminder_repo = AsyncMock()
    mock_reminder_repo.collection = AsyncMock()
    mock_reminder_repo.collection.insert_one = AsyncMock(return_value=AsyncMock(inserted_id="rem_1"))
    
    mock_db_reminder = {
        "_id": "rem_1",
        "patient_id": "patient_1",
        "reminder_type": "medication",
        "title": "Take Warfarin",
        "description": "Scheduled dosage",
        "scheduled_time": "09:00",
        "recurrence": "daily",
        "status": "active",
        "source_type": "manual",
        "source_id": None
    }
    mock_reminder_repo.collection.find_one = AsyncMock(return_value=mock_db_reminder)

    mock_event_dispatcher = AsyncMock()

    mock_val_service = AsyncMock()
    mock_val_service.validate_medications = AsyncMock(return_value={
        "decision": "BLOCK",
        "severity": "CRITICAL",
        "recommendations": ["Critical interaction risk"]
    })
    mock_val_service.validate_and_update_patient_memory = AsyncMock()

    service = ReminderService(
        reminder_repository=mock_reminder_repo,
        user_repository=mock_user_repo,
        event_dispatcher=mock_event_dispatcher
    )

    schema = ReminderCreateSchema(
        patient_id="patient_1",
        reminder_type=ReminderType.MEDICATION,
        title="Take Warfarin",
        scheduled_time="09:00",
        recurrence="daily",
        status=ReminderStatus.ACTIVE,
        source_type=ReminderSourceType.MANUAL,
        override=True,
        override_reason="Doctor override necessary",
        user_role="doctor"
    )

    with patch("app.core.dependencies.get_medication_validation_service", return_value=mock_val_service):
        reminder = await service.create_reminder(schema)
        assert reminder.id == "rem_1"
        assert reminder.title == "Take Warfarin"
        mock_val_service.validate_and_update_patient_memory.assert_called_once_with("patient_1")
