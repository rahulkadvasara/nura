"""
Tests for BackgroundWorker and WorkerScheduler — job execution, heartbeat, graceful shutdown.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.services.report_background.worker import BackgroundWorker
from app.services.report_background.queue_manager import JobStatus
from app.services.report_background.background_telemetry import BackgroundTelemetry


def make_mock_queue(job=None):
    q = MagicMock()
    q.dequeue = AsyncMock(side_effect=[job, None])  # returns job once, then None (empty)
    q.mark_completed = AsyncMock()
    q.mark_failed = AsyncMock()
    return q


def make_mock_pipeline(success=True, error=None):
    p = MagicMock()
    if success:
        p.execute_pipeline = AsyncMock(return_value={"success": True, "status": "READY"})
    else:
        p.execute_pipeline = AsyncMock(return_value={"success": False, "error": error or "stage failed"})
    return p


def make_mock_progress():
    t = MagicMock()
    t.set_stage = AsyncMock()
    t.mark_completed = AsyncMock()
    t.mark_failed = AsyncMock()
    return t


def make_mock_db():
    col = MagicMock()
    col.update_one = AsyncMock()
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=col)
    return db


@pytest.mark.asyncio
async def test_worker_processes_job_successfully():
    """Worker dequeues a job, executes pipeline, marks job completed and progress=100%."""
    shutdown = asyncio.Event()
    job = {
        "_id": "job-001",
        "report_id": "rep-001",
        "status": JobStatus.PROCESSING,
        "worker_id": "worker-1",
        "created_at": datetime.now(timezone.utc),
    }

    mock_queue = make_mock_queue(job=job)
    mock_pipeline = make_mock_pipeline(success=True)
    mock_progress = make_mock_progress()
    mock_telemetry = BackgroundTelemetry()
    mock_db = make_mock_db()

    worker = BackgroundWorker(
        worker_id="worker-1",
        queue_manager=mock_queue,
        pipeline_service=mock_pipeline,
        progress_tracker=mock_progress,
        telemetry=mock_telemetry,
        shutdown_event=shutdown,
        db=mock_db,
    )

    # Run the worker but signal shutdown after 2 poll iterations
    async def stop_after_work():
        await asyncio.sleep(0.1)
        shutdown.set()

    await asyncio.gather(worker.run(), stop_after_work())

    mock_queue.mark_completed.assert_called_once_with("job-001")
    mock_progress.mark_completed.assert_called_once_with("rep-001")


@pytest.mark.asyncio
async def test_worker_handles_pipeline_failure():
    """Worker records failure when pipeline returns success=False."""
    shutdown = asyncio.Event()
    job = {
        "_id": "job-002",
        "report_id": "rep-002",
        "status": JobStatus.PROCESSING,
        "worker_id": "worker-2",
        "created_at": datetime.now(timezone.utc),
    }

    mock_queue = make_mock_queue(job=job)
    mock_pipeline = make_mock_pipeline(success=False, error="OCR service unavailable")
    mock_progress = make_mock_progress()
    telemetry = BackgroundTelemetry()
    mock_db = make_mock_db()

    worker = BackgroundWorker(
        worker_id="worker-2",
        queue_manager=mock_queue,
        pipeline_service=mock_pipeline,
        progress_tracker=mock_progress,
        telemetry=telemetry,
        shutdown_event=shutdown,
        db=mock_db,
    )

    async def stop_after():
        await asyncio.sleep(0.1)
        shutdown.set()

    await asyncio.gather(worker.run(), stop_after())

    mock_queue.mark_failed.assert_called_once()
    mock_progress.mark_failed.assert_called_once()


@pytest.mark.asyncio
async def test_worker_graceful_shutdown_while_idle():
    """Worker exits cleanly when shutdown event is set while no jobs are available."""
    shutdown = asyncio.Event()
    mock_queue = MagicMock()
    mock_queue.dequeue = AsyncMock(return_value=None)  # always empty

    mock_progress = make_mock_progress()
    telemetry = BackgroundTelemetry()
    mock_db = make_mock_db()

    worker = BackgroundWorker(
        worker_id="worker-3",
        queue_manager=mock_queue,
        pipeline_service=MagicMock(),
        progress_tracker=mock_progress,
        telemetry=telemetry,
        shutdown_event=shutdown,
        db=mock_db,
    )

    async def trigger_shutdown():
        await asyncio.sleep(0.05)
        shutdown.set()

    # Should complete without hanging
    await asyncio.gather(worker.run(), trigger_shutdown())
    # If we get here, the worker shut down cleanly
    assert True


@pytest.mark.asyncio
async def test_background_telemetry_records_completion():
    """BackgroundTelemetry correctly counts completions and computes reports/hour."""
    telemetry = BackgroundTelemetry()
    telemetry.record_completion(pages=5)
    telemetry.record_completion(pages=12)
    telemetry.record_completion(pages=8)
    assert telemetry.reports_per_hour() == 3.0
    assert telemetry.avg_pages_per_report() == pytest.approx((5 + 12 + 8) / 3, 0.01)


@pytest.mark.asyncio
async def test_background_telemetry_failure_rate():
    """BackgroundTelemetry computes failure_rate correctly."""
    telemetry = BackgroundTelemetry()
    telemetry.record_completion()
    telemetry.record_completion()
    telemetry.record_failure("timeout")
    # 1 failure / 3 total = 33.3%
    assert telemetry.failure_rate() == pytest.approx(33.3, 0.5)


@pytest.mark.asyncio
async def test_background_telemetry_cache_hit_ratio():
    """BackgroundTelemetry tracks cache hit ratios per cache type."""
    telemetry = BackgroundTelemetry()
    telemetry.record_cache_hit("ocr")
    telemetry.record_cache_hit("ocr")
    telemetry.record_cache_miss("ocr")
    # 2 hits, 1 miss = 2/3 ≈ 0.667
    assert telemetry.cache_hit_ratio("ocr") == pytest.approx(0.667, 0.01)
