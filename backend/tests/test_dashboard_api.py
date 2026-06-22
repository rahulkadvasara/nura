"""
Nura - Dashboard API Tests
Tests for GET /api/v1/dashboard/patient, /doctor, and /admin endpoints
covering role protection and successful data retrieval
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_current_user, get_auth_service
from app.core.dependencies import (
    get_patient_dashboard_service,
    get_doctor_dashboard_service,
    get_admin_dashboard_service,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.schemas.dashboard import (
    PatientDashboardResponse,
    DoctorDashboardResponse,
    AdminDashboardResponse,
    RecentHealthInsight,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Fixtures: Test users per role
# ---------------------------------------------------------------------------

def _make_user(user_id: str, role: UserRole) -> UserInDB:
    now = utc_now()
    return UserInDB(
        id=user_id,
        email=f"{role.value}@example.com",
        password_hash="hashed",
        full_name=f"Test {role.value.capitalize()}",
        role=role,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


PATIENT_USER = _make_user("patient_001", UserRole.PATIENT)
DOCTOR_USER = _make_user("doctor_001", UserRole.DOCTOR)
ADMIN_USER = _make_user("admin_001", UserRole.ADMIN)


def _patient_dashboard_data() -> PatientDashboardResponse:
    return PatientDashboardResponse(
        upcoming_appointments_count=3,
        active_reminders_count=5,
        reports_count=7,
        unread_notifications_count=2,
        recent_health_insights=[
            RecentHealthInsight(
                id="ins001",
                title="Elevated Cholesterol",
                severity="high",
                created_at=utc_now(),
            )
        ],
    )


def _doctor_dashboard_data() -> DoctorDashboardResponse:
    return DoctorDashboardResponse(
        todays_appointments_count=4,
        upcoming_appointments_count=6,
        total_patients_count=22,
        pending_approvals_count=2,
        wallet_balance=12500.0,
        total_earnings=45000.0,
    )


def _admin_dashboard_data() -> AdminDashboardResponse:
    return AdminDashboardResponse(
        total_users_count=100,
        total_patients_count=80,
        total_doctors_count=20,
        pending_doctor_verifications_count=5,
        total_appointments_count=300,
        total_revenue=150000.0,
        platform_earnings=22500.0,
        active_consultations_count=45,
        reports_count=120,
        reminders_count=65,
        active_chats_count=15,
        verified_doctors_count=15,
    )



# ---------------------------------------------------------------------------
# Client fixture
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def _mock_auth_service(current_user: UserInDB):
    """Create an auth_service mock that always passes require_role validation."""
    auth_svc = MagicMock()
    auth_svc.require_role = MagicMock(return_value=None)  # Never raise
    auth_svc.user_service = MagicMock()
    return auth_svc


# ---------------------------------------------------------------------------
# Patient dashboard tests
# ---------------------------------------------------------------------------

class TestPatientDashboardAPI:

    def test_patient_can_access_patient_dashboard(self, client):
        """Patient role can successfully access GET /dashboard/patient"""
        patient_svc = AsyncMock()
        patient_svc.get_dashboard = AsyncMock(return_value=_patient_dashboard_data())

        app.dependency_overrides[get_current_user] = lambda: PATIENT_USER
        app.dependency_overrides[get_auth_service] = lambda: _mock_auth_service(PATIENT_USER)
        app.dependency_overrides[get_patient_dashboard_service] = lambda: patient_svc

        response = client.get("/api/v1/dashboard/patient")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["upcoming_appointments_count"] == 3
        assert data["data"]["active_reminders_count"] == 5
        assert data["data"]["reports_count"] == 7
        assert data["data"]["unread_notifications_count"] == 2
        assert len(data["data"]["recent_health_insights"]) == 1

    def test_doctor_blocked_from_patient_dashboard(self, client):
        """Doctor role is blocked from GET /dashboard/patient (403)"""
        auth_svc = MagicMock()
        auth_svc.require_role = MagicMock(side_effect=PermissionError("Insufficient role"))
        auth_svc.user_service = MagicMock()

        app.dependency_overrides[get_current_user] = lambda: DOCTOR_USER
        app.dependency_overrides[get_auth_service] = lambda: auth_svc

        response = client.get("/api/v1/dashboard/patient")
        assert response.status_code == 403

    def test_admin_blocked_from_patient_dashboard(self, client):
        """Admin role is blocked from GET /dashboard/patient (403)"""
        auth_svc = MagicMock()
        auth_svc.require_role = MagicMock(side_effect=PermissionError("Insufficient role"))
        auth_svc.user_service = MagicMock()

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_auth_service] = lambda: auth_svc

        response = client.get("/api/v1/dashboard/patient")
        assert response.status_code == 403

    def test_unauthenticated_blocked_from_patient_dashboard(self, client):
        """Unauthenticated request is rejected (401/403) from patient dashboard"""
        response = client.get("/api/v1/dashboard/patient")
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Doctor dashboard tests
# ---------------------------------------------------------------------------

class TestDoctorDashboardAPI:

    def test_doctor_can_access_doctor_dashboard(self, client):
        """Doctor role can successfully access GET /dashboard/doctor"""
        doctor_svc = AsyncMock()
        doctor_svc.get_dashboard = AsyncMock(return_value=_doctor_dashboard_data())

        app.dependency_overrides[get_current_user] = lambda: DOCTOR_USER
        app.dependency_overrides[get_auth_service] = lambda: _mock_auth_service(DOCTOR_USER)
        app.dependency_overrides[get_doctor_dashboard_service] = lambda: doctor_svc

        response = client.get("/api/v1/dashboard/doctor")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["todays_appointments_count"] == 4
        assert data["data"]["upcoming_appointments_count"] == 6
        assert data["data"]["total_patients_count"] == 22
        assert data["data"]["pending_approvals_count"] == 2
        assert data["data"]["wallet_balance"] == 12500.0
        assert data["data"]["total_earnings"] == 45000.0

    def test_patient_blocked_from_doctor_dashboard(self, client):
        """Patient role is blocked from GET /dashboard/doctor (403)"""
        auth_svc = MagicMock()
        auth_svc.require_role = MagicMock(side_effect=PermissionError("Insufficient role"))
        auth_svc.user_service = MagicMock()

        app.dependency_overrides[get_current_user] = lambda: PATIENT_USER
        app.dependency_overrides[get_auth_service] = lambda: auth_svc

        response = client.get("/api/v1/dashboard/doctor")
        assert response.status_code == 403

    def test_unauthenticated_blocked_from_doctor_dashboard(self, client):
        """Unauthenticated request is rejected from doctor dashboard"""
        response = client.get("/api/v1/dashboard/doctor")
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Admin dashboard tests
# ---------------------------------------------------------------------------

class TestAdminDashboardAPI:

    def test_admin_can_access_admin_dashboard(self, client):
        """Admin role can successfully access GET /dashboard/admin"""
        admin_svc = AsyncMock()
        admin_svc.get_dashboard = AsyncMock(return_value=_admin_dashboard_data())

        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
        app.dependency_overrides[get_auth_service] = lambda: _mock_auth_service(ADMIN_USER)
        app.dependency_overrides[get_admin_dashboard_service] = lambda: admin_svc

        response = client.get("/api/v1/dashboard/admin")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_users_count"] == 100
        assert data["data"]["total_patients_count"] == 80
        assert data["data"]["total_doctors_count"] == 20
        assert data["data"]["pending_doctor_verifications_count"] == 5
        assert data["data"]["total_appointments_count"] == 300
        assert data["data"]["total_revenue"] == 150000.0
        assert data["data"]["platform_earnings"] == 22500.0
        assert data["data"]["active_consultations_count"] == 45
        assert data["data"]["reports_count"] == 120
        assert data["data"]["reminders_count"] == 65
        assert data["data"]["active_chats_count"] == 15
        assert data["data"]["verified_doctors_count"] == 15


    def test_patient_blocked_from_admin_dashboard(self, client):
        """Patient role is blocked from GET /dashboard/admin (403)"""
        auth_svc = MagicMock()
        auth_svc.require_role = MagicMock(side_effect=PermissionError("Insufficient role"))
        auth_svc.user_service = MagicMock()

        app.dependency_overrides[get_current_user] = lambda: PATIENT_USER
        app.dependency_overrides[get_auth_service] = lambda: auth_svc

        response = client.get("/api/v1/dashboard/admin")
        assert response.status_code == 403

    def test_doctor_blocked_from_admin_dashboard(self, client):
        """Doctor role is blocked from GET /dashboard/admin (403)"""
        auth_svc = MagicMock()
        auth_svc.require_role = MagicMock(side_effect=PermissionError("Insufficient role"))
        auth_svc.user_service = MagicMock()

        app.dependency_overrides[get_current_user] = lambda: DOCTOR_USER
        app.dependency_overrides[get_auth_service] = lambda: auth_svc

        response = client.get("/api/v1/dashboard/admin")
        assert response.status_code == 403

    def test_unauthenticated_blocked_from_admin_dashboard(self, client):
        """Unauthenticated request is rejected from admin dashboard"""
        response = client.get("/api/v1/dashboard/admin")
        assert response.status_code in (401, 403)
