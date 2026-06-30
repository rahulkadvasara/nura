import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional

from app.services.drug_background.worker import BackgroundWorker
from app.services.drug_background.queue_manager import DrugQueueManager
from app.services.drug_background.telemetry import DrugBackgroundTelemetry
from app.services.drug_safety.validation_service import MedicationValidationService

logger = logging.getLogger("nura.drug_background.scheduler")

DEFAULT_WORKER_COUNT = 2

class WorkerScheduler:
    """
    Manages a pool of background validation workers.
    Ensures safe initialization, graceful worker pool shutdown, and stuck task recovery on restarts.
    """

    def __init__(
        self,
        queue_manager: DrugQueueManager,
        validation_service: MedicationValidationService,
        telemetry: DrugBackgroundTelemetry,
        worker_count: int = DEFAULT_WORKER_COUNT,
        db=None,
    ):
        self.queue_manager = queue_manager
        self.validation_service = validation_service
        self.telemetry = telemetry
        self.worker_count = worker_count
        self.db = db

        self._shutdown_event: asyncio.Event = asyncio.Event()
        self._workers: List[BackgroundWorker] = []
        self._tasks: List[asyncio.Task] = []
        self._running: bool = False

    async def start(self) -> None:
        """Start the background worker pool and recover any stale processing jobs."""
        if self._running:
            logger.warning("WorkerScheduler already running — ignoring start() call")
            return

        logger.info(f"WorkerScheduler starting {self.worker_count} drug validation workers")
        self._shutdown_event.clear()

        # Recover jobs stuck in PROCESSING from a prior crash
        recovered = await self.queue_manager.recover_stale_processing_jobs()
        if recovered:
            logger.info(f"Recovered {recovered} stale background drug validation jobs at startup")

        # Spawn worker tasks
        for _ in range(self.worker_count):
            worker_id = f"drug-worker-{uuid.uuid4().hex[:8]}"
            worker = BackgroundWorker(
                worker_id=worker_id,
                queue_manager=self.queue_manager,
                validation_service=self.validation_service,
                telemetry=self.telemetry,
                shutdown_event=self._shutdown_event,
                db=self.db,
            )
            self._workers.append(worker)
            task = asyncio.create_task(worker.run(), name=f"drug-worker-{worker_id}")
            self._tasks.append(task)

        self._running = True
        logger.info(f"WorkerScheduler successfully running {self.worker_count} workers")

    async def stop(self) -> None:
        """Signal workers to stop and wait for in-flight tasks to complete."""
        if not self._running:
            return

        logger.info("WorkerScheduler shutting down — signalling background workers")
        self._shutdown_event.set()

        # Wait for worker tasks to complete (with a 30s timeout)
        if self._tasks:
            await asyncio.wait(self._tasks, timeout=30)

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
        """Fetch live heartbeat records from MongoDB for all active workers."""
        if self.db is None:
            return []
        cursor = self.db["drug_worker_heartbeats"].find({})
        records = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            records.append(doc)
        return records


# Global Singleton Reference Scheduler
_drug_worker_scheduler_instance: Optional[WorkerScheduler] = None

def get_drug_worker_scheduler(
    queue_manager=None,
    validation_service=None,
    telemetry=None,
    db=None,
    worker_count=DEFAULT_WORKER_COUNT
) -> WorkerScheduler:
    global _drug_worker_scheduler_instance
    if _drug_worker_scheduler_instance is None:
        if queue_manager is None or validation_service is None or telemetry is None or db is None:
            # Import dependencies dynamically to avoid circular references
            from app.core.dependencies import (
                get_database,
                get_drug_queue_manager,
                get_medication_validation_service,
                get_drug_background_telemetry
            )
            # Fetch standard references
            database = db or get_database()
            q_mgr = queue_manager or get_drug_queue_manager()
            v_svc = validation_service or get_medication_validation_service()
            tel = telemetry or get_drug_background_telemetry()
        else:
            database = db
            q_mgr = queue_manager
            v_svc = validation_service
            tel = telemetry
            
        _drug_worker_scheduler_instance = WorkerScheduler(
            queue_manager=q_mgr,
            validation_service=v_svc,
            telemetry=tel,
            worker_count=worker_count,
            db=database
        )
    return _drug_worker_scheduler_instance
