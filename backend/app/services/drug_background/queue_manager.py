import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nura.drug_background.queue")

class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DEAD_LETTER = "dead_letter"

class JobPriority(str, Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

PRIORITY_ORDER = {JobPriority.HIGH: 0, JobPriority.NORMAL: 1, JobPriority.LOW: 2}

class DrugQueueManager:
    """
    MongoDB-backed job queue for Drug Safety background validations.
    Features:
    - Target Collection: `drug_jobs`
    - Supported Statuses: pending, queued, processing, completed, failed, cancelled, dead_letter
    - Priority-based scheduling (high, normal, low)
    - Automatic de-duplication of active tasks per patient
    """

    COLLECTION = "drug_jobs"
    MAX_RETRIES = 3

    def __init__(self, db):
        self.db = db

    @property
    def collection(self):
        return self.db[self.COLLECTION]

    async def enqueue(
        self,
        patient_id: str,
        priority: JobPriority = JobPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Enqueue a background validation job.
        If a job is already queued or processing for the patient, returns the existing job ID.
        """
        # De-duplication check
        existing = await self.collection.find_one({
            "patient_id": patient_id,
            "status": {"$in": [JobStatus.QUEUED, JobStatus.PROCESSING]}
        })
        if existing:
            job_id = str(existing["_id"])
            logger.info(f"Duplicate job check: patient {patient_id} has active job {job_id}. Skipping enqueue.")
            return job_id

        now = datetime.now(timezone.utc)
        job = {
            "patient_id": patient_id,
            "status": JobStatus.QUEUED,
            "priority": priority,
            "priority_order": PRIORITY_ORDER[priority],
            "retry_count": 0,
            "max_retries": self.MAX_RETRIES,
            "errors": [],
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now,
            "started_at": None,
            "completed_at": None,
            "worker_id": None,
        }
        result = await self.collection.insert_one(job)
        job_id = str(result.inserted_id)
        logger.info(f"Enqueued background drug validation job {job_id} for patient {patient_id} (priority={priority})")
        return job_id

    async def dequeue(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """
        Atomically claim the highest-priority queued job.
        """
        now = datetime.now(timezone.utc)
        job = await self.collection.find_one_and_update(
            {"status": JobStatus.QUEUED},
            {
                "$set": {
                    "status": JobStatus.PROCESSING,
                    "worker_id": worker_id,
                    "started_at": now,
                    "updated_at": now,
                }
            },
            sort=[("priority_order", 1), ("created_at", 1)],
            return_document=True,
        )
        if job:
            logger.info(f"Worker {worker_id} claimed validation job for patient {job.get('patient_id')}")
        return job

    async def mark_completed(self, job_id: str) -> None:
        """Mark a job as successfully completed."""
        from bson import ObjectId
        await self.collection.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "status": JobStatus.COMPLETED,
                    "completed_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        logger.info(f"Background job {job_id} completed successfully")

    async def mark_failed(self, job_id: str, error: str) -> None:
        """
        Fail job. Re-queues up to MAX_RETRIES.
        Moves to DLQ (DEAD_LETTER) if retries are exhausted.
        """
        from bson import ObjectId
        now = datetime.now(timezone.utc)
        job = await self.collection.find_one({"_id": ObjectId(job_id)})
        if not job:
            return

        retry_count = job.get("retry_count", 0) + 1
        max_retries = job.get("max_retries", self.MAX_RETRIES)

        if retry_count >= max_retries:
            await self.collection.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "status": JobStatus.DEAD_LETTER,
                        "retry_count": retry_count,
                        "updated_at": now,
                        "completed_at": now,
                    },
                    "$push": {"errors": error},
                },
            )
            logger.error(f"Background job {job_id} moved to DEAD_LETTER (DLQ) after {retry_count} failures")
        else:
            await self.collection.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "status": JobStatus.QUEUED,
                        "retry_count": retry_count,
                        "worker_id": None,
                        "updated_at": now,
                        "started_at": None,
                    },
                    "$push": {"errors": error},
                },
            )
            logger.warning(f"Background job {job_id} re-queued (retry {retry_count}/{max_retries})")

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Return counts per status in the drug background queue."""
        pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
        cursor = self.collection.aggregate(pipeline)
        stats: Dict[str, int] = {}
        async for doc in cursor:
            stats[doc["_id"]] = doc["count"]

        return {
            "pending": stats.get(JobStatus.PENDING, 0),
            "queued": stats.get(JobStatus.QUEUED, 0),
            "processing": stats.get(JobStatus.PROCESSING, 0),
            "completed": stats.get(JobStatus.COMPLETED, 0),
            "failed": stats.get(JobStatus.FAILED, 0),
            "cancelled": stats.get(JobStatus.CANCELLED, 0),
            "dead_letter": stats.get(JobStatus.DEAD_LETTER, 0),
            "total": sum(stats.values()),
        }

    async def get_recent_failures(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return recently failed or dead-lettered queue jobs."""
        cursor = self.collection.find(
            {"status": {"$in": [JobStatus.FAILED, JobStatus.DEAD_LETTER]}},
            sort=[("updated_at", -1)],
            limit=limit,
        )
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    async def recover_stale_processing_jobs(self) -> int:
        """Re-queue processing jobs stuck for longer than 15 minutes."""
        from datetime import timedelta
        stale_threshold = datetime.now(timezone.utc) - timedelta(minutes=15)
        result = await self.collection.update_many(
            {"status": JobStatus.PROCESSING, "started_at": {"$lt": stale_threshold}},
            {
                "$set": {
                    "status": JobStatus.QUEUED,
                    "worker_id": None,
                    "started_at": None,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        if result.modified_count:
            logger.warning(f"Recovered {result.modified_count} stale drug validation jobs back to QUEUED")
        return result.modified_count
