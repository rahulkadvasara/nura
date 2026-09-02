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
from app.core.dependencies import get_medication_validation_service, get_drug_interaction_agent
from app.agents.base.context import AgentContext

async def test_reminders_and_drug_agent():
    print("--- Testing Reminders & DrugInteractionAgent Integration ---")
    db = get_database()
    reminder_repo = ReminderRepository(db.reminders)
    user_repo = UserRepository(db.users)
    
    # 1. Get test patient user
    user_doc = await db.users.find_one({"role": "patient"})
    patient_id = str(user_doc["_id"]) if user_doc else "6a3784b31466c381d1cb2179"
    print(f"Testing with Patient ID: {patient_id}")
    
    reminder_service = ReminderService(
        reminder_repository=reminder_repo,
        user_repository=user_repo
    )
    val_service = get_medication_validation_service()
    drug_agent = get_drug_interaction_agent()
    
    # 2. Test DrugInteractionAgent execution for Aspirin
    print("\n1. Executing DrugInteractionAgent.execute for 'Aspirin'...")
    agent_ctx = AgentContext(patient_id=patient_id)
    agent_res = await drug_agent.execute("Check safety parameters for: Aspirin", context=agent_ctx)
    print(f"Agent Response -> Found: {agent_res.interaction_found} | Severity: {agent_res.severity}")
    print(f"Agent Warnings ({len(agent_res.warnings)}): {agent_res.warnings}")
    assert hasattr(agent_res, "severity"), "Agent response missing severity field"
    
    # 3. Test non-blocking reminder creation for Aspirin (even if duplicate or interacting)
    print("\n2. Testing NON-BLOCKING ReminderService.create_reminder for 'Aspirin'...")
    schema = ReminderCreateSchema(
        patient_id=patient_id,
        reminder_type=ReminderType.MEDICATION,
        title="Take Aspirin",
        description="Scheduled dosage of Aspirin",
        scheduled_time="20:00",
        recurrence="daily",
        status="active"
    )
    
    # Should create reminder cleanly without throwing ValueError
    created_reminder = await reminder_service.create_reminder(schema)
    print(f"Successfully created non-blocking reminder ID: {created_reminder.id} | Title: {created_reminder.title}")
    
    # 4. Clean up test reminder
    print("\n3. Cleaning up test reminder...")
    deleted = await reminder_service.delete_reminder(created_reminder.id)
    print(f"Reminder cleanup success: {deleted}")
    
    print("\n--- ALL REMINDER & DRUG INTERACTION AGENT TESTS PASSED! ---")

if __name__ == "__main__":
    asyncio.run(test_reminders_and_drug_agent())
