"""
Nura - Medical Extraction Telemetry
"""

import threading
from typing import Dict, Any


class ReportExtractionTelemetry:
    """Thread-safe statistics tracker for structured medical information extraction jobs"""

    def __init__(self):
        self._lock = threading.Lock()
        self.total_extractions = 0
        self.successful_extractions = 0
        self.failed_extractions = 0
        self.document_type_counts = {}
        self.total_extraction_confidence = 0.0
        self.total_duration_ms = 0.0

    def record_extraction(self, doc_type: str, confidence: float, duration_ms: float, success: bool) -> None:
        with self._lock:
            self.total_extractions += 1
            if success:
                self.successful_extractions += 1
                self.total_extraction_confidence += confidence
                self.total_duration_ms += duration_ms
                self.document_type_counts[doc_type] = self.document_type_counts.get(doc_type, 0) + 1
            else:
                self.failed_extractions += 1

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            avg_conf = self.total_extraction_confidence / max(1, self.successful_extractions)
            avg_dur = self.total_duration_ms / max(1, self.successful_extractions)
            return {
                "total_extractions": self.total_extractions,
                "successful_extractions": self.successful_extractions,
                "failed_extractions": self.failed_extractions,
                "average_extraction_confidence": avg_conf,
                "average_duration_ms": avg_dur,
                "document_classification_counts": dict(self.document_type_counts)
            }

    def reset(self) -> None:
        with self._lock:
            self.total_extractions = 0
            self.successful_extractions = 0
            self.failed_extractions = 0
            self.document_type_counts.clear()
            self.total_extraction_confidence = 0.0
            self.total_duration_ms = 0.0


# Singleton reference
_telemetry_instance = ReportExtractionTelemetry()


def get_report_extraction_telemetry() -> ReportExtractionTelemetry:
    """Retrieve singleton extraction telemetry instance"""
    return _telemetry_instance
