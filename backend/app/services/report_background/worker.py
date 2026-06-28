"""
Nura - Background Worker
Async worker that claims jobs from the queue and executes the pipeline.
Supports configurable worker count, heartbeat, graceful shutdown, and auto-resume.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.services.report_background.queue_manager import ReportQueueManager, JobStatus
from app.services.report_background.progress_tracker import ReportProgressTracker
from app.services.report_background.background_telemetry import BackgroundTelemetry

logger = logging.getLogger("nura.report_background.worker")

HEARTBEAT_INTERVAL_SECONDS = 10
POLL_INTERVAL_SECONDS = 2


class BackgroundWorker:
    """
    Single async worker that continuously polls the queue and executes pipeline jobs.
    Each worker has a unique ID for heartbeat tracking.
    """

    def __init__(
        self,
        worker_id: str,
        queue_manager: ReportQueueManager,
        pipeline_service,
        progress_tracker: ReportProgressTracker,
        telemetry: BackgroundTelemetry,
        shutdown_event: asyncio.Event,
        db=None,
    ):
        self.worker_id = worker_id
        self.queue_manager = queue_manager
        self.pipeline_service = pipeline_service
        self.progress_tracker = progress_tracker
        self.telemetry = telemetry
        self.shutdown_event = shutdown_event
        self.db = db
        self._current_job_id: Optional[str] = None
        self._is_active: bool = False

    @property
    def is_active(self) -> bool:
        return self._is_active

    async def run(self) -> None:
        """Main worker loop — polls queue, executes jobs, records heartbeats."""
        logger.info(f"Worker {self.worker_id} started")

        heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        try:
            while not self.shutdown_event.is_set():
                job = await self.queue_manager.dequeue(self.worker_id)

                if job is None:
                    # No work available — wait before polling again
                    self._is_active = False
                    await asyncio.sleep(POLL_INTERVAL_SECONDS)
                    continue

                self._is_active = True
                job_id = str(job["_id"])
                report_id = job["report_id"]
                enqueued_at = job.get("created_at")

                # Record queue wait time
                if enqueued_at:
                    wait_ms = (time.time() - enqueued_at.timestamp()) * 1000
                    self.telemetry.record_queue_wait(wait_ms)

                logger.info(f"Worker {self.worker_id} processing report {report_id} (job {job_id})")
                self._current_job_id = job_id

                try:
                    # Update progress to first active stage
                    await self.progress_tracker.set_stage(report_id, "ocr")

                    # Execute the full pipeline — delegates to PipelineService
                    result = await self.pipeline_service.execute_pipeline(report_id)

                    if result.get("success"):
                        await self.queue_manager.mark_completed(job_id)
                        await self.progress_tracker.mark_completed(report_id)
                        self.telemetry.record_completion()
                        logger.info(f"Worker {self.worker_id} completed report {report_id}")
                    else:
                        error = result.get("error", "Pipeline returned non-success without explicit error")
                        await self.queue_manager.mark_failed(job_id, error)
                        await self.progress_tracker.mark_failed(report_id, error)
                        self.telemetry.record_failure(error)
                        logger.warning(f"Worker {self.worker_id} pipeline failed for {report_id}: {error}")

                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Worker {self.worker_id} unhandled error for {report_id}: {error_msg}", exc_info=True)
                    await self.queue_manager.mark_failed(job_id, error_msg)
                    await self.progress_tracker.mark_failed(report_id, error_msg)
                    self.telemetry.record_failure(error_msg)
                finally:
                    self._current_job_id = None
                    self._is_active = False

        finally:
            heartbeat_task.cancel()
            logger.info(f"Worker {self.worker_id} shut down cleanly")

    async def _heartbeat_loop(self) -> None:
        """Periodically write worker heartbeat to MongoDB so the scheduler can detect crashes."""
        while not self.shutdown_event.is_set():
            try:
                if self.db is not None:
                    await self.db["worker_heartbeats"].update_one(
                        {"worker_id": self.worker_id},
                        {
                            "$set": {
                                "worker_id": self.worker_id,
                                "is_active": self._is_active,
                                "current_job_id": self._current_job_id,
                                "last_seen": datetime.now(timezone.utc),
                            }
                        },
                        upsert=True,
                    )
            except Exception as e:
                logger.warning(f"Heartbeat failed for worker {self.worker_id}: {e}")
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
