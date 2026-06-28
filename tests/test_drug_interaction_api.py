import os
import sys
import pytest
import httpx
from httpx import ASGITransport
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.api.v1.ai import router
from app.core.dependencies import get_current_user, get_drug_interaction_engine, get_auth_service
from app.models.user import UserInDB, UserRole
from app.schemas.ai import DrugCheckResponse, DrugTelemetryResponse

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
async def test_drug_check_endpoint(mock_admin, mock_auth_service):
    mock_engine = MagicMock()
    mock_engine.check_interactions = AsyncMock(return_value={
        "medications": ["Warfarin", "Aspirin"],
        "normalized_medications": ["warfarin", "aspirin"],
        "detected_interactions": [
            {
                "drug_a": "Warfarin",
                "drug_a_normalized": "warfarin",
                "drug_b": "Aspirin",
                "drug_b_normalized": "aspirin",
                "severity": "HIGH",
                "description": "Increased bleeding risk."
            }
        ],
        "severity": "HIGH",
        "recommendations": ["Avoid combination.", "Immediate physician review recommended."],
        "statistics": {
            "total_lookups": 2,
            "cache_hits": 0,
            "cache_misses": 2,
            "cache_hit_ratio": 0.0,
            "avg_latency_ms": 10.0,
            "unknown_drug_count": 0,
            "normalization_count": 2,
            "interaction_checks": 1,
            "pairs_evaluated": 1,
            "interaction_avg_latency_ms": 15.0,
            "severity_distribution": {"HIGH": 1, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0, "NONE": 0}
        },
        "latency_ms": 15.2
    })
    
    app.dependency_overrides[get_current_user] = lambda: mock_admin
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_drug_interaction_engine] = lambda: mock_engine
    
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/drug/check", json={"medications": ["Warfarin", "Aspirin"]})
        assert res.status_code == 200
        data = res.json()
        assert data["severity"] == "HIGH"
        assert len(data["detected_interactions"]) == 1
        assert data["detected_interactions"][0]["severity"] == "HIGH"
        
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_drug_interactions_statistics_endpoint(mock_admin, mock_auth_service):
    app.dependency_overrides[get_current_user] = lambda: mock_admin
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/drug/interactions/statistics")
        assert res.status_code == 200
        data = res.json()
        assert "interaction_checks" in data
        assert "pairs_evaluated" in data
        assert "severity_distribution" in data
        
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_drug_interactions_endpoints_unauthorized(mock_patient, mock_auth_service):
    app.dependency_overrides[get_current_user] = lambda: mock_patient
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_drug_interaction_engine] = MagicMock()
    
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Check should fail with 403 Forbidden
        res = await client.post("/drug/check", json={"medications": ["Warfarin"]})
        assert res.status_code == 403
        
        # Stats should fail with 403 Forbidden
        res2 = await client.get("/drug/interactions/statistics")
        assert res2.status_code == 403
        
    app.dependency_overrides.clear()
