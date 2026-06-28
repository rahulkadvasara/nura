"""
Load and integration tests for the background processing system.
Tests concurrent job processing, progress tracking, batch dispatch, and large document streaming.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.services.report_background.job_dispatcher import JobDispatcher
from app.services.report_background.progress_tracker import ReportProgressTracker, STAGE_WEIGHTS
from app.services.report_background.background_telemetry import BackgroundTelemetry
from app.services.report_background.queue_manager import ReportQueueManager


# ─────────────────────────────────────────────────────────────────────────────
# Progress Tracker
# ─────────────────────────────────────────────────────────────────────────────

def make_mock_progress_db(stored: dict | None = None):
    """Build a mock MongoDB database for progress tracker."""
    storage = stored or {}

    col = MagicMock()

    async def update_one(filt, update, upsert=False):
        report_id = filt.get("report_id", "unknown")
        storage[report_id] = update.get("$set", {})

    async def find_one(filt):
        report_id = filt.get("report_id")
        return storage.get(report_id)

    col.update_one = update_one
    col.find_one = find_one
    col.delete_one = AsyncMock()

    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=col)
    return db, storage


@pytest.mark.asyncio
async def test_progress_tracker_stage_percentages():
    """Progress tracker assigns correct percentages at each stage."""
    db, storage = make_mock_progress_db()
    tracker = ReportProgressTracker(db=db)
    report_id = "rep-progress-test"

    for stage, expected_pct in STAGE_WEIGHTS.items():
        await tracker.set_stage(report_id, stage)
        progress = await tracker.get_progress(report_id)
        assert progress["percentage"] == expected_pct, \
            f"Stage '{stage}' should be {expected_pct}% but got {progress['percentage']}%"


@pytest.mark.asyncio
async def test_progress_tracker_completed_is_100():
    """mark_completed sets percentage to 100%."""
    db, storage = make_mock_progress_db()
    tracker = ReportProgressTracker(db=db)
    await tracker.mark_completed("rep-done")
    progress = await tracker.get_progress("rep-done")
    assert progress["percentage"] == 100


@pytest.mark.asyncio
async def test_progress_tracker_failed_sets_zero():
    """mark_failed sets percentage to 0 and stores error message."""
    db, storage = make_mock_progress_db()
    tracker = ReportProgressTracker(db=db)
    await tracker.mark_failed("rep-fail", "OCR timeout")
    progress = await tracker.get_progress("rep-fail")
    assert progress["percentage"] == 0
    assert progress.get("error") == "OCR timeout"


# ─────────────────────────────────────────────────────────────────────────────
# Job Dispatcher — Batch Dispatch
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_batch_dispatch_creates_individual_jobs():
    """dispatch_batch creates one job per report and returns mapping."""
    db, storage = make_mock_progress_db()
    tracker = ReportProgressTracker(db=db)

    mock_queue = MagicMock()
    job_counter = [0]

    async def enqueue(report_id, patient_id, priority, metadata=None):
        job_counter[0] += 1
        return f"job-{job_counter[0]}"

    mock_queue.enqueue = enqueue

    dispatcher = JobDispatcher(queue_manager=mock_queue, progress_tracker=tracker)

    reports = [
        {"report_id": f"rep-{i}", "patient_id": "pat-1"}
        for i in range(5)
    ]
    results = await dispatcher.dispatch_batch(reports)

    assert len(results) == 5
    assert all(r["success"] is True for r in results)
    assert job_counter[0] == 5


@pytest.mark.asyncio
async def test_batch_dispatch_handles_partial_failures():
    """Batch dispatch records failure for individual reports without aborting the batch."""
    db, storage = make_mock_progress_db()
    tracker = ReportProgressTracker(db=db)

    call_count = [0]
    mock_queue = MagicMock()

    async def enqueue_with_failure(report_id, patient_id, priority, metadata=None):
        call_count[0] += 1
        if call_count[0] == 2:
            raise RuntimeError("DB write failed")
        return f"job-{call_count[0]}"

    mock_queue.enqueue = enqueue_with_failure

    dispatcher = JobDispatcher(queue_manager=mock_queue, progress_tracker=tracker)
    reports = [{"report_id": f"rep-{i}", "patient_id": "pat-x"} for i in range(3)]
    results = await dispatcher.dispatch_batch(reports)

    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    assert len(successes) == 2
    assert len(failures) == 1


# ─────────────────────────────────────────────────────────────────────────────
# Load Simulation
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_concurrent_dispatch_10_reports():
    """10 reports can be dispatched concurrently via asyncio.gather without conflicts."""
    db, storage = make_mock_progress_db()
    tracker = ReportProgressTracker(db=db)

    call_count = [0]
    mock_queue = MagicMock()

    async def enqueue(report_id, patient_id, priority, metadata=None):
        await asyncio.sleep(0.01)  # simulate async latency
        call_count[0] += 1
        return f"job-{call_count[0]}"

    mock_queue.enqueue = enqueue
    dispatcher = JobDispatcher(queue_manager=mock_queue, progress_tracker=tracker)

    tasks = [
        dispatcher.dispatch(f"rep-load-{i}", "pat-load")
        for i in range(10)
    ]
    job_ids = await asyncio.gather(*tasks)

    assert len(job_ids) == 10
    assert call_count[0] == 10


@pytest.mark.asyncio
async def test_large_document_parallel_page_processing():
    """100-page document can be processed in parallel batches without error."""
    from app.services.report_background.parallel_processor import ParallelOCRProcessor

    pages_processed = []

    async def process_page(page_num):
        await asyncio.sleep(0.001)  # simulate very fast OCR
        pages_processed.append(page_num)
        return {"page": page_num, "text": f"content {page_num}"}

    processor = ParallelOCRProcessor(max_concurrency=10)
    tasks = [process_page(i) for i in range(100)]
    results = await processor.process_pages_parallel(tasks)

    assert len(results) == 100
    errors = [r for r in results if isinstance(r, Exception)]
    assert len(errors) == 0
