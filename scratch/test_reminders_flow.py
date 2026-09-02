import asyncio
import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.db.mongodb import get_database
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.user_repository import UserRepository
from app.services.reminder_service import ReminderService
from app.schemas.reminder import ReminderCreateSchema, ReminderType
from app.core.dependencies import get_medication_validation_service

async def test_reminders_and_drug_safety():
    print("--- Testing Reminders & Drug Safety Integration ---")
    db = get_database()
    reminder_repo = ReminderRepository(db.reminders)
    user_repo = UserRepository(db.users)
    
    # 1. Get or create test patient user
    user_doc = await db.users.find_one({"role": "patient"})
    if not user_doc:
        patient_id = "6a3784b31466c381d1cb2179"
    else:
        patient_id = str(user_doc["_id"])
    print(f"Testing with Patient ID: {patient_id}")
    
    reminder_service = ReminderService(
        reminder_repository=reminder_repo,
        user_repository=user_repo
    )
    
    val_service = get_medication_validation_service()
    
    # 2. Test direct MedicationValidationService.validate_medications with override kwargs
    print("\n1. Testing MedicationValidationService.validate_medications with kwargs...")
    res = await val_service.validate_medications(
        patient_id=patient_id,
        incoming_medications=["Aspirin"],
        source="reminder",
        override_reason="Doctor approved",
        overridden_by="doctor"
    )
    print(f"Validation Decision: {res.get('decision')} | Severity: {res.get('severity')} | Latency: {res.get('latency_ms')}ms")
    assert "decision" in res, "Validation result missing decision"
    print("MedicationValidationService signature test passed!")
    
    # 3. Test ReminderService.create_reminder for a safe medication
    print("\n2. Testing ReminderService.create_reminder for 'Aspirin'...")
    schema = ReminderCreateSchema(
        patient_id=patient_id,
        reminder_type=ReminderType.MEDICATION,
        title="Take Aspirin",
        description="Scheduled dosage of Aspirin",
        scheduled_time="20:00",
        recurrence="daily",
        status="active"
    )
    
    created_reminder = await reminder_service.create_reminder(schema)
    print(f"Successfully created reminder ID: {created_reminder.id} | Title: {created_reminder.title} | Time: {created_reminder.scheduled_time}")
    
    # 4. Clean up created reminder
    print("\n3. Cleaning up test reminder...")
    deleted = await reminder_service.delete_reminder(created_reminder.id)
    print(f"Reminder cleanup success: {deleted}")
    
    print("\n--- ALL REMINDER & DRUG SAFETY TESTS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    asyncio.run(test_reminders_and_drug_safety())
