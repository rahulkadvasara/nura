import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_prescription_service,
    get_consultation_service,
    get_notification_service,
    get_audit_log_service,
    get_appointment_service,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.models.appointment import AppointmentInDB, AppointmentStatus, PaymentStatus, ConsultationInDB, PrescriptionInDB, Medication
from app.models.doctor import DoctorProfileInDB, DoctorProfileStatus
from app.schemas.appointment import PrescriptionResponse, PatientPrescriptionResponse, PatientConsultationItemResponse
from app.services.prescription_service import _prescription_to_response

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

@pytest.fixture
def client():
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def doctor_user():
    now = utc_now()
    return UserInDB(
        id="507f1f77bcf86cd799439002",
        email="doctor@example.com",
        password_hash="hashed_pw",
        full_name="Doctor Name",
        role=UserRole.DOCTOR,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def patient_user():
    now = utc_now()
    return UserInDB(
        id="507f1f77bcf86cd799439001",
        email="patient@example.com",
        password_hash="hashed_pw",
        full_name="Patient Name",
        role=UserRole.PATIENT,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def doctor_profile():
    now = utc_now()
    return DoctorProfileInDB(
        id="507f1f77bcf86cd799439010",
        user_id="507f1f77bcf86cd799439002",
        specialization="Cardiology",
        qualifications=["MBBS"],
        experience_years=10,
        consultation_fee=500.0,
        bio="Cardiologist",
        languages=["English"],
        profile_status=DoctorProfileStatus.VERIFIED,
        average_rating=4.8,
        total_reviews=12,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def sample_consultation():
    now = utc_now()
    return ConsultationInDB(
        id="507f1f77bcf86cd799439080",
        appointment_id="507f1f77bcf86cd799439050",
        patient_id="507f1f77bcf86cd799439001",
        doctor_id="507f1f77bcf86cd799439010",
        consultation_notes="Patient is doing fine.",
        diagnosis="Common Cold",
        recommendations="Rest",
        follow_up_required=False,
        follow_up_date=None,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def sample_prescription():
    now = utc_now()
    return PrescriptionInDB(
        id="507f1f77bcf86cd799439090",
        consultation_id="507f1f77bcf86cd799439080",
        patient_id="507f1f77bcf86cd799439001",
        doctor_id="507f1f77bcf86cd799439010",
        medications=[
            Medication(
                drug_name="Aspirin",
                dosage="500mg",
                frequency="Once daily",
                duration="5 days",
                instructions="Take with water"
            )
        ],
        dosage_instructions="Take medications after meals.",
        notes="General prescription notes",
        created_at=now,
        updated_at=now
    )


def test_doctor_create_prescription_success(client, doctor_user, doctor_profile, sample_prescription):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    from app.core.dependencies import get_doctor_profile_service
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = doctor_profile
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    mock_service = AsyncMock()
    mock_service.create_prescription.return_value = sample_prescription
    mock_service.to_response = _prescription_to_response
    app.dependency_overrides[get_prescription_service] = lambda: mock_service

    mock_notif = AsyncMock()
    app.dependency_overrides[get_notification_service] = lambda: mock_notif
    mock_audit = AsyncMock()
    app.dependency_overrides[get_audit_log_service] = lambda: mock_audit

    payload = {
        "medications": [
            {
                "drug_name": "Aspirin",
                "dosage": "500mg",
                "frequency": "Once daily",
                "duration": "5 days",
                "instructions": "Take with water"
            }
        ],
        "dosage_instructions": "Take medications after meals.",
        "notes": "General prescription notes"
    }

    response = client.post(
        "/api/v1/doctor/consultations/507f1f77bcf86cd799439080/prescription",
        json=payload
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == "507f1f77bcf86cd799439090"
    assert len(data["data"]["medications"]) == 1
    assert data["data"]["medications"][0]["drug_name"] == "Aspirin"
    assert data["data"]["medications"][0]["instructions"] == "Take with water"


def test_create_prescription_duplicate_fails(client, doctor_user, doctor_profile):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    from app.core.dependencies import get_doctor_profile_service
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = doctor_profile
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    mock_service = AsyncMock()
    mock_service.create_prescription.side_effect = ValueError("A prescription has already been created for consultation")
    app.dependency_overrides[get_prescription_service] = lambda: mock_service

    payload = {
        "medications": [{"drug_name": "Aspirin", "dosage": "500mg", "frequency": "Once daily", "duration": "5 days"}],
    }

    response = client.post(
        "/api/v1/doctor/consultations/507f1f77bcf86cd799439080/prescription",
        json=payload
    )
    assert response.status_code == 400
    assert "already been created" in response.json()["message"]


def test_doctor_update_prescription_success(client, doctor_user, doctor_profile, sample_prescription):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    from app.core.dependencies import get_doctor_profile_service
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = doctor_profile
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    mock_service = AsyncMock()
    mock_service.update_prescription.return_value = sample_prescription
    mock_service.to_response = _prescription_to_response
    app.dependency_overrides[get_prescription_service] = lambda: mock_service

    mock_appt_service = AsyncMock()
    app.dependency_overrides[get_appointment_service] = lambda: mock_appt_service
    mock_audit = AsyncMock()
    app.dependency_overrides[get_audit_log_service] = lambda: mock_audit

    payload = {
        "medications": [
            {
                "drug_name": "Aspirin Updated",
                "dosage": "1000mg",
                "frequency": "Twice daily",
                "duration": "10 days",
                "instructions": "Take with meals"
            }
        ],
        "dosage_instructions": "Updated dosage instructions"
    }

    response = client.put(
        "/api/v1/doctor/prescriptions/507f1f77bcf86cd799439090",
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_doctor_update_prescription_fails_not_completed(client, doctor_user, doctor_profile):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    from app.core.dependencies import get_doctor_profile_service
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = doctor_profile
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    mock_service = AsyncMock()
    mock_service.update_prescription.side_effect = ValueError("Prescription can only be updated while the consultation is completed")
    app.dependency_overrides[get_prescription_service] = lambda: mock_service

    payload = {
        "dosage_instructions": "Try updated instructions"
    }

    response = client.put(
        "/api/v1/doctor/prescriptions/507f1f77bcf86cd799439090",
        json=payload
    )
    assert response.status_code == 400
    assert "only be updated while the consultation is completed" in response.json()["message"]


def test_patient_view_prescriptions_and_consultations(client, patient_user, sample_prescription, sample_consultation):
    app.dependency_overrides[get_current_user] = lambda: patient_user

    mock_consultation_service = AsyncMock()
    mock_consultation_service.list_patient_consultation_history.return_value = [
        {
            "id": "507f1f77bcf86cd799439080",
            "appointment_id": "507f1f77bcf86cd799439050",
            "patient_id": "507f1f77bcf86cd799439001",
            "doctor_id": "507f1f77bcf86cd799439010",
            "doctor_name": "Doctor Name",
            "doctor_specialization": "Cardiology",
            "appointment_date": "2026-06-25",
            "appointment_time": "10:00",
            "diagnosis": "Common Cold",
            "consultation_notes": "Notes",
            "follow_up_required": False,
            "follow_up_date": None,
            "prescription_status": "Prescribed",
            "prescription_id": "507f1f77bcf86cd799439090",
            "created_at": utc_now(),
            "updated_at": utc_now()
        }
    ]
    app.dependency_overrides[get_consultation_service] = lambda: mock_consultation_service

    mock_prescription_service = AsyncMock()
    mock_prescription_service.list_prescriptions_by_patient.return_value = [sample_prescription]
    mock_prescription_service.get_prescription_by_id.return_value = sample_prescription
    app.dependency_overrides[get_prescription_service] = lambda: mock_prescription_service

    from app.core.dependencies import get_doctor_profile_repository, get_user_repository
    mock_doctor_repo = AsyncMock()
    mock_user_repo = AsyncMock()
    app.dependency_overrides[get_doctor_profile_repository] = lambda: mock_doctor_repo
    app.dependency_overrides[get_user_repository] = lambda: mock_user_repo

    # 1. Test get patient consultations
    response = client.get("/api/v1/patient/consultations")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["consultations"]) == 1
    assert data["data"]["consultations"][0]["doctor_name"] == "Doctor Name"

    # 2. Test get patient prescriptions
    response = client.get("/api/v1/patient/prescriptions")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_patient_view_prescriptions_forbidden_for_doctors(client, doctor_user):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    response = client.get("/api/v1/patient/prescriptions")
    assert response.status_code == 403
    assert "Only patients" in response.json()["message"]
