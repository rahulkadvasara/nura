import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from datetime import datetime, timezone

from app.services.drug_background.queue_manager import DrugQueueManager, JobStatus, JobPriority
from app.services.drug_background.worker import BackgroundWorker
from app.services.drug_background.scheduler import WorkerScheduler
from app.services.drug_background.telemetry import DrugBackgroundTelemetry
from app.services.drug_safety.validation_service import MedicationValidationService

@pytest.mark.asyncio
async def test_queue_manager_enqueue_de_duplicate():
    mock_coll = AsyncMock()
    # Mock find_one to return None (no duplicate exists)
    mock_coll.find_one.return_value = None
    mock_coll.insert_one.return_value = MagicMock(inserted_id=ObjectId())
    
    db = MagicMock()
    db.__getitem__.return_value = mock_coll
    
    q_mgr = DrugQueueManager(db)
    
    job_id = await q_mgr.enqueue("pat-123", priority=JobPriority.HIGH)
    assert job_id is not None
    mock_coll.insert_one.assert_called_once()
    
    # Mock find_one to return the existing job (simulating duplicate check)
    mock_coll.find_one.return_value = {"_id": ObjectId(job_id), "patient_id": "pat-123", "status": JobStatus.QUEUED}
    mock_coll.insert_one.reset_mock()
    
    duplicate_job_id = await q_mgr.enqueue("pat-123")
    assert duplicate_job_id == job_id
    mock_coll.insert_one.assert_not_called()

@pytest.mark.asyncio
async def test_worker_polling_and_completion():
    mock_queue = AsyncMock()
    mock_val_service = AsyncMock()
    mock_telemetry = MagicMock(spec=DrugBackgroundTelemetry)
    shutdown_event = asyncio.Event()
    db = MagicMock()
    
    # Mock worker heartbeats collection in db
    mock_hb_coll = AsyncMock()
    db.__getitem__.return_value = mock_hb_coll

    job = {
        "_id": ObjectId(),
        "patient_id": "pat-55",
        "created_at": datetime.now(timezone.utc)
    }
    # First dequeue returns the job, second returns None to stop
    mock_queue.dequeue.side_effect = [job, None]
    # Mock successful patient memory update
    mock_val_service.validate_and_update_patient_memory.return_value = {"status": "success"}

    worker = BackgroundWorker(
        worker_id="test-worker",
        queue_manager=mock_queue,
        validation_service=mock_val_service,
        telemetry=mock_telemetry,
        shutdown_event=shutdown_event,
        db=db
    )
    
    # Stop worker automatically by setting shutdown event after a brief delay
    async def stop_after_delay():
        await asyncio.sleep(0.05)
        shutdown_event.set()
        
    asyncio.create_task(stop_after_delay())
    
    await worker.run()
    
    # Assertions
    mock_val_service.validate_and_update_patient_memory.assert_called_once_with("pat-55")
    mock_queue.mark_completed.assert_called_once()
    mock_telemetry.record_completion.assert_called_once()

@pytest.mark.asyncio
async def test_worker_failure_retry_and_dlq():
    mock_queue = AsyncMock()
    mock_val_service = AsyncMock()
    mock_telemetry = MagicMock(spec=DrugBackgroundTelemetry)
    shutdown_event = asyncio.Event()
    db = MagicMock()
    
    mock_hb_coll = AsyncMock()
    db.__getitem__.return_value = mock_hb_coll

    job = {
        "_id": ObjectId(),
        "patient_id": "pat-55",
        "created_at": datetime.now(timezone.utc)
    }
    mock_queue.dequeue.side_effect = [job, None]
    # Simulate unhandled exception in validation service
    mock_val_service.validate_and_update_patient_memory.side_effect = Exception("Groq Timeout")

    worker = BackgroundWorker(
        worker_id="test-worker",
        queue_manager=mock_queue,
        validation_service=mock_val_service,
        telemetry=mock_telemetry,
        shutdown_event=shutdown_event,
        db=db
    )
    
    async def stop_after_delay():
        await asyncio.sleep(0.05)
        shutdown_event.set()
        
    asyncio.create_task(stop_after_delay())
    
    await worker.run()
    
    mock_queue.mark_failed.assert_called_once_with(str(job["_id"]), "Groq Timeout")
    mock_telemetry.record_failure.assert_called_once_with("Groq Timeout")
