import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional

from app.services.drug_background.queue_manager import DrugQueueManager
from app.services.drug_background.telemetry import DrugBackgroundTelemetry
from app.services.drug_safety.validation_service import MedicationValidationService

logger = logging.getLogger("nura.drug_background.worker")

HEARTBEAT_INTERVAL_SECONDS = 10
POLL_INTERVAL_SECONDS = 2

class BackgroundWorker:
    """
    Async worker that claims patient validation tasks, processes them, and records heartbeats.
    """

    def __init__(
        self,
        worker_id: str,
        queue_manager: DrugQueueManager,
        validation_service: MedicationValidationService,
        telemetry: DrugBackgroundTelemetry,
        shutdown_event: asyncio.Event,
        db=None,
    ):
        self.worker_id = worker_id
        self.queue_manager = queue_manager
        self.validation_service = validation_service
        self.telemetry = telemetry
        self.shutdown_event = shutdown_event
        self.db = db
        self._current_job_id: Optional[str] = None
        self._is_active: bool = False

    @property
    def is_active(self) -> bool:
        return self._is_active

    async def run(self) -> None:
        """Main loop that retrieves queued tasks and processes them."""
        logger.info(f"Background worker {self.worker_id} started")
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        try:
            while not self.shutdown_event.is_set():
                job = await self.queue_manager.dequeue(self.worker_id)

                if job is None:
                    self._is_active = False
                    await asyncio.sleep(POLL_INTERVAL_SECONDS)
                    continue

                self._is_active = True
                job_id = str(job["_id"])
                patient_id = job["patient_id"]
                enqueued_at = job.get("created_at")

                if enqueued_at:
                    wait_ms = (datetime.now(timezone.utc) - enqueued_at.replace(tzinfo=timezone.utc)).total_seconds() * 1000
                    self.telemetry.record_queue_wait(wait_ms)

                logger.info(f"Worker {self.worker_id} starting validation check for patient {patient_id} (job {job_id})")
                self._current_job_id = job_id
                start_exec = time.perf_counter()

                try:
                    # Execute patient memory validation update
                    result = await self.validation_service.validate_and_update_patient_memory(patient_id)

                    if result is not None:
                        await self.queue_manager.mark_completed(job_id)
                        exec_latency_ms = (time.perf_counter() - start_exec) * 1000.0
                        self.telemetry.record_completion(exec_latency_ms)
                        logger.info(f"Worker {self.worker_id} completed validation for patient {patient_id}")
                    else:
                        error_msg = "Validation service returned empty result summary"
                        await self.queue_manager.mark_failed(job_id, error_msg)
                        self.telemetry.record_failure(error_msg)
                        logger.warning(f"Worker {self.worker_id} validation returned empty results for patient {patient_id}")

                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Worker {self.worker_id} unhandled validation error for patient {patient_id}: {error_msg}", exc_info=True)
                    await self.queue_manager.mark_failed(job_id, error_msg)
                    self.telemetry.record_failure(error_msg)
                finally:
                    self._current_job_id = None
                    self._is_active = False

        finally:
            heartbeat_task.cancel()
            logger.info(f"Worker {self.worker_id} shut down cleanly")

    async def _heartbeat_loop(self) -> None:
        """Periodically records worker heartbeat status in MongoDB."""
        while not self.shutdown_event.is_set():
            try:
                if self.db is not None:
                    await self.db["drug_worker_heartbeats"].update_one(
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
                logger.warning(f"Heartbeat registration failed for worker {self.worker_id}: {e}")
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
