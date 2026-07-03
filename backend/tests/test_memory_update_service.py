"""
Nura - Memory Update Service Tests
Verifies conditional database index operations and longitudinal appends
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.chat_memory.memory_update_service import MemoryUpdateService


@pytest.mark.asyncio
async def test_evaluate_and_sync_skipped():
    evaluator = AsyncMock()
    evaluator.evaluate_session = AsyncMock(return_value={
        "should_store_chat_memory": False,
        "should_update_patient_memory": False,
        "memory_score": 0.1
    })

    service = MemoryUpdateService(
        patient_memory_repository=AsyncMock(),
        embedding_service=AsyncMock(),
        vector_service=AsyncMock(),
        evaluator=evaluator,
        summary_service=AsyncMock()
    )

    res = await service.evaluate_and_sync_session("sess123", "pat123", ["msg1"])
    assert res["status"] == "skipped"


@pytest.mark.asyncio
async def test_evaluate_and_sync_stored():
    evaluator = AsyncMock()
    evaluator.evaluate_session = AsyncMock(return_value={
        "should_store_chat_memory": True,
        "should_update_patient_memory": True,
        "memory_score": 0.8
    })

    summary_service = AsyncMock()
    summary_service.generate_summary = AsyncMock(return_value={
        "summary": "High blood pressure notes.",
        "keywords": ["hypertension"],
        "entities": ["hypertension"],
        "medications": ["Lisinopril"],
        "symptoms": ["chest discomfort"],
        "diagnoses": ["hypertension"],
        "recommendations": ["Reduce sodium"],
        "followups": []
    })

    patient_repo = AsyncMock()
    # Mock return existing patient memory as None to test creation flow
    patient_repo.get_by_patient_id = AsyncMock(return_value=None)
    patient_repo.create = AsyncMock()

    embedding_service = AsyncMock()
    embedding_service.embed = AsyncMock(return_value=[0.1, 0.2, 0.3])

    vector_service = AsyncMock()
    vector_service.create_collection = AsyncMock()
    vector_service.upsert = AsyncMock()

    service = MemoryUpdateService(
        patient_memory_repository=patient_repo,
        embedding_service=embedding_service,
        vector_service=vector_service,
        evaluator=evaluator,
        summary_service=summary_service
    )

    # Mock chat message repository internally inside evaluate_and_sync_session
    # We can mock get_chat_message_repository patch
    import app.core.dependencies as deps_module
    original_get_repo = deps_module.get_chat_message_repository
    
    mock_msg_repo = AsyncMock()
    mock_msg_repo.get_by_session_id = AsyncMock(return_value=[])
    deps_module.get_chat_message_repository = lambda: mock_msg_repo

    try:
        res = await service.evaluate_and_sync_session("sess123", "pat123", ["msg1", "msg2"])
        assert res["status"] == "stored"
        # Verify vector upsert was triggered
        vector_service.upsert.assert_called_once()
        # Verify MongoDB insert was triggered
        patient_repo.create.assert_called_once()
    finally:
        # Restore original repo getter function
        deps_module.get_chat_message_repository = original_get_repo
