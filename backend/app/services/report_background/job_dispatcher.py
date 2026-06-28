"""
Nura - Job Dispatcher
Creates queue jobs and dispatches them — wraps PipelineService, supports batch dispatch.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from app.services.report_background.queue_manager import ReportQueueManager, JobPriority
from app.services.report_background.progress_tracker import ReportProgressTracker

logger = logging.getLogger("nura.report_background.dispatcher")


class JobDispatcher:
    """
    Responsible for creating and submitting processing jobs into the queue.
    Wraps PipelineService — does NOT duplicate processing logic.
    Supports single-report and batch dispatch.
    """

    def __init__(
        self,
        queue_manager: ReportQueueManager,
        progress_tracker: ReportProgressTracker,
    ):
        self.queue_manager = queue_manager
        self.progress_tracker = progress_tracker

    async def dispatch(
        self,
        report_id: str,
        patient_id: str,
        priority: JobPriority = JobPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Enqueue a single report processing job.
        Returns the job ID.
        """
        # Initialize progress tracking
        await self.progress_tracker.set_stage(report_id, "uploaded")

        job_id = await self.queue_manager.enqueue(
            report_id=report_id,
            patient_id=patient_id,
            priority=priority,
            metadata=metadata,
        )
        logger.info(f"Dispatched job {job_id} for report {report_id} (priority={priority})")
        return job_id

    async def dispatch_batch(
        self,
        reports: List[Dict[str, str]],
        priority: JobPriority = JobPriority.NORMAL,
    ) -> List[Dict[str, str]]:
        """
        Dispatch multiple reports as individual jobs.
        `reports` should be a list of dicts with `report_id` and `patient_id`.
        Returns a list of {report_id, job_id} mappings.
        """
        results = []
        for item in reports:
            try:
                job_id = await self.dispatch(
                    report_id=item["report_id"],
                    patient_id=item["patient_id"],
                    priority=priority,
                    metadata={"batch": True, "batch_size": len(reports)},
                )
                results.append({"report_id": item["report_id"], "job_id": job_id, "success": True})
            except Exception as e:
                logger.error(f"Failed to dispatch batch job for report {item.get('report_id')}: {e}")
                results.append({"report_id": item.get("report_id"), "job_id": None, "success": False, "error": str(e)})
        return results
