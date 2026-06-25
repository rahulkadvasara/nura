"""
Nura - Payment History, Revenue Summary & Administration Tests
Unit and API integration tests for patient history, admin overview, revenue statistics, and auditing.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from bson import ObjectId

from app.main import app
from app.models.user import UserInDB, UserRole, AuthProvider
from app.models.payment import PaymentInDB, PaymentStatus, PaymentMethod
from app.models.doctor import DoctorProfileInDB, DoctorProfileStatus
from app.models.appointment import AppointmentInDB, AppointmentStatus, PaymentStatus as AppPaymentStatus
from app.core.dependencies import get_current_user, get_payment_service, get_doctor_earnings_service, get_audit_log_service
from app.services.payment_service import PaymentService
from app.services.doctor_earnings_service import DoctorEarningsService

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

@pytest.fixture
def client():
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def patient_user():
    return UserInDB(
        id="507f1f77bcf86cd799439101",
        role=UserRole.PATIENT,
        email="patient@example.com",
        password_hash="hash",
        full_name="John Patient",
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=utc_now(),
        updated_at=utc_now(),
    )

@pytest.fixture
def doctor_user():
    return UserInDB(
        id="507f1f77bcf86cd799439102",
        role=UserRole.DOCTOR,
        email="doctor@example.com",
        password_hash="hash",
        full_name="Dr. Smith",
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=utc_now(),
        updated_at=utc_now(),
    )

@pytest.fixture
def admin_user():
    return UserInDB(
        id="507f1f77bcf86cd799439103",
        role=UserRole.ADMIN,
        email="admin@example.com",
        password_hash="hash",
        full_name="Admin Board",
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=utc_now(),
        updated_at=utc_now(),
    )

@pytest.fixture
def sample_payment():
    now = utc_now()
    return PaymentInDB(
        id="507f1f77bcf86cd799439201",
        appointment_id="507f1f77bcf86cd799439301",
        patient_id="507f1f77bcf86cd799439101",
        doctor_id="507f1f77bcf86cd799439102",
        amount=1000.0,
        platform_fee=150.0,
        doctor_amount=850.0,
        currency="INR",
        payment_method=PaymentMethod.RAZORPAY,
        payment_status=PaymentStatus.SUCCESS,
        razorpay_order_id="order_123",
        razorpay_payment_id="pay_123",
        verified_at=now,
        created_at=now - timedelta(days=2),
        updated_at=now,
    )

@pytest.fixture
def sample_appointment():
    return AppointmentInDB(
        id="507f1f77bcf86cd799439301",
        patient_id="507f1f77bcf86cd799439101",
        doctor_id="doctor_profile_id_123",
        slot_date="2026-06-25",
        slot_time="10:00",
        duration_minutes=30,
        consultation_fee=1000.0,
        status=AppointmentStatus.APPROVED,
        payment_status=AppPaymentStatus.PAID,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


# ===========================================================================
# Service Unit Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_list_patient_payment_history_service(sample_payment, sample_appointment, patient_user, doctor_user):
    # Mock repositories
    pay_repo = MagicMock()
    appt_repo = MagicMock()
    user_repo = MagicMock()
    
    pay_repo.collection = MagicMock()
    pay_repo.collection.count_documents = AsyncMock(return_value=1)
    
    appt_repo.collection = MagicMock()
    user_repo.collection = MagicMock()

    
    # Mock payments cursor conversion
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    
    # Mongo doc representation of payment
    payment_mongo = sample_payment.model_dump()
    payment_mongo["_id"] = ObjectId(sample_payment.id)
    mock_cursor.to_list = AsyncMock(return_value=[payment_mongo])
    pay_repo.collection.find.return_value = mock_cursor
    
    # Mock appointment and user get returns
    appt_repo.get = AsyncMock(return_value=sample_appointment)
    user_repo.get = AsyncMock(return_value=doctor_user)
    
    # Profile find return
    pay_repo.db = MagicMock()
    doctor_profiles_col = MagicMock()
    doctor_profiles_col.find_one = AsyncMock(return_value={"user_id": doctor_user.id, "specialization": "Cardiology"})
    pay_repo.db.__getitem__ = MagicMock(return_value=doctor_profiles_col)


    service = PaymentService(
        payment_repository=pay_repo,
        appointment_repository=appt_repo,
        user_repository=user_repo,
    )
    
    results, total = await service.list_patient_payment_history(
        patient_id=patient_user.id,
        limit=10,
        skip=0
    )
    
    assert total == 1
    assert len(results) == 1
    assert results[0].payment_id == sample_payment.id
    assert results[0].amount == 1000.0
    assert results[0].doctor["full_name"] == "Dr. Smith"
    assert results[0].doctor["specialization"] == "Cardiology"
    assert results[0].receipt_information["doctor_share"] == 850.0
    assert results[0].receipt_information["platform_fee"] == 150.0


# ===========================================================================
# API Integration & Authentication Tests
# ===========================================================================

def test_patient_history_api_success(client, patient_user, sample_payment):
    # Setup mocks & dependencies override
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    payment_service_mock = AsyncMock()
    app.dependency_overrides[get_payment_service] = lambda: payment_service_mock
    
    from app.schemas.payment import PatientPaymentHistoryItemSchema
    
    mock_history_item = PatientPaymentHistoryItemSchema(
        payment_id=sample_payment.id,
        appointment={"id": "appt_123", "slot_date": "2026-06-25", "slot_time": "10:00", "status": "approved", "reason": "General check"},
        doctor={"id": "doc_123", "full_name": "Dr. Smith", "specialization": "Cardiology", "email": "doctor@example.com"},
        amount=1000.0,
        status="success",
        created_date=sample_payment.created_at,
        paid_date=sample_payment.verified_at,
        receipt_information={"doctor_share": 850.0, "platform_fee": 150.0}
    )
    payment_service_mock.list_patient_payment_history.return_value = ([mock_history_item], 1)
    
    res = client.get("/api/v1/payments/history?limit=10&skip=0")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["data"]["payments"]) == 1
    assert data["data"]["payments"][0]["payment_id"] == sample_payment.id
    assert data["data"]["payments"][0]["doctor"]["full_name"] == "Dr. Smith"


def test_admin_payments_endpoint_unauthorized(client, patient_user):
    # Patient trying to call admin payments
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    res = client.get("/api/v1/admin/payments")
    assert res.status_code == 403


def test_admin_payments_endpoint_success(client, admin_user, sample_payment):
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    payment_service_mock = AsyncMock()
    app.dependency_overrides[get_payment_service] = lambda: payment_service_mock
    
    from app.schemas.payment import AdminPaymentListItemSchema
    
    mock_item = AdminPaymentListItemSchema(
        payment_id=sample_payment.id,
        appointment_id=sample_payment.appointment_id,
        patient={"id": "pat_123", "full_name": "John Patient", "email": "patient@example.com"},
        doctor={"id": "doc_123", "full_name": "Dr. Smith", "email": "doctor@example.com", "specialization": "Cardiology"},
        amount=1000.0,
        doctor_share=850.0,
        platform_share=150.0,
        payment_status="success",
        created_at=sample_payment.created_at,
        verified_at=sample_payment.verified_at
    )
    payment_service_mock.list_payments_for_admin.return_value = ([mock_item], 1)
    
    res = client.get("/api/v1/admin/payments?search=John")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["data"]["payments"]) == 1
    assert data["data"]["payments"][0]["patient"]["full_name"] == "John Patient"


def test_admin_revenue_summary_success(client, admin_user):
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    payment_service_mock = AsyncMock()
    app.dependency_overrides[get_payment_service] = lambda: payment_service_mock
    
    from app.schemas.payment import AdminRevenueSummaryResponse, MonthlyRevenueItem, DailyRevenueItem
    
    mock_summary = AdminRevenueSummaryResponse(
        total_revenue=50000.0,
        doctor_payouts=42500.0,
        platform_earnings=7500.0,
        successful_payments=50,
        failed_payments=5,
        pending_payments=10,
        average_consultation_fee=1000.0,
        total_transactions=65,
        monthly_revenue=[MonthlyRevenueItem(month="2026-06", amount=50000.0, doctor_share=42500.0, platform_share=7500.0)],
        daily_revenue=[DailyRevenueItem(date="2026-06-25", amount=5000.0, doctor_share=42500.0, platform_share=7500.0)]
    )
    payment_service_mock.get_admin_payments_summary.return_value = mock_summary
    
    res = client.get("/api/v1/admin/payments/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["total_revenue"] == 50000.0
    assert data["data"]["successful_payments"] == 50
    assert len(data["data"]["monthly_revenue"]) == 1


def test_admin_payment_detail_and_audit_success(client, admin_user, sample_payment):
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    payment_service_mock = AsyncMock()
    app.dependency_overrides[get_payment_service] = lambda: payment_service_mock
    
    detail_data = {
        "payment_id": sample_payment.id,
        "amount": 1000.0,
        "doctor_share": 850.0,
        "platform_share": 150.0,
        "payment_status": "success",
        "patient": {"id": "pat_123", "full_name": "John Patient"},
        "doctor": {"id": "doc_123", "full_name": "Dr. Smith"}
    }
    payment_service_mock.get_payment_detail_for_admin.return_value = detail_data
    
    res = client.get(f"/api/v1/admin/payments/{sample_payment.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["payment_id"] == sample_payment.id
    
    payment_service_mock.get_payment_detail_for_admin.assert_called_once_with(
        payment_id=sample_payment.id,
        admin_user_id=admin_user.id
    )
