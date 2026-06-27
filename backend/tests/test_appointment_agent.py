"""
Nura - Unit tests for AppointmentAgent
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.operations.appointment_agent import AppointmentAgent
from app.agents.base.context import AgentContext
from app.agents.operations.schemas import AppointmentAgentResponse
from app.models.appointment import AppointmentInDB, AppointmentStatus, PaymentStatus
from app.models.doctor import DoctorAvailabilityInDB, DayOfWeek
from datetime import datetime, timezone


@pytest.fixture
def mock_appointment_service():
    service = MagicMock()
    
    mock_appt = AppointmentInDB(
        id="appt-999",
        patient_id="patient-123",
        doctor_id="doctor-456",
        availability_id="slot-777",
        slot_date="2026-06-29",
        slot_time="10:00",
        duration_minutes=30,
        consultation_fee=500.0,
        status=AppointmentStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        reason="Checkup",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    service.create_appointment = AsyncMock(return_value=mock_appt)
    service.cancel_patient_appointment = AsyncMock(return_value=mock_appt)
    service.get_appointment_by_id = AsyncMock(return_value=mock_appt)
    service.list_patient_appointments_history = AsyncMock(return_value=[])

    mock_res_schema = MagicMock()
    mock_res_schema.model_dump = MagicMock(return_value={
        "id": "appt-999",
        "patient_id": "patient-123",
        "doctor_id": "doctor-456",
        "availability_id": "slot-777",
        "slot_date": "2026-06-29",
        "slot_time": "10:00",
        "duration_minutes": 30,
        "consultation_fee": 500.0,
        "status": "pending",
        "payment_status": "pending"
    })
    service.to_response = MagicMock(return_value=mock_res_schema)
    return service


@pytest.fixture
def mock_doctor_profile_service():
    service = MagicMock()
    
    mock_discovery = MagicMock()
    mock_discovery.model_dump = MagicMock(return_value={
        "id": "doctor-456",
        "user_id": "user-doctor",
        "name": "Dr. Sarah Jenkins",
        "specialization": "Dermatology",
        "hospital": "Nura Clinic"
    })
    service.search_verified_doctors = AsyncMock(return_value=[mock_discovery])
    return service


@pytest.fixture
def mock_doctor_availability_service():
    service = MagicMock()
    
    mock_slot = DoctorAvailabilityInDB(
        id="slot-777",
        doctor_id="doctor-456",
        date="2026-06-29",
        day_of_week=DayOfWeek.MONDAY,
        start_time="10:00",
        end_time="10:30",
        slot_duration=30,
        is_available=True,
        active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    service.get_active_availability = AsyncMock(return_value=[mock_slot])
    service.update_availability = AsyncMock(return_value=mock_slot)
    return service


@pytest.fixture
def mock_ai_service_search():
    service = MagicMock()
    mock_res = MagicMock()
    mock_res.response = """
    {
      "action": "search_doctors",
      "parameters": {
        "doctor_name": null,
        "specialization": "Dermatology"
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
def mock_ai_service_book():
    service = MagicMock()
    mock_res = MagicMock()
    mock_res.response = """
    {
      "action": "book_appointment",
      "parameters": {
        "doctor_id": "doctor-456",
        "availability_id": "slot-777",
        "reason": "Acne checkup"
      }
    }
    """
    mock_res.prompt_tokens = 100
    mock_res.completion_tokens = 50
    mock_res.total_tokens = 150
    mock_res.estimated_cost = 0.002
    service.generate = AsyncMock(return_value=mock_res)
    return service


@pytest.mark.asyncio
async def test_appointment_agent_search(
    mock_appointment_service,
    mock_doctor_profile_service,
    mock_doctor_availability_service,
    mock_ai_service_search,
    monkeypatch
):
    mock_ctx_service = MagicMock()
    mock_ctx_service.assemble_context = AsyncMock(return_value=None)
    monkeypatch.setattr("app.core.dependencies.get_patient_context_service", lambda: mock_ctx_service)

    agent = AppointmentAgent(
        appointment_service=mock_appointment_service,
        doctor_service=mock_doctor_profile_service,
        availability_service=mock_doctor_availability_service,
        settings=None
    )
    agent.ai_service = mock_ai_service_search

    ctx = AgentContext(patient_id="patient-123")
    res = await agent.run("Find dermatologist specialized in acne", ctx)

    assert res.success is True
    assert isinstance(res.response, AppointmentAgentResponse)
    assert res.response.action == "search_doctors"
    assert len(res.response.search_results) == 1
    assert res.response.search_results[0]["name"] == "Dr. Sarah Jenkins"
    
    mock_doctor_profile_service.search_verified_doctors.assert_called_once_with(
        name_query=None,
        specialization="Dermatology"
    )


@pytest.mark.asyncio
async def test_appointment_agent_book(
    mock_appointment_service,
    mock_doctor_profile_service,
    mock_doctor_availability_service,
    mock_ai_service_book,
    monkeypatch
):
    mock_ctx_service = MagicMock()
    mock_ctx_service.assemble_context = AsyncMock(return_value=None)
    monkeypatch.setattr("app.core.dependencies.get_patient_context_service", lambda: mock_ctx_service)

    agent = AppointmentAgent(
        appointment_service=mock_appointment_service,
        doctor_service=mock_doctor_profile_service,
        availability_service=mock_doctor_availability_service,
        settings=None
    )
    agent.ai_service = mock_ai_service_book

    ctx = AgentContext(patient_id="patient-123")
    res = await agent.run("Book slot 777 for doctor 456 due to acne", ctx)

    assert res.success is True
    assert isinstance(res.response, AppointmentAgentResponse)
    assert res.response.action == "book_appointment"
    assert res.response.appointment is not None
    assert res.response.appointment["id"] == "appt-999"
    
    mock_appointment_service.create_appointment.assert_called_once()
    mock_doctor_availability_service.update_availability.assert_called_once()
