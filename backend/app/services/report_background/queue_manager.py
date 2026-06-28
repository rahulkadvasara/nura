"""
Nura - Report Queue Manager
MongoDB-backed priority job queue with dead-letter queue support.
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nura.report_background.queue")


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


class ReportQueueManager:
    """
    Production queue manager backed by MongoDB `report_jobs` collection.
    Supports priority ordering, status lifecycle, and dead-letter queue (DLQ).
    """

    COLLECTION = "report_jobs"
    MAX_RETRIES = 3

    def __init__(self, db):
        self.db = db

    @property
    def collection(self):
        return self.db[self.COLLECTION]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def enqueue(
        self,
        report_id: str,
        patient_id: str,
        priority: JobPriority = JobPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new job record and add it to the queue. Returns the job document ID."""
        now = datetime.now(timezone.utc)
        job = {
            "report_id": report_id,
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
        logger.info(f"Enqueued job {job_id} for report {report_id} (priority={priority})")
        return job_id

    async def dequeue(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """
        Atomically claim the highest-priority queued job for the given worker.
        Returns the job document, or None if queue is empty.
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
            logger.info(f"Worker {worker_id} claimed job for report {job.get('report_id')}")
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
        logger.info(f"Job {job_id} marked as COMPLETED")

    async def mark_failed(self, job_id: str, error: str) -> None:
        """
        Record a failure for the job. If retries are exhausted, moves to DLQ.
        Otherwise, re-queues with incremented retry count.
        """
        from bson import ObjectId
        now = datetime.now(timezone.utc)
        job = await self.collection.find_one({"_id": ObjectId(job_id)})
        if not job:
            return

        retry_count = job.get("retry_count", 0) + 1
        max_retries = job.get("max_retries", self.MAX_RETRIES)

        if retry_count >= max_retries:
            # Move to dead-letter queue
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
            logger.error(f"Job {job_id} moved to DEAD LETTER QUEUE after {retry_count} failures")
        else:
            # Re-queue with exponential backoff noted in metadata
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
            logger.warning(f"Job {job_id} re-queued (retry {retry_count}/{max_retries})")

    async def cancel(self, report_id: str) -> bool:
        """Cancel a pending or queued job for the given report. Returns True if cancelled."""
        result = await self.collection.update_one(
            {"report_id": report_id, "status": {"$in": [JobStatus.PENDING, JobStatus.QUEUED]}},
            {"$set": {"status": JobStatus.CANCELLED, "updated_at": datetime.now(timezone.utc)}},
        )
        cancelled = result.modified_count > 0
        if cancelled:
            logger.info(f"Cancelled queued job for report {report_id}")
        return cancelled

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Return queue depth counts per status."""
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
        """Return most recent failed / DLQ jobs with their error logs."""
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
        """Re-queue jobs stuck in PROCESSING state (worker crashed). Returns count recovered."""
        from datetime import timedelta
        stale_threshold = datetime.now(timezone.utc) - timedelta(minutes=30)
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
            logger.warning(f"Recovered {result.modified_count} stale PROCESSING jobs back to QUEUED")
        return result.modified_count
