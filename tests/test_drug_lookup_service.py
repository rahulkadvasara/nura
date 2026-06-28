import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.services.drug_safety.lookup_service import DrugLookupService
from app.services.drug_safety.telemetry import drug_safety_telemetry

@pytest.fixture
def mock_db():
    # Setup mock collections
    master_col = MagicMock()
    
    # Mock documents for drug master
    async def mock_find_one(query):
        # Exact match query
        if "normalized_name" in query:
            name = query["normalized_name"]
            if name == "paracetamol":
                return {
                    "_id": "id1",
                    "drug_name": "Paracetamol",
                    "normalized_name": "paracetamol",
                    "aliases": ["acetaminophen"],
                    "source_dataset": "ddinter"
                }
            if name == "ibuprofen":
                return {
                    "_id": "id2",
                    "drug_name": "Ibuprofen",
                    "normalized_name": "ibuprofen",
                    "aliases": [],
                    "source_dataset": "ddinter"
                }
        # Alias query
        elif "aliases" in query:
            alias = query["aliases"]
            if alias == "acetaminophen":
                return {
                    "_id": "id1",
                    "drug_name": "Paracetamol",
                    "normalized_name": "paracetamol",
                    "aliases": ["acetaminophen"],
                    "source_dataset": "ddinter"
                }
        return None
        
    master_col.find_one = AsyncMock(side_effect=mock_find_one)
    
    db = MagicMock()
    db.drug_master = master_col
    return db

@pytest.mark.asyncio
async def test_drug_lookup_exact(mock_db):
    drug_safety_telemetry.reset()
    service = DrugLookupService(mock_db, ttl_seconds=10)
    
    # 1. Lookup exact
    res = await service.lookup("Paracetamol 650mg")
    assert res["exists"] is True
    assert res["matched_drug"]["normalized_name"] == "paracetamol"
    assert res["confidence"] == 1.0
    assert res["lookup_source"] == "database"
    
    # Verify telemetry
    stats = drug_safety_telemetry.get_statistics()
    assert stats["total_lookups"] == 1
    assert stats["cache_misses"] == 1
    assert stats["cache_hits"] == 0

@pytest.mark.asyncio
async def test_drug_lookup_alias(mock_db):
    drug_safety_telemetry.reset()
    service = DrugLookupService(mock_db, ttl_seconds=10)
    
    # 1. Lookup alias
    res = await service.lookup("acetaminophen")
    assert res["exists"] is True
    assert res["matched_drug"]["normalized_name"] == "paracetamol"
    assert res["confidence"] == 0.9
    
    # Verify database was queried by aliases
    mock_db.drug_master.find_one.assert_called()

@pytest.mark.asyncio
async def test_drug_lookup_cache_hits(mock_db):
    drug_safety_telemetry.reset()
    service = DrugLookupService(mock_db, ttl_seconds=10)
    
    # First lookup (database hit)
    res1 = await service.lookup("ibuprofen")
    assert res1["lookup_source"] == "database"
    
    # Second lookup (cache hit)
    res2 = await service.lookup("ibuprofen")
    assert res2["lookup_source"] == "cache"
    assert res2["exists"] is True
    assert res2["confidence"] == 1.0
    
    # Verify cache telemetry
    stats = drug_safety_telemetry.get_statistics()
    assert stats["total_lookups"] == 2
    assert stats["cache_hits"] == 1
    assert stats["cache_misses"] == 1
    
    cache_stats = await service.get_cache_statistics()
    assert cache_stats["hits"] == 1
    assert cache_stats["misses"] == 1
    assert cache_stats["cache_size"] == 1

@pytest.mark.asyncio
async def test_drug_lookup_not_found(mock_db):
    drug_safety_telemetry.reset()
    service = DrugLookupService(mock_db, ttl_seconds=10)
    
    res = await service.lookup("unknown drug")
    assert res["exists"] is False
    assert res["matched_drug"] is None
    assert res["confidence"] == 0.0
    
    # Verify telemetry
    stats = drug_safety_telemetry.get_statistics()
    assert stats["unknown_drug_count"] == 1

@pytest.mark.asyncio
async def test_drug_lookup_bulk(mock_db):
    service = DrugLookupService(mock_db, ttl_seconds=10)
    res = await service.bulk_lookup(["Paracetamol", "Ibuprofen Tablet", "unknown drug"])
    
    assert res["Paracetamol"]["exists"] is True
    assert res["Ibuprofen Tablet"]["exists"] is True
    assert res["unknown_drug"]["exists"] is False if "unknown_drug" in res else res["unknown drug"]["exists"] is False
