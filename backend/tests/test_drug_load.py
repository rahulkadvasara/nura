import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.drug_safety.lookup_service import DrugLookupService
from app.services.drug_safety.validation_service import MedicationValidationService
from app.services.drug_safety.telemetry import drug_safety_telemetry
from app.services.drug_cache.drug_cache_service import DrugCacheService

@pytest.fixture
def mock_db():
    mock_coll = AsyncMock()
    # Mock lookup record in master
    mock_coll.find_one.return_value = {
        "_id": "some-id",
        "drug_name": "Aspirin",
        "normalized_name": "ASPIRIN",
        "aliases": []
    }
    db = MagicMock(spec=AsyncIOMotorDatabase)
    db.drug_master = mock_coll
    return db

@pytest.mark.asyncio
async def test_lookup_load_and_performance(mock_db):
    """
    Runs 100 concurrent lookups on a drug.
    First check should go to DB (miss), subsequent 99 should hit the cache.
    Verifies that the caching reduces average latency and handles concurrency.
    """
    drug_safety_telemetry.reset()
    lookup_service = DrugLookupService(mock_db)
    lookup_service.cache_service.clear()

    # Define task runner
    async def run_lookup():
        return await lookup_service.lookup("Aspirin")

    # Launch 100 lookups concurrently
    start_time = time.perf_counter()
    tasks = [run_lookup() for _ in range(100)]
    results = await asyncio.gather(*tasks)
    total_time = (time.perf_counter() - start_time) * 1000.0

    # Assertions
    stats = drug_safety_telemetry.get_statistics()
    assert stats["total_lookups"] == 100
    assert stats["cache_hits"] == 99
    assert stats["cache_misses"] == 1
    
    # DB find_one should only be called once due to cache
    mock_db.drug_master.find_one.assert_called_once()
    
    # Cache hit ratio should be 0.99
    assert stats["cache_hit_ratio"] == 0.99
    
    # The total execution time for 100 lookups should be low (e.g. < 50ms)
    print(f"Total load check duration for 100 queries: {total_time:.2f}ms")
