"""
Nura - Worker Scheduler
Manages the background worker pool lifecycle (start, stop, scale).
Designed to integrate with FastAPI lifespan events.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.services.report_background.worker import BackgroundWorker
from app.services.report_background.queue_manager import ReportQueueManager
from app.services.report_background.progress_tracker import ReportProgressTracker
from app.services.report_background.background_telemetry import BackgroundTelemetry

logger = logging.getLogger("nura.report_background.scheduler")

DEFAULT_WORKER_COUNT = 3


class WorkerScheduler:
    """
    Manages a pool of BackgroundWorker instances.
    Starts workers on application startup, stops them on shutdown.
    Supports stale-job recovery on restart.
    """

    def __init__(
        self,
        queue_manager: ReportQueueManager,
        pipeline_service,
        progress_tracker: ReportProgressTracker,
        telemetry: BackgroundTelemetry,
        worker_count: int = DEFAULT_WORKER_COUNT,
        db=None,
    ):
        self.queue_manager = queue_manager
        self.pipeline_service = pipeline_service
        self.progress_tracker = progress_tracker
        self.telemetry = telemetry
        self.worker_count = worker_count
        self.db = db

        self._shutdown_event: asyncio.Event = asyncio.Event()
        self._workers: List[BackgroundWorker] = []
        self._tasks: List[asyncio.Task] = []
        self._running: bool = False

    async def start(self) -> None:
        """Start the worker pool and recover any stale processing jobs."""
        if self._running:
            logger.warning("WorkerScheduler already running — ignoring start() call")
            return

        logger.info(f"WorkerScheduler starting {self.worker_count} workers")
        self._shutdown_event.clear()

        # Recover jobs that were stuck in PROCESSING from a prior crash
        recovered = await self.queue_manager.recover_stale_processing_jobs()
        if recovered:
            logger.info(f"Recovered {recovered} stale jobs at startup")

        # Spawn worker tasks
        for _ in range(self.worker_count):
            worker_id = f"worker-{uuid.uuid4().hex[:8]}"
            worker = BackgroundWorker(
                worker_id=worker_id,
                queue_manager=self.queue_manager,
                pipeline_service=self.pipeline_service,
                progress_tracker=self.progress_tracker,
                telemetry=self.telemetry,
                shutdown_event=self._shutdown_event,
                db=self.db,
            )
            self._workers.append(worker)
            task = asyncio.create_task(worker.run(), name=f"report-worker-{worker_id}")
            self._tasks.append(task)

        self._running = True
        self.telemetry.set_worker_counts(self.worker_count, 0)
        logger.info(f"WorkerScheduler running {self.worker_count} workers")

    async def stop(self) -> None:
        """Signal all workers to stop and wait for in-flight jobs to complete."""
        if not self._running:
            return

        logger.info("WorkerScheduler shutting down — signalling workers")
        self._shutdown_event.set()

        # Wait for all worker tasks to complete (with a 60s timeout)
        if self._tasks:
            await asyncio.wait(self._tasks, timeout=60)

        self._workers.clear()
        self._tasks.clear()
        self._running = False
        logger.info("WorkerScheduler shut down cleanly")

    def worker_count_active(self) -> int:
        return sum(1 for w in self._workers if w.is_active)

    def worker_count_idle(self) -> int:
        return sum(1 for w in self._workers if not w.is_active)

    def get_worker_status(self) -> List[Dict[str, Any]]:
        """Return status snapshot for all workers."""
        return [
            {
                "worker_id": w.worker_id,
                "is_active": w.is_active,
                "current_job_id": w._current_job_id,
            }
            for w in self._workers
        ]

    async def get_heartbeats(self) -> List[Dict[str, Any]]:
        """Fetch live heartbeat records from MongoDB for all workers."""
        if self.db is None:
            return []
        cursor = self.db["worker_heartbeats"].find({})
        records = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            records.append(doc)
        return records
