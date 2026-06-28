import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.services.drug_safety.interaction_engine import DrugInteractionEngine
from app.services.drug_safety.lookup_service import DrugLookupService
from app.services.drug_safety.telemetry import drug_safety_telemetry


@pytest.fixture
def mock_lookup_service():
    service = MagicMock()
    async def mock_lookup(name):
        n = name.lower().strip()
        if "warfarin" in n:
            return {
                "exists": True,
                "matched_drug": {"drug_name": "Warfarin", "normalized_name": "warfarin", "aliases": [], "source_dataset": "ddinter"}
            }
        if "aspirin" in n:
            return {
                "exists": True,
                "matched_drug": {"drug_name": "Aspirin", "normalized_name": "aspirin", "aliases": [], "source_dataset": "ddinter"}
            }
        if "metformin" in n:
            return {
                "exists": True,
                "matched_drug": {"drug_name": "Metformin", "normalized_name": "metformin", "aliases": [], "source_dataset": "ddinter"}
            }
        return {"exists": False, "matched_drug": None}
    service.lookup = AsyncMock(side_effect=mock_lookup)
    return service


@pytest.fixture
def mock_db():
    db = MagicMock()
    interactions_col = MagicMock()
    
    async def mock_find_to_list(length=1000):
        # We check the query to see if it matches warfarin and aspirin
        # Let's say there is a HIGH interaction between warfarin and aspirin
        query = interactions_col.find.call_args[0][0]
        or_conds = query.get("$or", [])
        
        matches = []
        # Check if conditions ask for warfarin and aspirin
        has_warfarin_aspirin = False
        for cond in or_conds:
            da = cond.get("drug_a_normalized")
            db_name = cond.get("drug_b_normalized")
            if (da == "warfarin" and db_name == "aspirin") or (da == "aspirin" and db_name == "warfarin"):
                has_warfarin_aspirin = True
                
        if has_warfarin_aspirin:
            matches.append({
                "drug_a": "Warfarin",
                "drug_a_normalized": "warfarin",
                "drug_b": "Aspirin",
                "drug_b_normalized": "aspirin",
                "severity": "HIGH",
                "interaction_description": "Increased bleeding risk."
            })
            
        return matches
        
    find_mock = MagicMock()
    find_mock.to_list = AsyncMock(side_effect=mock_find_to_list)
    interactions_col.find = MagicMock(return_value=find_mock)
    
    db.drug_interactions = interactions_col
    return db


@pytest.mark.asyncio
async def test_interaction_engine_single_medication(mock_db, mock_lookup_service):
    engine = DrugInteractionEngine(mock_db, mock_lookup_service)
    res = await engine.check_interactions(["Warfarin"])
    
    assert res.severity == "NONE"
    assert len(res.detected_interactions) == 0
    assert "No known interactions detected." in res.recommendations


@pytest.mark.asyncio
async def test_interaction_engine_duplicate_medications(mock_db, mock_lookup_service):
    engine = DrugInteractionEngine(mock_db, mock_lookup_service)
    # Check that duplicate inputs don't evaluate a drug against itself
    res = await engine.check_interactions(["Warfarin", "warfarin"])
    
    assert res.severity == "NONE"
    assert len(res.detected_interactions) == 0


@pytest.mark.asyncio
async def test_interaction_engine_multiple_meds_with_interaction(mock_db, mock_lookup_service):
    drug_safety_telemetry.reset()
    engine = DrugInteractionEngine(mock_db, mock_lookup_service)
    
    res = await engine.check_interactions(["Warfarin", "Aspirin 325mg", "Metformin"])
    
    assert res.severity == "HIGH"
    assert len(res.detected_interactions) == 1
    assert res.detected_interactions[0].drug_a_normalized == "warfarin"
    assert res.detected_interactions[0].drug_b_normalized == "aspirin"
    assert "Avoid combination." in res.recommendations
    
    stats = drug_safety_telemetry.get_statistics()
    assert stats["interaction_checks"] == 1
    assert stats["pairs_evaluated"] == 3 # Warfarin-Aspirin, Warfarin-Metformin, Aspirin-Metformin


@pytest.mark.asyncio
async def test_interaction_engine_unknown_medication(mock_db, mock_lookup_service):
    engine = DrugInteractionEngine(mock_db, mock_lookup_service)
    res = await engine.check_interactions(["Warfarin", "FakeDrug123"])
    
    # FakeDrug123 should be skipped since it's not found in lookup_service
    assert res.severity == "NONE"
    assert len(res.detected_interactions) == 0
    assert res.normalized_medications == ["warfarin"]
