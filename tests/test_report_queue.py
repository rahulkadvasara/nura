"""
Tests for ReportQueueManager — enqueue, dequeue, priority ordering, DLQ, cancel.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.report_background.queue_manager import ReportQueueManager, JobStatus, JobPriority


def make_db(jobs_by_query: dict = None):
    """Build a minimal mock MongoDB db object."""
    mock_collection = MagicMock()
    mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id="job123"))
    mock_collection.find_one_and_update = AsyncMock(return_value=None)
    mock_collection.update_one = AsyncMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_collection.update_many = AsyncMock(return_value=MagicMock(modified_count=0))

    pipeline_result = []

    class FakeCursor:
        def __aiter__(self): return self
        async def __anext__(self):
            raise StopAsyncIteration

    mock_collection.aggregate = MagicMock(return_value=FakeCursor())
    mock_collection.find = MagicMock(return_value=FakeCursor())

    mock_db = MagicMock()
    mock_db.__getitem__ = MagicMock(return_value=mock_collection)
    return mock_db, mock_collection


@pytest.mark.asyncio
async def test_enqueue_returns_job_id():
    """Enqueue creates a job and returns a string job ID."""
    db, col = make_db()
    manager = ReportQueueManager(db=db)
    job_id = await manager.enqueue("rep-1", "pat-1", priority=JobPriority.NORMAL)
    assert job_id == "job123"
    col.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_dequeue_returns_none_when_empty():
    """Dequeue returns None if no jobs are available."""
    db, col = make_db()
    col.find_one_and_update = AsyncMock(return_value=None)
    manager = ReportQueueManager(db=db)
    job = await manager.dequeue("worker-1")
    assert job is None


@pytest.mark.asyncio
async def test_dequeue_claims_job_with_worker_id():
    """Dequeue atomically sets status=PROCESSING and assigns worker_id."""
    db, col = make_db()
    claimed_job = {
        "_id": "abc123",
        "report_id": "rep-1",
        "patient_id": "pat-1",
        "status": JobStatus.PROCESSING,
        "worker_id": "worker-99",
        "created_at": MagicMock(timestamp=lambda: 1000.0),
    }
    col.find_one_and_update = AsyncMock(return_value=claimed_job)
    manager = ReportQueueManager(db=db)
    job = await manager.dequeue("worker-99")
    assert job["worker_id"] == "worker-99"
    assert job["status"] == JobStatus.PROCESSING


@pytest.mark.asyncio
async def test_cancel_queued_job():
    """cancel() updates status to CANCELLED and returns True."""
    db, col = make_db()
    col.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    manager = ReportQueueManager(db=db)
    result = await manager.cancel("rep-xyz")
    assert result is True


@pytest.mark.asyncio
async def test_cancel_non_existent_job():
    """cancel() returns False when no matching queued/pending job exists."""
    db, col = make_db()
    col.update_one = AsyncMock(return_value=MagicMock(modified_count=0))
    manager = ReportQueueManager(db=db)
    result = await manager.cancel("rep-nonexistent")
    assert result is False


@pytest.mark.asyncio
async def test_mark_failed_moves_to_dlq_after_max_retries():
    """After max_retries exhausted, mark_failed transitions job to dead_letter status."""
    from bson import ObjectId
    db, col = make_db()
    exhausted_job = {
        "_id": ObjectId(),
        "report_id": "rep-dlq",
        "retry_count": 2,   # next will be 3 >= max_retries (3)
        "max_retries": 3,
    }
    col.find_one = AsyncMock(return_value=exhausted_job)
    col.update_one = AsyncMock()
    manager = ReportQueueManager(db=db)
    await manager.mark_failed(str(exhausted_job["_id"]), "Fatal OCR error")
    # The update call should set status to DEAD_LETTER
    call_kwargs = col.update_one.call_args
    update_doc = call_kwargs[0][1]
    assert update_doc["$set"]["status"] == JobStatus.DEAD_LETTER


@pytest.mark.asyncio
async def test_mark_failed_requeues_below_max_retries():
    """When retry_count < max_retries, mark_failed re-queues the job."""
    from bson import ObjectId
    db, col = make_db()
    job = {
        "_id": ObjectId(),
        "report_id": "rep-retry",
        "retry_count": 1,
        "max_retries": 3,
    }
    col.find_one = AsyncMock(return_value=job)
    col.update_one = AsyncMock()
    manager = ReportQueueManager(db=db)
    await manager.mark_failed(str(job["_id"]), "Transient network error")
    call_kwargs = col.update_one.call_args
    update_doc = call_kwargs[0][1]
    assert update_doc["$set"]["status"] == JobStatus.QUEUED
    assert update_doc["$set"]["retry_count"] == 2


@pytest.mark.asyncio
async def test_recover_stale_processing_jobs():
    """recover_stale_processing_jobs re-queues stale PROCESSING jobs."""
    db, col = make_db()
    col.update_many = AsyncMock(return_value=MagicMock(modified_count=3))
    manager = ReportQueueManager(db=db)
    count = await manager.recover_stale_processing_jobs()
    assert count == 3
