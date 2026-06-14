"""
Nura - Health Endpoint Tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "app" in data
    assert "environment" in data
    assert "mongodb" in data
    assert "qdrant" in data
    assert data["app"] == "Nura"


def test_health_response_structure():
    """Test health response structure"""
    response = client.get("/api/v1/health")
    data = response.json()
    
    expected_keys = {"status", "app", "environment", "mongodb", "qdrant"}
    assert set(data.keys()) == expected_keys