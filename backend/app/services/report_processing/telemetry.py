"""
Nura - Report Processing Telemetry
"""

import threading
from typing import Dict, Any


class ReportProcessingTelemetry:
    """Thread-safe statistics tracker for document upload and OCR processing pipelines"""

    def __init__(self):
        self._lock = threading.Lock()
        self.uploaded_documents = 0
        self.processed_pages = 0
        self.total_ocr_latency_ms = 0.0
        self.total_confidence = 0.0
        self.failures = 0
        self.retries = 0
        self.method_counts = {}
        self.total_processing_time_ms = 0.0

    def record_upload(self) -> None:
        with self._lock:
            self.uploaded_documents += 1

    def record_page(self, method: str, confidence: float, latency_ms: float) -> None:
        with self._lock:
            self.processed_pages += 1
            self.total_confidence += confidence
            self.total_ocr_latency_ms += latency_ms
            self.method_counts[method] = self.method_counts.get(method, 0) + 1

    def record_processing(self, duration_ms: float, success: bool) -> None:
        with self._lock:
            self.total_processing_time_ms += duration_ms
            if not success:
                self.failures += 1

    def record_retry(self) -> None:
        with self._lock:
            self.retries += 1

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            avg_conf = self.total_confidence / max(1, self.processed_pages)
            avg_ocr_lat = self.total_ocr_latency_ms / max(1, self.processed_pages)
            avg_proc_time = self.total_processing_time_ms / max(1, self.uploaded_documents)
            return {
                "uploaded_documents": self.uploaded_documents,
                "processed_pages": self.processed_pages,
                "ocr_latency_average_ms": avg_ocr_lat,
                "average_confidence": avg_conf,
                "failures": self.failures,
                "retries": self.retries,
                "extraction_methods": dict(self.method_counts),
                "average_processing_time_ms": avg_proc_time
            }

    def reset(self) -> None:
        with self._lock:
            self.uploaded_documents = 0
            self.processed_pages = 0
            self.total_ocr_latency_ms = 0.0
            self.total_confidence = 0.0
            self.failures = 0
            self.retries = 0
            self.method_counts.clear()
            self.total_processing_time_ms = 0.0


# Singleton instance
_telemetry_instance = ReportProcessingTelemetry()


def get_report_processing_telemetry() -> ReportProcessingTelemetry:
    """Retrieve singleton telemetry instance"""
    return _telemetry_instance
