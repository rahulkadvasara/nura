import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.services.drug_safety.medication_collector import MedicationCollector
from app.services.drug_safety.decision_engine import ValidationDecisionEngine
from app.services.drug_safety.validation_service import MedicationValidationService
from app.services.drug_safety.normalizer import DrugNormalizer
from app.services.drug_safety.interaction_engine import DrugInteractionEngine
from app.services.drug_safety.telemetry import drug_safety_telemetry
from app.services.drug_safety.models import DrugCheckResponse, InteractionPairDetail
from app.models.reminder import ReminderInDB, ReminderType, ReminderStatus
from app.models.report import ReportInDB
from app.models.patient_memory import PatientMemoryInDB


@pytest.fixture
def mock_normalizer():
    norm = MagicMock(spec=DrugNormalizer)
    # Simple normalizer mock: returns uppercase stripped string
    norm.normalize.side_effect = lambda name: name.strip().upper() if name else None
    return norm


@pytest.fixture
def mock_repositories():
    pres_repo = AsyncMock()
    rem_repo = AsyncMock()
    rep_repo = AsyncMock()
    pm_repo = AsyncMock()
    return pres_repo, rem_repo, rep_repo, pm_repo


@pytest.mark.asyncio
async def test_medication_collector(mock_normalizer, mock_repositories):
    pres_repo, rem_repo, rep_repo, pm_repo = mock_repositories

    # Mock Prescriptions
    mock_med1 = MagicMock()
    mock_med1.drug_name = "Aspirin"
    mock_pres = MagicMock()
    mock_pres.medications = [mock_med1]
    pres_repo.get_by_patient_id.return_value = [mock_pres]

    # Mock Reminders
    mock_rem = ReminderInDB(
        id="rem-1",
        patient_id="pat-123",
        reminder_type=ReminderType.MEDICATION,
        title="Take Warfarin",
        description="",
        scheduled_time="08:00",
        recurrence="daily",
        status=ReminderStatus.ACTIVE
    )
    rem_repo.get_active_reminders.return_value = [mock_rem]

    # Mock Reports
    mock_rep = MagicMock()
    mock_rep.medications = [{"drug_name": "Lisinopril"}]
    rep_repo.get_by_patient_id.return_value = [mock_rep]

    # Mock Patient Memory
    mock_pm = MagicMock()
    mock_pm.medications = ["Metformin"]
    mock_pm.medication_history = [{"medicine": "Ibuprofen"}]
    pm_repo.get_by_patient_id.return_value = mock_pm

    collector = MedicationCollector(
        prescription_repository=pres_repo,
        reminder_repository=rem_repo,
        report_repository=rep_repo,
        patient_memory_repository=pm_repo,
        normalizer=mock_normalizer
    )

    collected = await collector.collect("pat-123")
    
    # Assertions
    assert "ASPIRIN" in collected
    assert "WARFARIN" in collected
    assert "LISINOPRIL" in collected
    assert "METFORMIN" in collected
    assert "IBUPROFEN" in collected
    assert len(collected) == 5


@pytest.mark.asyncio
async def test_decision_engine_allow(mock_normalizer):
    interaction_engine = AsyncMock(spec=DrugInteractionEngine)
    # Mock no interactions found
    interaction_engine.check_interactions.return_value = DrugCheckResponse(
        medications=["ASPIRIN", "METFORMIN"],
        normalized_medications=["ASPIRIN", "METFORMIN"],
        detected_interactions=[],
        severity="NONE",
        recommendations=["No known interactions detected."],
        statistics={},
        latency_ms=10.0
    )

    engine = ValidationDecisionEngine(interaction_engine, mock_normalizer)
    result = await engine.evaluate(
        current_normalized=["ASPIRIN"],
        incoming_raw=["Metformin"]
    )

    assert result["decision"] == "ALLOW"
    assert result["severity"] == "NONE"
    assert len(result["detected_interactions"]) == 0
    assert len(result["recommendations"]) > 0
    assert "No known interactions detected." in result["recommendations"][0]


@pytest.mark.asyncio
async def test_decision_engine_block(mock_normalizer):
    interaction_engine = AsyncMock(spec=DrugInteractionEngine)
    # Mock high severity interaction found
    interaction = InteractionPairDetail(
        drug_a="ASPIRIN",
        drug_b="WARFARIN",
        drug_a_normalized="ASPIRIN",
        drug_b_normalized="WARFARIN",
        severity="HIGH",
        description="Increased risk of bleeding."
    )
    interaction_engine.check_interactions.return_value = DrugCheckResponse(
        medications=["ASPIRIN", "WARFARIN"],
        normalized_medications=["ASPIRIN", "WARFARIN"],
        detected_interactions=[interaction],
        severity="HIGH",
        recommendations=["Increased bleeding risk recommended action."],
        statistics={},
        latency_ms=10.0
    )

    engine = ValidationDecisionEngine(interaction_engine, mock_normalizer)
    result = await engine.evaluate(
        current_normalized=["ASPIRIN"],
        incoming_raw=["Warfarin"]
    )

    assert result["decision"] == "BLOCK"
    assert result["severity"] == "HIGH"
    assert len(result["detected_interactions"]) == 1
    assert result["detected_interactions"][0].description == "Increased risk of bleeding."


@pytest.mark.asyncio
async def test_validation_service(mock_normalizer, mock_repositories):
    pres_repo, rem_repo, rep_repo, pm_repo = mock_repositories
    db = MagicMock()
    db.patient_memory = pm_repo.collection

    # Set up collector mock
    collector = AsyncMock(spec=MedicationCollector)
    collector.collect.return_value = ["ASPIRIN"]

    # Set up decision engine mock
    decision_engine = AsyncMock(spec=ValidationDecisionEngine)
    decision_engine.evaluate.return_value = {
        "decision": "ALLOW",
        "severity": "NONE",
        "detected_interactions": [],
        "recommendations": ["Safe to proceed."]
    }

    interaction_engine = AsyncMock(spec=DrugInteractionEngine)

    # Telemetry check before
    drug_safety_telemetry.reset()
    stats_before = drug_safety_telemetry.get_statistics()
    assert stats_before["validation_checks"] == 0

    service = MedicationValidationService(db, collector, decision_engine, interaction_engine)
    res = await service.validate_medications("pat-123", ["Metformin"], source="reminder")

    assert res["decision"] == "ALLOW"
    stats_after = drug_safety_telemetry.get_statistics()
    assert stats_after["validation_checks"] == 1
    assert stats_after["reminder_validations"] == 1
    assert stats_after["allow_decisions"] == 1


@pytest.mark.asyncio
async def test_validation_and_update_patient_memory(mock_normalizer, mock_repositories):
    pres_repo, rem_repo, rep_repo, pm_repo = mock_repositories
    
    # Mock collection update
    mock_col = AsyncMock()
    db = MagicMock()
    db.patient_memory = mock_col

    collector = AsyncMock(spec=MedicationCollector)
    collector.collect.return_value = ["ASPIRIN", "WARFARIN"]

    interaction = InteractionPairDetail(
        drug_a="ASPIRIN",
        drug_b="WARFARIN",
        drug_a_normalized="ASPIRIN",
        drug_b_normalized="WARFARIN",
        severity="HIGH",
        description="Bleeding danger"
    )
    interaction_engine = AsyncMock(spec=DrugInteractionEngine)
    interaction_engine.check_interactions.return_value = DrugCheckResponse(
        medications=["ASPIRIN", "WARFARIN"],
        normalized_medications=["ASPIRIN", "WARFARIN"],
        detected_interactions=[interaction],
        severity="HIGH",
        recommendations=["Avoid concurrent use."],
        statistics={},
        latency_ms=10.0
    )

    decision_engine = AsyncMock(spec=ValidationDecisionEngine)
    service = MedicationValidationService(db, collector, decision_engine, interaction_engine)
    
    summary = await service.validate_and_update_patient_memory("pat-123")

    assert summary is not None
    assert summary["active_interaction_count"] == 1
    assert summary["highest_severity"] == "HIGH"
    
    # Verify update called
    mock_col.update_one.assert_called_once()
    args, kwargs = mock_col.update_one.call_args
    assert args[0] == {"patient_id": "pat-123"}
    assert "$set" in args[1]
    assert "validation_summary" in args[1]["$set"]
    assert args[1]["$set"]["validation_summary"]["highest_severity"] == "HIGH"
