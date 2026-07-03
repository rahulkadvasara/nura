"""
Nura - Chat Memory API Tests
Tests conversation memory routes access constraints, evaluate/sync tools, and scroll lookups
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.models.user import UserInDB, UserRole
from app.core.dependencies import (
    get_current_user,
    get_conversation_evaluator,
    get_memory_update_service,
    get_vector_service,
    get_chat_session_service,
    get_chat_message_repository,
)

# Client reference
client = TestClient(app)

# Mock users
admin_user = UserInDB(
    id="admin123",
    email="admin@nura.com",
    role=UserRole.ADMIN,
    full_name="Admin User",
    password_hash="...",
    is_active=True
)

patient_user = UserInDB(
    id="pat123",
    email="patient@nura.com",
    role=UserRole.PATIENT,
    full_name="Patient User",
    password_hash="...",
    is_active=True
)


@pytest.fixture(autouse=True)
def mock_mongodb():
    from app.db.mongodb import mongodb_connection
    original_db = mongodb_connection.database
    mock_db = MagicMock()
    mongodb_connection.database = mock_db
    yield mock_db
    mongodb_connection.database = original_db


@pytest.fixture
def override_admin():
    app.dependency_overrides[get_current_user] = lambda: admin_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def override_patient():
    app.dependency_overrides[get_current_user] = lambda: patient_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


def test_evaluate_memory_admin_only(override_patient):
    # Patient tries to access admin-only endpoint
    response = client.post("/api/v1/chat/memory/evaluate", json={"session_id": "sess123"})
    assert response.status_code == 403


def test_evaluate_memory_success(override_admin):
    mock_evaluator = AsyncMock()
    mock_evaluator.evaluate_session = AsyncMock(return_value={
        "memory_score": 0.8,
        "semantic_score": 0.9,
        "clinical_score": 0.7,
        "should_store_chat_memory": True,
        "should_update_patient_memory": True
    })
    app.dependency_overrides[get_conversation_evaluator] = lambda: mock_evaluator

    try:
        response = client.post("/api/v1/chat/memory/evaluate", json={"session_id": "sess123"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["memory_score"] == 0.8
    finally:
        app.dependency_overrides.pop(get_conversation_evaluator, None)


def test_force_sync_memory_success(override_admin):
    mock_update_service = AsyncMock()
    mock_update_service.evaluate_and_sync_session = AsyncMock(return_value={"status": "stored"})
    app.dependency_overrides[get_memory_update_service] = lambda: mock_update_service

    mock_session_service = AsyncMock()
    mock_session = MagicMock()
    mock_session.patient_id = "pat123"
    mock_session_service.get_session_by_id = AsyncMock(return_value=mock_session)
    app.dependency_overrides[get_chat_session_service] = lambda: mock_session_service

    mock_msg_repo = AsyncMock()
    mock_msg_repo.get_by_session_id = AsyncMock(return_value=[])
    app.dependency_overrides[get_chat_message_repository] = lambda: mock_msg_repo

    try:
        response = client.post("/api/v1/chat/memory/update", json={"session_id": "sess123"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "complete" in data["data"]["status"]
    finally:
        app.dependency_overrides.pop(get_memory_update_service, None)
        app.dependency_overrides.pop(get_chat_session_service, None)
        app.dependency_overrides.pop(get_chat_message_repository, None)


def test_get_statistics_success(override_admin):
    from app.services.chat_memory.telemetry import memory_telemetry
    memory_telemetry.reset()
    memory_telemetry.record_evaluation(0.7, 0.8, 0.6, True, True)

    response = client.get("/api/v1/chat/memory/statistics")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["evaluations_count"] == 1


def test_get_session_memory_success(override_patient):
    mock_session_service = AsyncMock()
    mock_session = MagicMock()
    mock_session.patient_id = "pat123"
    mock_session_service.get_session_by_id = AsyncMock(return_value=mock_session)
    app.dependency_overrides[get_chat_session_service] = lambda: mock_session_service

    mock_vector = AsyncMock()
    mock_vector.create_collection = AsyncMock()
    mock_vector.scroll = AsyncMock(return_value=([
        {
            "id": "pt123",
            "payload": {
                "summary": "High blood pressure",
                "keywords": ["hypertension"],
                "entities": ["hypertension"],
                "timestamp": "2026-07-03"
            }
        }
    ], None))
    app.dependency_overrides[get_vector_service] = lambda: mock_vector

    try:
        response = client.get("/api/v1/chat/session/sess123/memory")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["summary"] == "High blood pressure"
    finally:
        app.dependency_overrides.pop(get_chat_session_service, None)
        app.dependency_overrides.pop(get_vector_service, None)
