"""
Nura - Google Meet Integration Tests
Unit and integration tests for Google Meet OAuth authorization flow and meeting creation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from app.services.google_meet_service import (
    GoogleMeetService,
    GOOGLE_MEET_SCOPE,
)
from app.models.appointment import AppointmentInDB, AppointmentStatus, PaymentStatus
from app.schemas.appointment import AppointmentUpdateSchema


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MockSystemIntegrationRepository:
    def __init__(self):
        self.store = {}

    async def get_integration(self, name: str):
        return self.store.get(name)

    async def save_integration(self, name: str, data: dict):
        self.store[name] = dict(data)
        return self.store[name]


class MockAppointmentRepository:
    def __init__(self):
        self.appts = {}

    async def get(self, appt_id: str):
        return self.appts.get(appt_id)

    async def update(self, appt_id: str, update_obj):
        appt = self.appts.get(appt_id)
        if not appt:
            return None

        update_dict = update_obj.model_dump(exclude_unset=True) if hasattr(update_obj, "model_dump") else dict(update_obj)
        doc = appt.model_dump()
        doc.update(update_dict)
        doc["updated_at"] = utc_now()
        updated_appt = AppointmentInDB(**doc)
        self.appts[appt_id] = updated_appt
        return updated_appt


@pytest.fixture
def repo():
    return MockSystemIntegrationRepository()


@pytest.fixture
def appt_repo():
    return MockAppointmentRepository()


@pytest.fixture
def meet_service(repo, appt_repo):
    return GoogleMeetService(
        system_integration_repository=repo,
        appointment_repository=appt_repo,
    )


def test_authorize_url_generation(meet_service):
    """Test authorize() constructs correct URL with minimum required scope"""
    auth_url = meet_service.authorize(state="test_state")
    assert "https://accounts.google.com/o/oauth2/v2/auth" in auth_url
    assert f"scope={GOOGLE_MEET_SCOPE.replace('/', '%2F').replace(':', '%3A')}" in auth_url or GOOGLE_MEET_SCOPE in auth_url
    assert "response_type=code" in auth_url
    assert "access_type=offline" in auth_url
    assert "prompt=consent" in auth_url
    assert "state=test_state" in auth_url


@pytest.mark.asyncio
async def test_handle_callback_success(meet_service, repo):
    """Test handle_callback() exchanges code for tokens and persists refresh token"""
    fake_token_response = {
        "access_token": "mock_access_123",
        "refresh_token": "mock_refresh_456",
        "expires_in": 3600,
        "scope": GOOGLE_MEET_SCOPE,
        "token_type": "Bearer",
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fake_token_response

    with patch("app.core.config.settings.GOOGLE_MEET_CLIENT_ID", "test_client_id"), \
         patch("app.core.config.settings.GOOGLE_MEET_CLIENT_SECRET", "test_client_secret"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        result = await meet_service.handle_callback("mock_auth_code")
        assert result["authorized"] is True
        assert result["has_refresh_token"] is True

        stored = await repo.get_integration("google_meet")
        assert stored is not None
        assert stored["access_token"] == "mock_access_123"
        assert stored["refresh_token"] == "mock_refresh_456"


@pytest.mark.asyncio
async def test_get_access_token_cached_and_refreshed(meet_service, repo):
    """Test get_access_token() returns valid token or refreshes when expired"""
    now = utc_now()
    # Set valid token
    await repo.save_integration("google_meet", {
        "access_token": "valid_token",
        "refresh_token": "valid_refresh",
        "expires_at": (now + timedelta(minutes=30)).isoformat(),
    })

    token = await meet_service.get_access_token()
    assert token == "valid_token"

    # Set expired token
    await repo.save_integration("google_meet", {
        "access_token": "expired_token",
        "refresh_token": "valid_refresh",
        "expires_at": (now - timedelta(minutes=10)).isoformat(),
    })

    fake_refresh_response = {
        "access_token": "new_access_token_999",
        "expires_in": 3600,
    }
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fake_refresh_response

    with patch("app.core.config.settings.GOOGLE_MEET_CLIENT_ID", "test_client_id"), \
         patch("app.core.config.settings.GOOGLE_MEET_CLIENT_SECRET", "test_client_secret"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        refreshed_token = await meet_service.get_access_token()
        assert refreshed_token == "new_access_token_999"


@pytest.mark.asyncio
async def test_create_meeting_success(meet_service, repo):
    """Test create_meeting() calls Google Meet API and returns meeting Uri"""
    await repo.save_integration("google_meet", {
        "access_token": "valid_access_token",
        "refresh_token": "valid_refresh_token",
        "expires_at": (utc_now() + timedelta(hours=1)).isoformat(),
    })

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "name": "spaces/xyz-123-abc",
        "meetingUri": "https://meet.google.com/xyz-123-abc",
        "meetingCode": "xyz-123-abc",
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        meet_url = await meet_service.create_meeting("appt_001")
        assert meet_url == "https://meet.google.com/xyz-123-abc"


@pytest.mark.asyncio
async def test_create_meeting_duplicate_prevention(meet_service, appt_repo):
    """Test create_meeting() returns existing meeting link without calling Google Meet API twice"""
    existing_appt = AppointmentInDB(
        id="appt_002",
        patient_id="pat_1",
        doctor_id="doc_1",
        slot_date="2026-09-10",
        slot_time="10:00",
        duration_minutes=30,
        consultation_fee=500.0,
        status=AppointmentStatus.APPROVED,
        payment_status=PaymentStatus.PAID,
        meeting_link="https://meet.google.com/existing-link-123",
        meeting_provider="google_meet",
        meeting_created_at=utc_now(),
    )
    appt_repo.appts["appt_002"] = existing_appt

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        meet_url = await meet_service.create_meeting("appt_002")
        assert meet_url == "https://meet.google.com/existing-link-123"
        mock_post.assert_not_called()


@pytest.mark.asyncio
async def test_create_meeting_unconfigured_graceful_fallback(meet_service):
    """Test create_meeting() handles missing credentials gracefully returning None"""
    meet_url = await meet_service.create_meeting("appt_003")
    assert meet_url is None
