import time
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from bson import ObjectId

from app.models.report import ReportInDB, ProcessingStatus
from app.repositories.report_repository import ReportRepository
from app.services.report_pipeline.pipeline_state import PipelineState
from app.services.report_pipeline.pipeline_events import (
    PipelineStageCompletedEvent,
    PipelineFailedEvent,
    PipelineCompletedEvent
)
from app.services.report_pipeline.pipeline_telemetry import PipelineTelemetry
from app.services.report_pipeline.pipeline_validator import PipelineValidator

logger = logging.getLogger("nura.report_pipeline.service")


class PipelineService:
    """Report Processing Orchestrator Pipeline coordinating all medical document subsystems"""

    def __init__(
        self,
        report_repository: ReportRepository,
        document_parser,
        extraction_service,
        risk_service,
        understanding_service,
        sync_service,
        telemetry: PipelineTelemetry,
        validator: PipelineValidator,
        event_dispatcher=None,
        max_stage_retries: int = 3
    ):
        self.report_repository = report_repository
        self.document_parser = document_parser
        self.extraction_service = extraction_service
        self.risk_service = risk_service
        self.understanding_service = understanding_service
        self.sync_service = sync_service
        self.telemetry = telemetry
        self.validator = validator
        self.event_dispatcher = event_dispatcher
        self.max_stage_retries = max_stage_retries

    async def execute_pipeline(self, report_id: str, force_retry: bool = False) -> Dict[str, Any]:
        """Execute end-to-end processing pipeline with stage retries, recovery, and telemetry tracking"""
        pipeline_start = time.time()
        
        # 1. Retrieve report
        report = await self.report_repository.get(report_id)
        if not report:
            raise ValueError(f"Report with ID {report_id} not found in database")

        # Skip if already completed and not forced
        if report.processing_status == ProcessingStatus.COMPLETED and not force_retry:
            if getattr(report, "pipeline_status", None) == PipelineState.READY:
                return {"success": True, "status": PipelineState.READY, "message": "Report already processed and READY"}

        logger.info(f"Starting processing pipeline for report {report_id} (force_retry={force_retry})")
        
        # Initial status update
        await self.report_repository.collection.update_one(
            {"_id": self.report_repository.collection.find_one({"_id": report_id}) or report_id if not isinstance(report_id, bytes) else report_id},
            {
                "$set": {
                    "pipeline_status": PipelineState.PROCESSING,
                    "pipeline_started_at": datetime.now(timezone.utc),
                    "pipeline_errors": [],
                    "pipeline_retries": getattr(report, "pipeline_retries", 0) + (1 if force_retry else 0)
                }
            }
        )

        stages = ["ocr", "extraction", "risk", "summary", "sync"]
        timings = {}
        stage_errors = []

        try:
            # ----------------------------------------------------
            # STAGE 1: OCR Processing
            # ----------------------------------------------------
            stage_start = time.time()
            ocr_status = getattr(report, "ocr_status", "pending")
            
            if ocr_status == "completed" and not force_retry:
                logger.info(f"Skipping OCR stage for {report_id} (already complete)")
                timings["ocr_duration_ms"] = getattr(report, "ocr_duration_ms", 0.0) or 0.0
            else:
                success = await self._run_stage_with_retries(
                    report_id, "ocr", self.document_parser.process_report, report_id
                )
                timings["ocr_duration_ms"] = (time.time() - stage_start) * 1000.0
                await self.telemetry.record_stage_duration(
                    report_id, "ocr", timings["ocr_duration_ms"], success
                )
                if not success:
                    raise RuntimeError("OCR Processing stage failed")

            await self._update_pipeline_status(report_id, PipelineState.OCR_COMPLETE)
            await self._dispatch_event(PipelineStageCompletedEvent(report_id, report.patient_id, "ocr", PipelineState.OCR_COMPLETE))

            # Fetch fresh report state
            report = await self.report_repository.get(report_id)

            # ----------------------------------------------------
            # STAGE 2: Clinical Extraction
            # ----------------------------------------------------
            stage_start = time.time()
            ext_status = getattr(report, "extraction_status", "pending")
            
            if ext_status == "completed" and not force_retry and report.laboratory_results:
                logger.info(f"Skipping Clinical Extraction stage for {report_id} (already complete)")
                timings["extraction_duration_ms"] = getattr(report, "extraction_duration_ms", 0.0) or 0.0
            else:
                success = await self._run_stage_with_retries(
                    report_id, "extraction", self.extraction_service.extract_medical_information, report_id
                )
                timings["extraction_duration_ms"] = (time.time() - stage_start) * 1000.0
                await self.telemetry.record_stage_duration(
                    report_id, "extraction", timings["extraction_duration_ms"], success
                )
                if not success:
                    raise RuntimeError("Clinical Extraction stage failed")

            await self._update_pipeline_status(report_id, PipelineState.EXTRACTION_COMPLETE)
            await self._dispatch_event(PipelineStageCompletedEvent(report_id, report.patient_id, "extraction", PipelineState.EXTRACTION_COMPLETE))

            # Fetch fresh report state
            report = await self.report_repository.get(report_id)

            # ----------------------------------------------------
            # STAGE 3: Clinical Risk Analysis
            # ----------------------------------------------------
            stage_start = time.time()
            risk_status = getattr(report, "overall_risk", None)
            
            if risk_status and not force_retry:
                logger.info(f"Skipping Clinical Risk stage for {report_id} (already complete)")
                timings["risk_duration_ms"] = getattr(report, "risk_duration_ms", 0.0) or 0.0
            else:
                success = await self._run_stage_with_retries(
                    report_id, "risk", self.risk_service.analyze_report_risks, report_id
                )
                timings["risk_duration_ms"] = (time.time() - stage_start) * 1000.0
                await self.telemetry.record_stage_duration(
                    report_id, "risk", timings["risk_duration_ms"], success
                )
                if not success:
                    raise RuntimeError("Clinical Risk analysis stage failed")

            await self._update_pipeline_status(report_id, PipelineState.RISK_COMPLETE)
            await self._dispatch_event(PipelineStageCompletedEvent(report_id, report.patient_id, "risk", PipelineState.RISK_COMPLETE))

            # Fetch fresh report state
            report = await self.report_repository.get(report_id)

            # ----------------------------------------------------
            # STAGE 4: AI Report Understanding
            # ----------------------------------------------------
            stage_start = time.time()
            sum_status = getattr(report, "ai_summary", None)
            
            if sum_status and not force_retry:
                logger.info(f"Skipping AI Summarization stage for {report_id} (already complete)")
                timings["summary_duration_ms"] = getattr(report, "summary_duration_ms", 0.0) or 0.0
            else:
                success = await self._run_stage_with_retries(
                    report_id, "summary", self.understanding_service.generate_report_summary, report_id
                )
                timings["summary_duration_ms"] = (time.time() - stage_start) * 1000.0
                await self.telemetry.record_stage_duration(
                    report_id, "summary", timings["summary_duration_ms"], success
                )
                if not success:
                    raise RuntimeError("AI Summarization stage failed")

            await self._update_pipeline_status(report_id, PipelineState.SUMMARY_COMPLETE)
            await self._dispatch_event(PipelineStageCompletedEvent(report_id, report.patient_id, "summary", PipelineState.SUMMARY_COMPLETE))

            # Fetch fresh report state
            report = await self.report_repository.get(report_id)

            # ----------------------------------------------------
            # STAGE 5: Knowledge Synchronization
            # ----------------------------------------------------
            stage_start = time.time()
            sync_status = getattr(report, "is_synchronized", False)
            
            if sync_status and not force_retry:
                logger.info(f"Skipping Knowledge Sync stage for {report_id} (already complete)")
                timings["sync_duration_ms"] = getattr(report, "sync_duration_ms", 0.0) or 0.0
            else:
                success = await self._run_stage_with_retries(
                    report_id, "sync", self.sync_service.synchronize_report, report_id
                )
                timings["sync_duration_ms"] = (time.time() - stage_start) * 1000.0
                await self.telemetry.record_stage_duration(
                    report_id, "sync", timings["sync_duration_ms"], success
                )
                if not success:
                    raise RuntimeError("Knowledge Synchronization stage failed")

            await self._update_pipeline_status(report_id, PipelineState.SYNC_COMPLETE)
            await self._dispatch_event(PipelineStageCompletedEvent(report_id, report.patient_id, "sync", PipelineState.SYNC_COMPLETE))

            # ----------------------------------------------------
            # Post-Execution Validator Validation
            # ----------------------------------------------------
            fresh_report = await self.report_repository.get(report_id)
            audit = await self.validator.validate_report_readiness(report_id)
            
            if audit["valid"]:
                # Transition status to READY
                total_duration_ms = (time.time() - pipeline_start) * 1000.0
                await self.report_repository.collection.update_one(
                    {"_id": self.report_repository.collection.find_one({"_id": report_id}) or report_id if not isinstance(report_id, bytes) else report_id},
                    {
                        "$set": {
                            "pipeline_status": PipelineState.READY,
                            "processing_status": ProcessingStatus.COMPLETED,
                            "pipeline_completed_at": datetime.now(timezone.utc),
                            "pipeline_duration_ms": total_duration_ms,
                            **timings
                        }
                    }
                )
                await self.telemetry.record_stage_duration(
                    report_id, "pipeline", total_duration_ms, True
                )
                await self._dispatch_event(PipelineCompletedEvent(report_id, report.patient_id, PipelineState.READY))
                
                return {
                    "success": True,
                    "status": PipelineState.READY,
                    "timings": timings,
                    "validation": audit
                }
            else:
                # Transition status to PARTIAL_SUCCESS or FAILED based on validator issues
                logger.warning(f"Report validation audit failed for {report_id}: {audit['issues']}")
                await self.report_repository.collection.update_one(
                    {"_id": self.report_repository.collection.find_one({"_id": report_id}) or report_id if not isinstance(report_id, bytes) else report_id},
                    {
                        "$set": {
                            "pipeline_status": PipelineState.PARTIAL_SUCCESS,
                            "pipeline_errors": audit["issues"],
                            "pipeline_completed_at": datetime.now(timezone.utc)
                        }
                    }
                )
                return {
                    "success": False,
                    "status": PipelineState.PARTIAL_SUCCESS,
                    "timings": timings,
                    "validation": audit
                }

        except Exception as exc:
            logger.error(f"Processing pipeline execution halted for {report_id}: {exc}", exc_info=True)
            err_msg = str(exc)
            
            # Transition status to FAILED
            await self.report_repository.collection.update_one(
                {"_id": self.report_repository.collection.find_one({"_id": report_id}) or report_id if not isinstance(report_id, bytes) else report_id},
                {
                    "$set": {
                        "pipeline_status": PipelineState.FAILED,
                        "processing_status": ProcessingStatus.FAILED,
                        "pipeline_completed_at": datetime.now(timezone.utc)
                    },
                    "$push": {
                        "pipeline_errors": err_msg
                    }
                }
            )
            await self.telemetry.record_stage_duration(
                report_id, "pipeline", (time.time() - pipeline_start) * 1000.0, False, err_msg
            )
            await self._dispatch_event(PipelineFailedEvent(report_id, report.patient_id, "pipeline", err_msg))
            
            return {
                "success": False,
                "status": PipelineState.FAILED,
                "error": err_msg,
                "timings": timings
            }

    async def _run_stage_with_retries(self, report_id: str, stage_name: str, stage_func, *args) -> bool:
        """Helper to invoke a stage service with exponential backoff retries"""
        retries = 0
        while retries < self.max_stage_retries:
            try:
                logger.info(f"Invoking pipeline stage '{stage_name}' (Attempt {retries + 1}/{self.max_stage_retries})")
                await stage_func(*args)
                return True
            except Exception as e:
                retries += 1
                logger.warning(f"Pipeline stage '{stage_name}' failed at attempt {retries}: {e}")
                await self.telemetry.record_retry(report_id, stage_name, retries)
                if retries < self.max_stage_retries:
                    # Short backoff
                    await asyncio.sleep(1.0 * (2 ** (retries - 1)))
        return False

    async def _update_pipeline_status(self, report_id: str, status: PipelineState) -> None:
        """Update report pipeline status key in MongoDB"""
        try:
            await self.report_repository.collection.update_one(
                {"_id": self.report_repository.collection.find_one({"_id": report_id}) or report_id if not isinstance(report_id, bytes) else report_id},
                {"$set": {"pipeline_status": status}}
            )
        except Exception as e:
            logger.error(f"Failed to update report pipeline status to {status}: {e}")

    async def _dispatch_event(self, event) -> None:
        """Trigger event notification via dispatcher if configured"""
        if self.event_dispatcher:
            try:
                await self.event_dispatcher.dispatch(event)
            except Exception as e:
                logger.error(f"Event dispatch error inside pipeline orchestrator: {e}")
