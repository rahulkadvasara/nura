"""
Nura - Clinical Report Synchronization Telemetry Metrics
"""

import threading
from typing import Dict, Any


class ReportSyncTelemetry:
    """Thread-safe statistics collector for report synchronization pipeline executions"""

    def __init__(self):
        self._lock = threading.Lock()
        self._total_syncs = 0
        self._successful_syncs = 0
        self._failed_syncs = 0
        self._accumulated_chunks = 0
        self._accumulated_upserts = 0
        self._accumulated_latency_ms = 0.0
        self._duplicate_chunks_prevented = 0

    def record_sync_run(
        self,
        latency_ms: float,
        chunks_count: int,
        upserted_count: int,
        success: bool
    ):
        with self._lock:
            self._total_syncs += 1
            if success:
                self._successful_syncs += 1
            else:
                self._failed_syncs += 1
            self._accumulated_chunks += chunks_count
            self._accumulated_upserts += upserted_count
            self._accumulated_latency_ms += latency_ms
            
            # Duplicates prevented is chunks calculated minus actually upserted
            prevented = chunks_count - upserted_count
            if prevented > 0:
                self._duplicate_chunks_prevented += prevented

    def record_duplicate_prevented(self, count: int = 1):
        with self._lock:
            self._duplicate_chunks_prevented += count

    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            avg_latency = 0.0
            if self._total_syncs > 0:
                avg_latency = self._accumulated_latency_ms / self._total_syncs

            success_rate = 1.0
            if self._total_syncs > 0:
                success_rate = self._successful_syncs / self._total_syncs

            return {
                "total_syncs": self._total_syncs,
                "successful_syncs": self._successful_syncs,
                "failed_syncs": self._failed_syncs,
                "success_rate": success_rate,
                "accumulated_chunks": self._accumulated_chunks,
                "accumulated_upserts": self._accumulated_upserts,
                "duplicate_chunks_prevented": self._duplicate_chunks_prevented,
                "average_latency_ms": round(avg_latency, 2)
            }


# Thread-safe global singleton
_telemetry_instance = ReportSyncTelemetry()


def get_report_sync_telemetry() -> ReportSyncTelemetry:
    """Access the global singleton report sync telemetry metrics instance"""
    return _telemetry_instance
