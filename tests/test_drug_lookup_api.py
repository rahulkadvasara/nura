import os
import sys
import pytest
import httpx
from httpx import ASGITransport
from fastapi import FastAPI, Depends
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.api.v1.ai import router
from app.core.dependencies import get_current_user, get_drug_normalizer, get_drug_lookup_service, require_role, get_auth_service
from app.models.user import UserInDB, UserRole
from app.schemas.ai import DrugLookupResponse, DrugNormalizeResponse, DrugTelemetryResponse

# Construct test FastAPI app instance
app = FastAPI()
app.include_router(router)

@pytest.fixture
def mock_admin():
    return UserInDB(
        id="admin_123",
        email="admin@nura.com",
        password_hash="hash",
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
        email_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

@pytest.fixture
def mock_patient():
    return UserInDB(
        id="patient_123",
        email="patient@nura.com",
        password_hash="hash",
        full_name="Patient User",
        role=UserRole.PATIENT,
        is_active=True,
        email_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

@pytest.fixture
def mock_auth_service():
    service = MagicMock()
    def require_role_impl(user, required_role):
        has_role = False
        if user.role == UserRole.ADMIN:
            has_role = True
        elif user.role == UserRole.DOCTOR:
            has_role = required_role in (UserRole.DOCTOR, UserRole.PATIENT)
        else:
            has_role = (user.role == required_role)
            
        if not has_role:
            raise PermissionError("Forbidden")
    service.require_role = require_role_impl
    return service

@pytest.mark.asyncio
async def test_drug_normalize_endpoint(mock_admin, mock_auth_service):
    mock_normalizer = MagicMock()
    mock_normalizer.normalize.return_value = "paracetamol"
    
    app.dependency_overrides[get_current_user] = lambda: mock_admin
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_drug_normalizer] = lambda: mock_normalizer
    
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/drug/normalize", json={"drug_name": "Paracetamol 650mg"})
        assert res.status_code == 200
        assert res.json()["normalized_name"] == "paracetamol"
        mock_normalizer.normalize.assert_called_once_with("Paracetamol 650mg")
        
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_drug_lookup_endpoint(mock_admin, mock_auth_service):
    mock_lookup_service = MagicMock()
    mock_lookup_service.lookup = AsyncMock(return_value={
        "exists": True,
        "matched_drug": {
            "drug_name": "Paracetamol",
            "normalized_name": "paracetamol",
            "aliases": ["acetaminophen"],
            "source_dataset": "ddinter"
        },
        "normalized_name": "paracetamol",
        "lookup_source": "database",
        "confidence": 1.0,
        "latency_ms": 12.5
    })
    
    app.dependency_overrides[get_current_user] = lambda: mock_admin
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_drug_lookup_service] = lambda: mock_lookup_service
    
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/drug/lookup/Paracetamol")
        assert res.status_code == 200
        data = res.json()
        assert data["exists"] is True
        assert data["normalized_name"] == "paracetamol"
        assert data["matched_drug"]["drug_name"] == "Paracetamol"
        
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_drug_statistics_endpoint(mock_admin, mock_auth_service):
    app.dependency_overrides[get_current_user] = lambda: mock_admin
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/drug/statistics")
        assert res.status_code == 200
        data = res.json()
        assert "total_lookups" in data
        assert "cache_hits" in data
        assert "cache_misses" in data
        
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_drug_endpoints_unauthorized(mock_patient, mock_auth_service):
    app.dependency_overrides[get_current_user] = lambda: mock_patient
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_drug_lookup_service] = MagicMock()
    app.dependency_overrides[get_drug_normalizer] = MagicMock()
    
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Lookup should fail with 403 Forbidden
        res = await client.get("/drug/lookup/Paracetamol")
        assert res.status_code == 403
        
        # Normalize should fail with 403 Forbidden
        res2 = await client.post("/drug/normalize", json={"drug_name": "Paracetamol"})
        assert res2.status_code == 403
        
        # Statistics should fail with 403 Forbidden
        res3 = await client.get("/drug/statistics")
        assert res3.status_code == 403
        
    app.dependency_overrides.clear()
