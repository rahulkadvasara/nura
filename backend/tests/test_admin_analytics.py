"""
Nura - Admin Analytics Service and API Tests
Unit and integration tests for platform operational analytics dashboard.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_auth_service,
    get_admin_analytics_service,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.services.admin_analytics_service import AdminAnalyticsService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user():
    now = utc_now()
    return UserInDB(
        id="admin_user_id",
        email="admin@example.com",
        password_hash="hashed",
        full_name="Admin User",
        role=UserRole.ADMIN,
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
        id="patient_user_id",
        email="patient@example.com",
        password_hash="hashed",
        full_name="Patient User",
        role=UserRole.PATIENT,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=now,
        updated_at=now
    )


class MockCursor:
    def __init__(self, result_list):
        self.result_list = result_list

    async def to_list(self, length=None):
        return self.result_list


def create_mock_collection(count_side_effect=None, aggregate_side_effect=None):
    col = MagicMock()
    if count_side_effect is not None:
        col.count_documents = AsyncMock(side_effect=count_side_effect)
    else:
        col.count_documents = AsyncMock(return_value=0)

    if aggregate_side_effect is not None:
        col.aggregate = MagicMock(side_effect=[MockCursor(r) for r in aggregate_side_effect])
    else:
        col.aggregate = MagicMock(return_value=MockCursor([]))
    return col


# ────────────────────────────────────────────────────────────────────────────
# 1. API Authorization Guard Tests
# ────────────────────────────────────────────────────────────────────────────

def test_analytics_endpoint_unauthorized_forbidden(client, patient_user):
    # Mock authentication to return a PATIENT user
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    # Mock require_role RBAC logic
    auth_svc = MagicMock()
    def mock_require_role(user, required_role):
        if user.role == UserRole.ADMIN:
            return
        raise PermissionError("Forbidden")
    auth_svc.require_role = mock_require_role
    app.dependency_overrides[get_auth_service] = lambda: auth_svc

    res = client.get("/api/v1/admin/analytics")
    assert res.status_code == 403
    assert "Forbidden" in res.json().get("message", "")


# ────────────────────────────────────────────────────────────────────────────
# 2. Aggregation Calculations Test
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analytics_aggregation_calculations():
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    # Mock count_documents side effects
    async def user_count_side_effect(filter_dict):
        if filter_dict.get("role") == "doctor" and filter_dict.get("is_active") is True:
            return 15
        if filter_dict.get("role") == "doctor":
            return 20
        if filter_dict.get("role") == "patient":
            return 70
        if filter_dict.get("role") == "admin":
            return 10
        if filter_dict.get("is_active") is True:
            return 90
        if filter_dict.get("is_active") is False:
            return 10
        if filter_dict == {}:
            return 100
        return 0

    async def doctor_count_side_effect(filter_dict):
        if filter_dict == {}:
            return 25
        if filter_dict.get("profile_status") == "verified":
            return 15
        if filter_dict.get("profile_status") == "pending":
            return 5
        if filter_dict.get("profile_status") == "rejected":
            return 3
        if filter_dict.get("profile_status") == "suspended":
            return 2
        return 0

    async def appointment_count_side_effect(filter_dict):
        if filter_dict == {}:
            return 200
        if filter_dict.get("status") == "pending":
            return 20
        if filter_dict.get("status") == "approved":
            return 30
        if filter_dict.get("status") == "completed":
            return 120
        if filter_dict.get("status") == "cancelled":
            return 20
        if filter_dict.get("status") == "rejected":
            return 10
        return 0

    # User aggregate outputs (7d, 30d)
    user_7d_agg = [{"_id": today_str, "count": 5}, {"_id": yesterday_str, "count": 3}]
    user_30d_agg = [{"_id": today_str, "count": 5}, {"_id": yesterday_str, "count": 3}]
    user_col = create_mock_collection(
        count_side_effect=user_count_side_effect,
        aggregate_side_effect=[user_7d_agg, user_30d_agg]
    )

    # Doctor collections
    doc_profile_col = create_mock_collection(count_side_effect=doctor_count_side_effect)
    doc_avail_col = create_mock_collection(aggregate_side_effect=[[{"count": 12}]])

    # Appointment aggregate outputs (7d, 30d)
    appt_7d_agg = [{"_id": today_str, "count": 10}, {"_id": yesterday_str, "count": 8}]
    appt_30d_agg = [{"_id": today_str, "count": 10}, {"_id": yesterday_str, "count": 8}]
    appt_col = create_mock_collection(
        count_side_effect=appointment_count_side_effect,
        aggregate_side_effect=[appt_7d_agg, appt_30d_agg]
    )

    # Revenue totals, 7d daily, 30d daily
    rev_totals = [{"total": 15000.0, "doctor": 12750.0, "platform": 2250.0}]
    rev_7d_agg = [{"_id": today_str, "total": 1000.0}, {"_id": yesterday_str, "total": 800.0}]
    rev_30d_agg = [{"_id": today_str, "total": 1000.0}, {"_id": yesterday_str, "total": 800.0}]
    payment_col = create_mock_collection(
        aggregate_side_effect=[rev_totals, rev_7d_agg, rev_30d_agg]
    )

    # Healthcare activity
    async def healthcare_count_side_effect(filter_dict):
        # We can map report, consult, prescription, active reminder
        return 50

    report_col = create_mock_collection(
        count_side_effect=lambda x: 15,
        aggregate_side_effect=[[{"_id": today_str, "count": 2}]]
    )
    consult_col = create_mock_collection(
        count_side_effect=lambda x: 120,
        aggregate_side_effect=[[{"_id": today_str, "count": 4}]]
    )
    prescription_col = create_mock_collection(count_side_effect=lambda x: 95)
    reminder_col = create_mock_collection(count_side_effect=lambda x: 45)

    service = AdminAnalyticsService(
        user_repository=MagicMock(collection=user_col),
        doctor_profile_repository=MagicMock(collection=doc_profile_col),
        doctor_availability_repository=MagicMock(collection=doc_avail_col),
        appointment_repository=MagicMock(collection=appt_col),
        payment_repository=MagicMock(collection=payment_col),
        consultation_repository=MagicMock(collection=consult_col),
        report_repository=MagicMock(collection=report_col),
        prescription_repository=MagicMock(collection=prescription_col),
        reminder_repository=MagicMock(collection=reminder_col)
    )

    result = await service.get_analytics()

    # Assert user metrics
    assert result["users"]["total_users"] == 100
    assert result["users"]["active_users"] == 90
    assert result["users"]["inactive_users"] == 10
    assert result["users"]["patients_count"] == 70
    assert result["users"]["doctors_count"] == 20
    assert result["users"]["admins_count"] == 10
    
    # Assert doctor metrics
    assert result["doctors"]["total_doctors"] == 25
    assert result["doctors"]["verified_doctors"] == 15
    assert result["doctors"]["pending_doctors"] == 5
    assert result["doctors"]["rejected_doctors"] == 3
    assert result["doctors"]["suspended_doctors"] == 2
    assert result["doctors"]["doctors_with_availability"] == 12
    assert result["doctors"]["active_doctors"] == 15

    # Assert appointment metrics
    assert result["appointments"]["total_appointments"] == 200
    assert result["appointments"]["pending_appointments"] == 20
    assert result["appointments"]["approved_appointments"] == 30
    assert result["appointments"]["completed_appointments"] == 120
    assert result["appointments"]["cancelled_appointments"] == 20
    assert result["appointments"]["rejected_appointments"] == 10

    # Assert revenue metrics
    assert result["revenue"]["total_revenue"] == 15000.0
    assert result["revenue"]["doctor_earnings"] == 12750.0
    assert result["revenue"]["platform_revenue"] == 2250.0

    # Assert healthcare activity
    assert result["healthcare"]["reports_uploaded"] == 15
    assert result["healthcare"]["consultations_completed"] == 120
    assert result["healthcare"]["prescriptions_created"] == 95
    assert result["healthcare"]["reminders_created"] == 45


# ────────────────────────────────────────────────────────────────────────────
# 3. Empty Database Graceful Fallback Test
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analytics_empty_database():
    user_col = create_mock_collection(aggregate_side_effect=[[], []])
    doc_profile_col = create_mock_collection()
    doc_avail_col = create_mock_collection(aggregate_side_effect=[[]])
    appt_col = create_mock_collection(aggregate_side_effect=[[], []])
    payment_col = create_mock_collection(aggregate_side_effect=[[], [], []])
    report_col = create_mock_collection(aggregate_side_effect=[[]])
    consult_col = create_mock_collection(aggregate_side_effect=[[]])
    prescription_col = create_mock_collection()
    reminder_col = create_mock_collection()

    service = AdminAnalyticsService(
        user_repository=MagicMock(collection=user_col),
        doctor_profile_repository=MagicMock(collection=doc_profile_col),
        doctor_availability_repository=MagicMock(collection=doc_avail_col),
        appointment_repository=MagicMock(collection=appt_col),
        payment_repository=MagicMock(collection=payment_col),
        consultation_repository=MagicMock(collection=consult_col),
        report_repository=MagicMock(collection=report_col),
        prescription_repository=MagicMock(collection=prescription_col),
        reminder_repository=MagicMock(collection=reminder_col)
    )

    result = await service.get_analytics()

    assert result["users"]["total_users"] == 0
    assert result["doctors"]["total_doctors"] == 0
    assert result["doctors"]["doctors_with_availability"] == 0
    assert result["revenue"]["total_revenue"] == 0.0
    assert result["revenue"]["doctor_earnings"] == 0.0
    assert result["revenue"]["platform_revenue"] == 0.0
    assert result["healthcare"]["reports_uploaded"] == 0


# ────────────────────────────────────────────────────────────────────────────
# 4. Chart Data Generation (Date Alignment) Test
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analytics_chart_data_generation():
    # Empty aggregations to let _fill_missing_dates do the work
    user_col = create_mock_collection(aggregate_side_effect=[[], []])
    doc_profile_col = create_mock_collection()
    doc_avail_col = create_mock_collection(aggregate_side_effect=[[]])
    appt_col = create_mock_collection(aggregate_side_effect=[[], []])
    payment_col = create_mock_collection(aggregate_side_effect=[[], [], []])
    report_col = create_mock_collection(aggregate_side_effect=[[]])
    consult_col = create_mock_collection(aggregate_side_effect=[[]])
    prescription_col = create_mock_collection()
    reminder_col = create_mock_collection()

    service = AdminAnalyticsService(
        user_repository=MagicMock(collection=user_col),
        doctor_profile_repository=MagicMock(collection=doc_profile_col),
        doctor_availability_repository=MagicMock(collection=doc_avail_col),
        appointment_repository=MagicMock(collection=appt_col),
        payment_repository=MagicMock(collection=payment_col),
        consultation_repository=MagicMock(collection=consult_col),
        report_repository=MagicMock(collection=report_col),
        prescription_repository=MagicMock(collection=prescription_col),
        reminder_repository=MagicMock(collection=reminder_col)
    )

    result = await service.get_analytics()

    # Confirms the dates returned cover exactly the last 7 and 30 days
    users_7 = result["users"]["users_last_7_days"]
    users_30 = result["users"]["users_last_30_days"]
    assert len(users_7) == 7
    assert len(users_30) == 30

    revenue_7 = result["revenue"]["revenue_last_7_days"]
    revenue_30 = result["revenue"]["revenue_last_30_days"]
    assert len(revenue_7) == 7
    assert len(revenue_30) == 30

    # Ensure format is YYYY-MM-DD
    for item in users_7:
        assert "date" in item
        assert "count" in item
        datetime.strptime(item["date"], "%Y-%m-%d")

    for item in revenue_30:
        assert "date" in item
        assert "amount" in item
        datetime.strptime(item["date"], "%Y-%m-%d")


# ────────────────────────────────────────────────────────────────────────────
# 5. Full End-to-End Endpoint Test with Admin User
# ────────────────────────────────────────────────────────────────────────────

def test_analytics_endpoint_success_with_admin(client, admin_user):
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    # Mock require_role RBAC logic
    auth_svc = MagicMock()
    auth_svc.require_role = MagicMock() # success for admin
    app.dependency_overrides[get_auth_service] = lambda: auth_svc

    # Mock AdminAnalyticsService
    async def mock_get_analytics():
        return {
            "users": {"total_users": 10, "users_last_7_days": [], "users_last_30_days": []},
            "doctors": {"total_doctors": 5},
            "appointments": {"total_appointments": 2, "appointments_last_7_days": [], "appointments_last_30_days": []},
            "revenue": {"total_revenue": 1000.0, "revenue_last_7_days": [], "revenue_last_30_days": []},
            "healthcare": {"reports_uploaded": 1, "reports_last_30_days": [], "consultations_last_30_days": []}
        }
    
    mock_service = MagicMock()
    mock_service.get_analytics = mock_get_analytics
    app.dependency_overrides[get_admin_analytics_service] = lambda: mock_service

    res = client.get("/api/v1/admin/analytics")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["message"] == "Platform analytics retrieved successfully"
    assert data["data"]["users"]["total_users"] == 10
    assert data["data"]["revenue"]["total_revenue"] == 1000.0
