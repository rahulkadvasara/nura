import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_doctor_profile_service,
    get_doctor_earnings_service,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.models.doctor import DoctorProfileInDB, DoctorProfileStatus
from app.schemas.payment import (
    DoctorEarningsResponse,
    DoctorWalletDetailsResponse,
    DoctorWalletResponse,
    MonthlyEarningsItem,
    RevenueTrendItem,
    DoctorTransactionItem,
    DoctorTransactionsResponse,
    PaymentResponse,
)
from app.models.payment import PaymentStatus, PaymentMethod

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
def unverified_doctor_user():
    now = utc_now()
    return UserInDB(
        id="507f1f77bcf86cd799439004",
        email="unverified@example.com",
        password_hash="hashed_pw",
        full_name="Unverified Doctor",
        role=UserRole.DOCTOR,
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
def unverified_doctor_profile():
    now = utc_now()
    return DoctorProfileInDB(
        id="507f1f77bcf86cd799439014",
        user_id="507f1f77bcf86cd799439004",
        specialization="Cardiology",
        qualifications=["MBBS"],
        experience_years=3,
        consultation_fee=300.0,
        bio="Unverified",
        languages=["English"],
        profile_status=DoctorProfileStatus.PENDING,
        created_at=now,
        updated_at=now
    )

def test_unauthorized_endpoints(client, unverified_doctor_user, unverified_doctor_profile):
    app.dependency_overrides[get_current_user] = lambda: unverified_doctor_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = unverified_doctor_profile
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    for path in ["/api/v1/doctor/earnings", "/api/v1/doctor/wallet", "/api/v1/doctor/transactions"]:
        response = client.get(path)
        assert response.status_code == 403
        assert "verified" in response.json()["message"].lower()

def test_get_wallet_success(client, doctor_user, doctor_profile):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = doctor_profile
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    now = utc_now()
    wallet_details = DoctorWalletResponse(
        id="wallet_123",
        doctor_id=doctor_user.id,
        total_earned=1000.0,
        total_withdrawn=200.0,
        available_balance=800.0,
        pending_balance=200.0,
        last_payout_at=None,
        created_at=now,
        updated_at=now
    )
    wallet_resp = DoctorWalletDetailsResponse(
        wallet_details=wallet_details,
        pending_amount=200.0,
        available_amount=800.0,
        lifetime_earnings=1000.0,
        total_withdrawn=200.0
    )

    mock_earnings_service = AsyncMock()
    mock_earnings_service.get_wallet_details.return_value = wallet_resp
    app.dependency_overrides[get_doctor_earnings_service] = lambda: mock_earnings_service

    response = client.get("/api/v1/doctor/wallet")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["available_amount"] == 800.0
    assert data["data"]["pending_amount"] == 200.0
    assert data["data"]["wallet_details"]["id"] == "wallet_123"

def test_get_wallet_empty(client, doctor_user, doctor_profile):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = doctor_profile
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    now = utc_now()
    wallet_details = DoctorWalletResponse(
        id="default_wallet_id",
        doctor_id=doctor_user.id,
        total_earned=0.0,
        total_withdrawn=0.0,
        available_balance=0.0,
        pending_balance=0.0,
        last_payout_at=None,
        created_at=now,
        updated_at=now
    )
    wallet_resp = DoctorWalletDetailsResponse(
        wallet_details=wallet_details,
        pending_amount=0.0,
        available_amount=0.0,
        lifetime_earnings=0.0,
        total_withdrawn=0.0
    )

    mock_earnings_service = AsyncMock()
    mock_earnings_service.get_wallet_details.return_value = wallet_resp
    app.dependency_overrides[get_doctor_earnings_service] = lambda: mock_earnings_service

    response = client.get("/api/v1/doctor/wallet")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["available_amount"] == 0.0
    assert data["data"]["wallet_details"]["id"] == "default_wallet_id"

def test_get_earnings_success(client, doctor_user, doctor_profile):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = doctor_profile
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    earnings_resp = DoctorEarningsResponse(
        available_balance=850.0,
        pending_balance=150.0,
        lifetime_earnings=1000.0,
        platform_revenue_share=150.0,
        doctor_revenue_share=850.0,
        total_consultations=2,
        total_completed_consultations=2,
        average_consultation_fee=500.0,
        monthly_earnings_summary=[
            MonthlyEarningsItem(month="2026-06", amount=850.0)
        ],
        recent_transactions=[
            PaymentResponse(
                id="pay_1",
                appointment_id="appt_1",
                patient_id="patient_1",
                doctor_id=doctor_user.id,
                amount=500.0,
                platform_fee=75.0,
                doctor_amount=425.0,
                currency="INR",
                payment_method=PaymentMethod.UPI,
                payment_status=PaymentStatus.COMPLETED,
                escrow_held=False,
                created_at=utc_now(),
                updated_at=utc_now()
            )
        ],
        revenue_trend=[
            RevenueTrendItem(date="2026-06-25", amount=850.0)
        ]
    )

    mock_earnings_service = AsyncMock()
    mock_earnings_service.get_earnings_summary.return_value = earnings_resp
    app.dependency_overrides[get_doctor_earnings_service] = lambda: mock_earnings_service

    response = client.get("/api/v1/doctor/earnings?start_date=2026-06-01&end_date=2026-06-30")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["available_balance"] == 850.0
    assert data["data"]["platform_revenue_share"] == 150.0
    assert data["data"]["doctor_revenue_share"] == 850.0
    assert data["data"]["monthly_earnings_summary"][0]["month"] == "2026-06"
    assert data["data"]["recent_transactions"][0]["id"] == "pay_1"

    mock_earnings_service.get_earnings_summary.assert_called_once_with(
        doctor_user_id=doctor_user.id,
        doctor_profile_id=doctor_profile.id,
        start_date="2026-06-01",
        end_date="2026-06-30",
        limit=10,
        skip=0,
        sort_by=None
    )

def test_get_transactions_filters(client, doctor_user, doctor_profile):
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    
    mock_profile_service = AsyncMock()
    mock_profile_service.get_profile_by_user_id.return_value = doctor_profile
    app.dependency_overrides[get_doctor_profile_service] = lambda: mock_profile_service

    tx_resp = DoctorTransactionsResponse(
        transactions=[
            DoctorTransactionItem(
                id="pay_1",
                appointment_id="appt_1",
                patient_id="patient_1",
                patient_name="Patient One",
                consultation_fee=500.0,
                doctor_share=425.0,
                platform_share=75.0,
                status="completed",
                created_at=utc_now()
            )
        ],
        total=1
    )

    mock_earnings_service = AsyncMock()
    mock_earnings_service.get_transactions.return_value = tx_resp
    app.dependency_overrides[get_doctor_earnings_service] = lambda: mock_earnings_service

    response = client.get("/api/v1/doctor/transactions?start_date=2026-06-01&end_date=2026-06-30&status_filter=completed&limit=10&skip=0")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 1
    assert data["data"]["transactions"][0]["patient_name"] == "Patient One"

    mock_earnings_service.get_transactions.assert_called_once_with(
        doctor_user_id=doctor_user.id,
        limit=10,
        skip=0,
        start_date="2026-06-01",
        end_date="2026-06-30",
        status="completed"
    )
