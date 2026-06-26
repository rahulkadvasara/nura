"""
Nura - Unit tests for MemorySyncService
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timezone

from app.models.patient_memory import PatientMemoryInDB, PatientMemoryCreate
from app.services.memory_sync_service import MemorySyncService
from app.schemas.embedding import EmbeddingResult, EmbeddingMetadata


@pytest.fixture
def mock_sync_dependencies():
    return {
        "patient_memory_repository": MagicMock(),
        "user_repository": MagicMock(),
        "patient_summary_builder": MagicMock(),
        "embedding_service": MagicMock(),
        "vector_service": MagicMock(),
        "index_version_service": MagicMock(),
        "audit_log_service": MagicMock()
    }


@pytest.mark.asyncio
async def test_sync_patient_first_time(mock_sync_dependencies):
    """Test that a patient without any summary gets it created and indexed in Qdrant"""
    service = MemorySyncService(**mock_sync_dependencies)
    patient_id = "pat-111"

    # 1. No existing patient memory record
    mock_sync_dependencies["patient_memory_repository"].get_by_patient_id = AsyncMock(return_value=None)

    # 2. Mock summary builder return
    dummy_summary = PatientMemoryCreate(
        patient_id=patient_id,
        ai_summary="Patient is healthy and active.",
        chronic_conditions=[],
        allergies=[],
        medications=[],
        surgeries=[],
        diagnoses=[],
        health_risks=[],
        recent_findings=[],
        timeline=[]
    )
    mock_sync_dependencies["patient_summary_builder"].build_summary = AsyncMock(return_value=dummy_summary)

    # 3. Mock active versions
    mock_sync_dependencies["index_version_service"].get_embedding_version = MagicMock(return_value="v1")
    mock_sync_dependencies["index_version_service"].get_schema_version = MagicMock(return_value=1)

    # 4. Mock Qdrant states
    mock_sync_dependencies["vector_service"].scroll = AsyncMock(side_effect=[
        ([], None),  # Initial check (no points)
        ([{"id": "pt-chunk-1", "payload": {"summary_version": 1}}], None)  # Post-verification check (points exist)
    ])
    mock_sync_dependencies["vector_service"].delete_by_filter = AsyncMock()
    mock_sync_dependencies["vector_service"].upsert_batch = AsyncMock()

    # 5. Mock Embedding generation
    dummy_embedding = EmbeddingResult(
        vector=[0.1] * 384,
        text="Patient is healthy and active.",
        metadata=EmbeddingMetadata(
            content_hash="dummy_hash",
            embedding_model="model",
            embedding_version="v1",
            indexed_at=datetime.now(timezone.utc),
            document_type="patient_memory",
            source_id=patient_id,
            collection_target="patient_memory"
        )
    )
    mock_sync_dependencies["embedding_service"].embed_batch = AsyncMock(return_value=[dummy_embedding])
    mock_sync_dependencies["embedding_service"].settings.EMBEDDING_DIMENSIONS = 384

    # 6. Mock MongoDB save and audit log
    mock_sync_dependencies["patient_memory_repository"].create = AsyncMock()
    mock_sync_dependencies["audit_log_service"].create_log = AsyncMock()

    # 7. Execute Sync
    res = await service.sync_patient(patient_id)

    # 8. Verifications
    assert res["success"] is True
    assert res["rebuilt_mongodb"] is True
    assert res["regenerated_qdrant"] is True
    assert res["summary_version"] == 1

    mock_sync_dependencies["patient_memory_repository"].create.assert_called_once()
    mock_sync_dependencies["vector_service"].delete_by_filter.assert_called_once()
    mock_sync_dependencies["vector_service"].upsert_batch.assert_called_once()
    mock_sync_dependencies["audit_log_service"].create_log.assert_called_once()


@pytest.mark.asyncio
async def test_sync_patient_unchanged_and_in_sync(mock_sync_dependencies):
    """Test that if the content hash and Qdrant index versions are identical, sync is skipped"""
    service = MemorySyncService(**mock_sync_dependencies)
    patient_id = "pat-222"

    # 1. Existing patient memory record
    existing_memory = PatientMemoryInDB(
        id="mem-222",
        patient_id=patient_id,
        ai_summary="Patient has mild allergy to dust.",
        chronic_conditions=[],
        allergies=["Dust"],
        medications=[],
        surgeries=[],
        diagnoses=[],
        health_risks=[],
        recent_findings=[],
        timeline=[],
        content_hash="temp_hash",
        summary_version=3,
        last_updated=datetime.now(timezone.utc)
    )
    mock_sync_dependencies["patient_memory_repository"].get_by_patient_id = AsyncMock(return_value=existing_memory)

    # 2. Build summary with same details
    new_summary = PatientMemoryCreate(
        patient_id=patient_id,
        ai_summary="Patient has mild allergy to dust.",
        chronic_conditions=[],
        allergies=["Dust"],
        medications=[],
        surgeries=[],
        diagnoses=[],
        health_risks=[],
        recent_findings=[],
        timeline=[]
    )
    mock_sync_dependencies["patient_summary_builder"].build_summary = AsyncMock(return_value=new_summary)

    # Stub hash function to match
    service.calculate_summary_hash = MagicMock(return_value="temp_hash")

    # 3. Mock active versions
    mock_sync_dependencies["index_version_service"].get_embedding_version = MagicMock(return_value="v1")
    mock_sync_dependencies["index_version_service"].get_schema_version = MagicMock(return_value=1)

    # 4. Mock Qdrant state - fully in sync
    qdrant_points = [
        {
            "id": "pt-1",
            "payload": {
                "patient_id": patient_id,
                "summary_version": 3,
                "embedding_version": "v1",
                "schema_version": 1
            }
        }
    ]
    mock_sync_dependencies["vector_service"].scroll = AsyncMock(return_value=(qdrant_points, None))

    # 5. Run Sync
    res = await service.sync_patient(patient_id)

    # 6. Verifications
    assert res["success"] is True
    assert res["rebuilt_mongodb"] is False
    assert res["regenerated_qdrant"] is False
    assert res["summary_version"] == 3

    mock_sync_dependencies["patient_memory_repository"].create.assert_not_called()
    mock_sync_dependencies["patient_memory_repository"].update.assert_not_called()
    mock_sync_dependencies["vector_service"].delete_by_filter.assert_not_called()
    mock_sync_dependencies["vector_service"].upsert_batch.assert_not_called()


@pytest.mark.asyncio
async def test_sync_patient_repair_out_of_sync_qdrant(mock_sync_dependencies):
    """Test that if the database summary matches but Qdrant point is missing, it regenerates vectors (index repair)"""
    service = MemorySyncService(**mock_sync_dependencies)
    patient_id = "pat-333"

    # 1. Existing patient memory record
    existing_memory = PatientMemoryInDB(
        id="mem-333",
        patient_id=patient_id,
        ai_summary="Patient has high cholesterol.",
        chronic_conditions=["High Cholesterol"],
        allergies=[],
        medications=[],
        surgeries=[],
        diagnoses=[],
        health_risks=[],
        recent_findings=[],
        timeline=[],
        content_hash="temp_hash_333",
        summary_version=5,
        last_updated=datetime.now(timezone.utc)
    )
    mock_sync_dependencies["patient_memory_repository"].get_by_patient_id = AsyncMock(return_value=existing_memory)

    # 2. New summary matches exactly
    new_summary = PatientMemoryCreate(
        patient_id=patient_id,
        ai_summary="Patient has high cholesterol.",
        chronic_conditions=["High Cholesterol"],
        allergies=[],
        medications=[],
        surgeries=[],
        diagnoses=[],
        health_risks=[],
        recent_findings=[],
        timeline=[]
    )
    mock_sync_dependencies["patient_summary_builder"].build_summary = AsyncMock(return_value=new_summary)
    service.calculate_summary_hash = MagicMock(return_value="temp_hash_333")

    # 3. Mock active versions
    mock_sync_dependencies["index_version_service"].get_embedding_version = MagicMock(return_value="v1")
    mock_sync_dependencies["index_version_service"].get_schema_version = MagicMock(return_value=1)

    # 4. Mock Qdrant states - initial is empty (index mismatch!), post-sync is filled
    mock_sync_dependencies["vector_service"].scroll = AsyncMock(side_effect=[
        ([], None),  # Out of sync initially
        ([{"id": "pt-rep-1", "payload": {"summary_version": 5}}], None)  # Post-verification succeeds
    ])
    mock_sync_dependencies["vector_service"].delete_by_filter = AsyncMock()
    mock_sync_dependencies["vector_service"].upsert_batch = AsyncMock()

    # 5. Mock embedding generation
    dummy_embedding = EmbeddingResult(
        vector=[0.2] * 384,
        text="Patient has high cholesterol.",
        metadata=EmbeddingMetadata(
            content_hash="temp_hash_333",
            embedding_model="model",
            embedding_version="v1",
            indexed_at=datetime.now(timezone.utc),
            document_type="patient_memory",
            source_id=patient_id,
            collection_target="patient_memory"
        )
    )
    mock_sync_dependencies["embedding_service"].embed_batch = AsyncMock(return_value=[dummy_embedding])
    mock_sync_dependencies["embedding_service"].settings.EMBEDDING_DIMENSIONS = 384
    mock_sync_dependencies["audit_log_service"].create_log = AsyncMock()

    # 6. Run Sync
    res = await service.sync_patient(patient_id)

    # 7. Verifications
    assert res["success"] is True
    assert res["rebuilt_mongodb"] is False  # DB stayed same
    assert res["regenerated_qdrant"] is True  # Qdrant was repaired!
    assert res["summary_version"] == 5

    mock_sync_dependencies["patient_memory_repository"].update.assert_not_called()
    mock_sync_dependencies["vector_service"].delete_by_filter.assert_called_once()
    mock_sync_dependencies["vector_service"].upsert_batch.assert_called_once()


@pytest.mark.asyncio
async def test_sync_patient_verification_failure(mock_sync_dependencies):
    """Test that if Qdrant upsert succeeds but verification finds mismatch/missing vectors, an error is raised"""
    service = MemorySyncService(**mock_sync_dependencies)
    patient_id = "pat-444"

    # 1. No existing patient memory record
    mock_sync_dependencies["patient_memory_repository"].get_by_patient_id = AsyncMock(return_value=None)

    # 2. Mock summary builder return
    dummy_summary = PatientMemoryCreate(
        patient_id=patient_id,
        ai_summary="Critical details.",
        chronic_conditions=[],
        allergies=[],
        medications=[],
        surgeries=[],
        diagnoses=[],
        health_risks=[],
        recent_findings=[],
        timeline=[]
    )
    mock_sync_dependencies["patient_summary_builder"].build_summary = AsyncMock(return_value=dummy_summary)

    # 3. Mock active versions
    mock_sync_dependencies["index_version_service"].get_embedding_version = MagicMock(return_value="v1")
    mock_sync_dependencies["index_version_service"].get_schema_version = MagicMock(return_value=1)

    # 4. Mock Qdrant states - both initial and post-sync return empty (represents write failures/mismatch)
    mock_sync_dependencies["vector_service"].scroll = AsyncMock(return_value=([], None))
    mock_sync_dependencies["vector_service"].delete_by_filter = AsyncMock()
    mock_sync_dependencies["vector_service"].upsert_batch = AsyncMock()

    # 5. Mock Embedding generation
    dummy_embedding = EmbeddingResult(
        vector=[0.3] * 384,
        text="Critical details.",
        metadata=EmbeddingMetadata(
            content_hash="hash",
            embedding_model="model",
            embedding_version="v1",
            indexed_at=datetime.now(timezone.utc),
            document_type="patient_memory",
            source_id=patient_id,
            collection_target="patient_memory"
        )
    )
    mock_sync_dependencies["embedding_service"].embed_batch = AsyncMock(return_value=[dummy_embedding])
    mock_sync_dependencies["embedding_service"].settings.EMBEDDING_DIMENSIONS = 384

    # 6. Mock MongoDB save
    mock_sync_dependencies["patient_memory_repository"].create = AsyncMock()

    # 7. Execute Sync - should raise ValueError on verification mismatch
    with pytest.raises(ValueError, match="Post-sync verification failed"):
        await service.sync_patient(patient_id)
