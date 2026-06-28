import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from app.db import get_database

logger = logging.getLogger("nura.report_pipeline.telemetry")


class PipelineTelemetry:
    """Thread-safe pipeline telemetry registry storing metrics and failures in MongoDB"""

    async def record_stage_duration(
        self,
        report_id: str,
        stage: str,
        duration_ms: float,
        success: bool,
        error_msg: str = None
    ) -> None:
        """Record stage execution outcome and duration"""
        try:
            db = get_database()
            record = {
                "report_id": report_id,
                "stage": stage.lower(),
                "duration_ms": duration_ms,
                "success": success,
                "error_message": error_msg,
                "timestamp": datetime.now(timezone.utc)
            }
            await db.pipeline_telemetry.insert_one(record)
        except Exception as e:
            logger.error(f"Failed to record pipeline telemetry: {e}")

    async def record_retry(self, report_id: str, stage: str, retry_count: int) -> None:
        """Record a pipeline retry attempt"""
        try:
            db = get_database()
            await db.pipeline_retries.insert_one({
                "report_id": report_id,
                "stage": stage.lower(),
                "retry_count": retry_count,
                "timestamp": datetime.now(timezone.utc)
            })
        except Exception as e:
            logger.error(f"Failed to record retry telemetry: {e}")

    async def get_statistics(self) -> Dict[str, Any]:
        """Fetch consolidated throughput, latency metrics, and error rates"""
        try:
            db = get_database()

            total_records = await db.pipeline_telemetry.count_documents({})
            failed_records = await db.pipeline_telemetry.count_documents({"success": False})

            stages = ["ocr", "extraction", "risk", "summary", "sync"]
            averages = {}

            for stage in stages:
                pipeline = [
                    {"$match": {"stage": stage, "success": True}},
                    {"$group": {"_id": None, "avg_dur": {"$avg": "$duration_ms"}}}
                ]
                cursor = db.pipeline_telemetry.aggregate(pipeline)
                result = await cursor.to_list(length=1)
                averages[f"avg_{stage}_ms"] = result[0]["avg_dur"] if result else 0.0

            err_pipeline = [
                {"$match": {"success": False, "error_message": {"$ne": None}}},
                {"$group": {"_id": "$error_message", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]
            err_cursor = db.pipeline_telemetry.aggregate(err_pipeline)
            common_errors = [{"error": r["_id"], "count": r["count"]} for r in await err_cursor.to_list(length=5)]

            total_reports = await db.reports.count_documents({})
            completed_reports = await db.reports.count_documents({"pipeline_status": "READY"})
            processing_reports = await db.reports.count_documents({"pipeline_status": {"$in": ["PROCESSING", "UPLOADED"]}})
            failed_reports = await db.reports.count_documents({"pipeline_status": "FAILED"})

            retries_count = await db.pipeline_retries.count_documents({})

            throughput = completed_reports
            failure_rate = (failed_records / max(1, total_records)) * 100

            # Compute overall pipeline duration
            overall_pipeline = [
                {"$match": {"stage": "pipeline", "success": True}},
                {"$group": {"_id": None, "avg_dur": {"$avg": "$duration_ms"}}}
            ]
            overall_cursor = db.pipeline_telemetry.aggregate(overall_pipeline)
            overall_result = await overall_cursor.to_list(length=1)
            avg_pipeline_ms = overall_result[0]["avg_dur"] if overall_result else 0.0

            return {
                "throughput": throughput,
                "total_processed": total_reports,
                "completed_count": completed_reports,
                "processing_count": processing_reports,
                "failed_count": failed_reports,
                "averages": averages,
                "avg_pipeline_duration_ms": avg_pipeline_ms,
                "failure_rate_percent": round(failure_rate, 2),
                "total_retries": retries_count,
                "common_errors": common_errors,
                "queue_depth": processing_reports,
                "health": "healthy" if failure_rate < 15 else "degraded"
            }
        except Exception as e:
            logger.error(f"Failed to fetch telemetry stats: {e}")
            return {
                "throughput": 0,
                "total_processed": 0,
                "completed_count": 0,
                "processing_count": 0,
                "failed_count": 0,
                "averages": {},
                "avg_pipeline_duration_ms": 0.0,
                "failure_rate_percent": 0.0,
                "total_retries": 0,
                "common_errors": [],
                "queue_depth": 0,
                "health": "unknown"
            }
