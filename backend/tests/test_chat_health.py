import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.chat.health_monitor import HealthMonitor


@pytest.mark.asyncio
async def test_health_monitor_healthy():
    mock_db = AsyncMock()
    mock_db.command.return_value = {"ok": 1.0}

    mock_qdrant = AsyncMock()
    mock_qdrant.client.get_collections.return_value = MagicMock()

    monitor = HealthMonitor(database=mock_db, vector_service=mock_qdrant)
    health = await monitor.check_health()

    assert health["status"] == "HEALTHY"
    assert health["details"]["mongodb"] == "HEALTHY"
    assert health["details"]["qdrant"] == "HEALTHY"


@pytest.mark.asyncio
async def test_health_monitor_unhealthy_mongodb():
    mock_db = AsyncMock()
    mock_db.command.side_effect = Exception("DB Connection Down")

    mock_qdrant = AsyncMock()
    mock_qdrant.client.get_collections.return_value = MagicMock()

    monitor = HealthMonitor(database=mock_db, vector_service=mock_qdrant)
    health = await monitor.check_health()

    assert health["status"] == "UNHEALTHY"
    assert health["details"]["mongodb"] == "UNHEALTHY"
    assert health["details"]["qdrant"] == "HEALTHY"


@pytest.mark.asyncio
async def test_health_monitor_degraded_qdrant():
    mock_db = AsyncMock()
    mock_db.command.return_value = {"ok": 1.0}

    mock_qdrant = AsyncMock()
    mock_qdrant.client.get_collections.side_effect = Exception("Qdrant Down")

    monitor = HealthMonitor(database=mock_db, vector_service=mock_qdrant)
    health = await monitor.check_health()

    assert health["status"] == "DEGRADED"
    assert health["details"]["mongodb"] == "HEALTHY"
    assert health["details"]["qdrant"] == "UNHEALTHY"
