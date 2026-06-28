from datetime import datetime, timezone
from app.events.base import BaseEvent


class PipelineStageCompletedEvent(BaseEvent):
    """Event triggered when a single pipeline stage finishes successfully"""
    def __init__(self, report_id: str, patient_id: str, stage: str, status: str):
        super().__init__(
            event_type="PipelineStageCompleted",
            payload={
                "report_id": report_id,
                "patient_id": patient_id,
                "stage": stage,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


class PipelineFailedEvent(BaseEvent):
    """Event triggered when a pipeline execution fails at any stage"""
    def __init__(self, report_id: str, patient_id: str, stage: str, error_message: str):
        super().__init__(
            event_type="PipelineFailed",
            payload={
                "report_id": report_id,
                "patient_id": patient_id,
                "failed_stage": stage,
                "error_message": error_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


class PipelineCompletedEvent(BaseEvent):
    """Event triggered when the entire pipeline reaches READY or PARTIAL_SUCCESS state"""
    def __init__(self, report_id: str, patient_id: str, status: str):
        super().__init__(
            event_type="PipelineCompleted",
            payload={
                "report_id": report_id,
                "patient_id": patient_id,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
