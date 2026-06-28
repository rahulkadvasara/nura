"""
Nura - Report Progress Tracker
Tracks per-report processing stage percentage, backed by MongoDB.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("nura.report_background.progress")

# Stage name → cumulative completion percentage weight
STAGE_WEIGHTS = {
    "uploaded": 5,
    "ocr": 30,
    "extraction": 50,
    "risk": 65,
    "summary": 85,
    "sync": 95,
    "completed": 100,
}

STAGE_LABELS = {
    "uploaded": "Uploading",
    "ocr": "OCR Scan",
    "extraction": "Clinical Extraction",
    "risk": "Risk Analysis",
    "summary": "AI Summary",
    "sync": "Synchronization",
    "completed": "Complete",
    "failed": "Failed",
}


class ReportProgressTracker:
    """
    Real-time per-report progress tracking backed by MongoDB `report_progress` collection.
    Stores stage + percentage for each active report — polled by the frontend every few seconds.
    """

    COLLECTION = "report_progress"

    def __init__(self, db):
        self.db = db

    @property
    def collection(self):
        return self.db[self.COLLECTION]

    async def set_stage(self, report_id: str, stage: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Record the current active pipeline stage and compute completion percentage."""
        percentage = STAGE_WEIGHTS.get(stage, 0)
        label = STAGE_LABELS.get(stage, stage.title())
        now = datetime.now(timezone.utc)

        await self.collection.update_one(
            {"report_id": report_id},
            {
                "$set": {
                    "report_id": report_id,
                    "stage": stage,
                    "stage_label": label,
                    "percentage": percentage,
                    "updated_at": now,
                    **(extra or {}),
                }
            },
            upsert=True,
        )

    async def get_progress(self, report_id: str) -> Dict[str, Any]:
        """Return current stage, label, and percentage for a report."""
        doc = await self.collection.find_one({"report_id": report_id})
        if not doc:
            return {
                "report_id": report_id,
                "stage": "uploaded",
                "stage_label": "Uploading",
                "percentage": 5,
                "updated_at": None,
            }
        doc.pop("_id", None)
        return doc

    async def mark_completed(self, report_id: str) -> None:
        """Mark report progress as 100% completed."""
        await self.set_stage(report_id, "completed")

    async def mark_failed(self, report_id: str, error: str) -> None:
        """Mark report progress as failed with error message."""
        await self.collection.update_one(
            {"report_id": report_id},
            {
                "$set": {
                    "report_id": report_id,
                    "stage": "failed",
                    "stage_label": "Failed",
                    "percentage": 0,
                    "error": error,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )

    async def cleanup(self, report_id: str) -> None:
        """Remove progress tracking record for a report (e.g. after deletion)."""
        await self.collection.delete_one({"report_id": report_id})
