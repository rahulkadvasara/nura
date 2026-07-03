import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.services.chat.deep_link_service import DeepLinkService
from app.services.chat.action_builder import ActionBuilder
from app.services.chat.rich_card_service import RichCardService
from app.services.chat.context_resolver import HealthcareContextResolver

from app.models.report import ReportInDB, ReportType, RiskLevel, ProcessingStatus
from app.models.reminder import ReminderInDB, ReminderType, ReminderStatus
from app.models.appointment import AppointmentInDB, AppointmentStatus, PaymentStatus, Medication
from app.models.doctor import DoctorProfileInDB, DoctorProfileStatus


def test_deep_link_service():
    assert DeepLinkService.get_report_link("rep123") == "/dashboard/records/rep123"
    assert DeepLinkService.get_reminder_link() == "/dashboard/reminders"
    assert DeepLinkService.get_appointment_link() == "/dashboard/appointments"
    assert DeepLinkService.get_doctor_link("doc123") == "/dashboard/doctors/doc123"
    assert DeepLinkService.get_drug_safety_link() == "/dashboard/patient"
    assert DeepLinkService.get_risk_analysis_link("rep123") == "/dashboard/records/rep123"


def test_action_builder():
    act = ActionBuilder.open_report("rep123")
    assert act.action_type == "OPEN_REPORT"
    assert act.label == "Open Report"
    assert act.url == "/dashboard/records/rep123"

    act = ActionBuilder.download_report("rep123")
    assert act.action_type == "DOWNLOAD_REPORT"
    assert act.url == "/api/v1/reports/rep123/download"

    act = ActionBuilder.view_doctor("doc123")
    assert act.action_type == "VIEW_DOCTOR"
    assert act.url == "/dashboard/doctors/doc123"

    act = ActionBuilder.book_appointment()
    assert act.action_type == "BOOK_APPOINTMENT"
    assert act.url == "/dashboard/appointments"

    act = ActionBuilder.create_reminder()
    assert act.action_type == "CREATE_REMINDER"
    assert act.url == "/dashboard/reminders"


def test_rich_card_service():
    service = RichCardService()

    # Create dummy records
    report = ReportInDB(
        id="rep1",
        patient_id="pat1",
        uploaded_by="pat1",
        report_type=ReportType.BLOOD_TEST,
        file_url="http://example.com/file.pdf",
        raw_text="Sample raw text",
        structured_data={},
        entities=[],
        ai_summary="This is a summary of the report",
        risk_level=RiskLevel.LOW,
        processing_status=ProcessingStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    reminder = ReminderInDB(
        id="rem1",
        patient_id="pat1",
        reminder_type=ReminderType.MEDICATION,
        title="Take Aspirin",
        description="Daily after breakfast",
        scheduled_time="08:00 AM",
        status=ReminderStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    resolved = {
        "reports": [report],
        "reminders": [reminder]
    }

    cards = service.build_cards(resolved)
    assert len(cards) == 2
    assert cards[0].card_type == "report"
    assert cards[0].title == "Medical Report"
    assert cards[0].summary == "This is a summary of the report"
    assert len(cards[0].actions) == 2
    assert cards[0].actions[0].action_type == "OPEN_REPORT"

    assert cards[1].card_type == "reminder"
    assert cards[1].title == "Take Aspirin"


@pytest.mark.asyncio
async def test_context_resolver():
    report_service = AsyncMock()
    reminder_service = AsyncMock()
    appointment_service = AsyncMock()
    prescription_service = AsyncMock()
    doctor_service = AsyncMock()
    database = AsyncMock()

    # Setup dummy database collections
    database.patient_memory = AsyncMock()
    database.patient_memory.find_one.return_value = {
        "patient_id": "pat1",
        "validation_summary": {
            "overall_severity": "WARNING",
            "active_interaction_count": 1,
            "summary": "1 warning detected"
        }
    }

    resolver = HealthcareContextResolver(
        report_service=report_service,
        reminder_service=reminder_service,
        appointment_service=appointment_service,
        prescription_service=prescription_service,
        doctor_service=doctor_service,
        database=database
    )

    # 1. Test "report" trigger
    report_service.list_reports_by_patient.return_value = [AsyncMock(id="rep1", document_type="Blood Report")]
    res = await resolver.resolve_context("pat1", "Check my latest report")
    assert "reports" in res
    report_service.list_reports_by_patient.assert_called_once_with("pat1", limit=5)

    # 2. Test "medication" and "safety" trigger
    prescription_service.list_prescriptions_by_patient.return_value = [AsyncMock(id="pr1")]
    res = await resolver.resolve_context("pat1", "Is my medication safe?")
    assert "prescriptions" in res
    assert "drug_safety" in res
    assert res["drug_safety"]["overall_severity"] == "WARNING"
