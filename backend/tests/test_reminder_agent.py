"""
Nura - Unit tests for ReminderAgent
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.operations.reminder_agent import ReminderAgent
from app.agents.base.context import AgentContext
from app.agents.operations.schemas import ReminderAgentResponse
from app.agents.base.response import AgentResponse
from app.models.reminder import ReminderInDB, ReminderType, ReminderStatus


@pytest.fixture
def mock_reminder_service():
    service = MagicMock()
    
    # Mock create_reminder
    mock_db_reminder = ReminderInDB(
        id="reminder-111",
        patient_id="patient-123",
        reminder_type=ReminderType.MEDICATION,
        title="Take Aspirin",
        description="Auto-scheduled medication reminder for Aspirin",
        scheduled_time="08:00",
        recurrence="daily",
        status=ReminderStatus.ACTIVE
    )
    service.create_reminder = AsyncMock(return_value=mock_db_reminder)
    
    # Mock to_response conversion
    mock_res_schema = MagicMock()
    mock_res_schema.model_dump = MagicMock(return_value={
        "id": "reminder-111",
        "patient_id": "patient-123",
        "reminder_type": "medication",
        "title": "Take Aspirin",
        "description": "Auto-scheduled medication reminder for Aspirin",
        "scheduled_time": "08:00",
        "recurrence": "daily",
        "status": "active"
    })
    service.to_response = MagicMock(return_value=mock_res_schema)
    
    # Mock list_active_reminders
    service.list_active_reminders = AsyncMock(return_value=[mock_db_reminder])
    
    # Mock update_reminder
    service.update_reminder = AsyncMock(return_value=mock_db_reminder)
    
    # Mock delete_reminder
    service.delete_reminder = AsyncMock(return_value=True)
    
    # Mock get_reminder_by_id
    service.get_reminder_by_id = AsyncMock(return_value=mock_db_reminder)

    return service


@pytest.fixture
def mock_ai_service_success():
    service = MagicMock()
    mock_res = MagicMock()
    mock_res.response = """
    {
      "action": "create_medication_reminder",
      "parameters": {
        "medication_name": "Aspirin",
        "title": "Take Aspirin",
        "description": "Take 1 tablet after breakfast",
        "scheduled_time": "08:00",
        "recurrence": "daily"
      }
    }
    """
    mock_res.prompt_tokens = 100
    mock_res.completion_tokens = 50
    mock_res.total_tokens = 150
    mock_res.estimated_cost = 0.002
    service.generate = AsyncMock(return_value=mock_res)
    return service


@pytest.fixture
def mock_drug_agent_no_interaction():
    agent = MagicMock()
    mock_response = MagicMock()
    mock_response.model_dump = MagicMock(return_value={
        "interaction_found": False,
        "severity": "LOW",
        "warnings": []
    })
    mock_res = AgentResponse(
        success=True,
        message="Safety verified",
        response=mock_response,
        execution_time=1.0,
        agent_name="DrugInteractionAgent"
    )
    agent.run = AsyncMock(return_value=mock_res)
    return agent


@pytest.fixture
def mock_drug_agent_high_interaction():
    agent = MagicMock()
    mock_response = MagicMock()
    mock_response.model_dump = MagicMock(return_value={
        "interaction_found": True,
        "severity": "HIGH",
        "warnings": ["Dangerous bleeding risk identified"]
    })
    mock_res = AgentResponse(
        success=True,
        message="Safety conflict identified",
        response=mock_response,
        execution_time=1.0,
        agent_name="DrugInteractionAgent"
    )
    agent.run = AsyncMock(return_value=mock_res)
    return agent


@pytest.mark.asyncio
async def test_reminder_agent_create_success(
    mock_reminder_service,
    mock_ai_service_success,
    mock_drug_agent_no_interaction,
    monkeypatch
):
    # Monkeypatch the get_drug_interaction_agent and get_patient_context_service dependencies
    monkeypatch.setattr("app.core.dependencies.get_drug_interaction_agent", lambda: mock_drug_agent_no_interaction)
    
    mock_ctx_service = MagicMock()
    mock_ctx_service.assemble_context = AsyncMock(return_value=None)
    monkeypatch.setattr("app.core.dependencies.get_patient_context_service", lambda: mock_ctx_service)

    agent = ReminderAgent(
        reminder_service=mock_reminder_service,
        settings=None
    )
    agent.ai_service = mock_ai_service_success

    ctx = AgentContext(patient_id="patient-123")
    res = await agent.run("Remind me to take Aspirin daily at 8 AM", ctx)

    assert res.success is True
    assert isinstance(res.response, ReminderAgentResponse)
    assert res.response.status == "success"
    assert res.response.action == "create_medication_reminder"
    assert res.response.created_reminder is not None
    assert res.response.created_reminder["title"] == "Take Aspirin"
    
    mock_reminder_service.create_reminder.assert_called_once()
    mock_drug_agent_no_interaction.run.assert_called_once()


@pytest.mark.asyncio
async def test_reminder_agent_create_blocked_by_safety(
    mock_reminder_service,
    mock_ai_service_success,
    mock_drug_agent_high_interaction,
    monkeypatch
):
    monkeypatch.setattr("app.core.dependencies.get_drug_interaction_agent", lambda: mock_drug_agent_high_interaction)
    
    mock_ctx_service = MagicMock()
    mock_ctx_service.assemble_context = AsyncMock(return_value=None)
    monkeypatch.setattr("app.core.dependencies.get_patient_context_service", lambda: mock_ctx_service)

    agent = ReminderAgent(
        reminder_service=mock_reminder_service,
        settings=None
    )
    agent.ai_service = mock_ai_service_success

    ctx = AgentContext(patient_id="patient-123")
    res = await agent.run("Remind me to take Aspirin daily at 8 AM", ctx)

    # Should report failed/aborted response status due to High Severity safety interaction checks
    assert res.success is False
    assert "Blocked" in res.message
    assert res.response.status == "failed"
    assert "bleeding risk" in res.response.warnings[0]
    
    # Verify Reminder creation service was never called (aborted for safety!)
    mock_reminder_service.create_reminder.assert_not_called()
    mock_drug_agent_high_interaction.run.assert_called_once()
