import time
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("nura.drug_background.telemetry")

class DrugBackgroundTelemetry:
    """
    In-memory telemetry tracker for the Drug Safety background validation pipeline.
    Tracks worker activity, queue wait times, completed jobs, failed jobs, and execution durations.
    Uses rolling 1-hour window for metrics calculations.
    """

    WINDOW_SECONDS = 3600  # 1 hour rolling window

    def __init__(self):
        self._total_workers: int = 0
        self._active_workers: int = 0
        self._completions: deque = deque()          # (timestamp, duration_ms)
        self._failures: deque = deque()             # (timestamp, error_message)
        self._queue_wait_times: deque = deque()     # (wait_ms,)
        
        self._total_jobs_completed: int = 0
        self._total_jobs_failed: int = 0

    def set_worker_counts(self, total: int, active: int) -> None:
        self._total_workers = total
        self._active_workers = active

    def worker_utilization(self) -> float:
        if self._total_workers == 0:
            return 0.0
        return round((self._active_workers / self._total_workers) * 100, 1)

    def record_queue_wait(self, wait_ms: float) -> None:
        self._queue_wait_times.append(wait_ms)
        if len(self._queue_wait_times) > 1000:
            self._queue_wait_times.popleft()

    def avg_queue_wait_ms(self) -> float:
        if not self._queue_wait_times:
            return 0.0
        return round(sum(self._queue_wait_times) / len(self._queue_wait_times), 1)

    def record_completion(self, duration_ms: float) -> None:
        now = time.time()
        self._completions.append((now, duration_ms))
        self._total_jobs_completed += 1
        self._prune_window()

    def record_failure(self, error: str) -> None:
        now = time.time()
        self._failures.append((now, error))
        self._total_jobs_failed += 1
        self._prune_window()

    def jobs_completed_per_hour(self) -> float:
        self._prune_window()
        return float(len(self._completions))

    def failure_rate(self) -> float:
        self._prune_window()
        total = len(self._completions) + len(self._failures)
        if total == 0:
            return 0.0
        return round(len(self._failures) / total * 100, 1)

    def avg_execution_duration_ms(self) -> float:
        self._prune_window()
        if not self._completions:
            return 0.0
        durations = [item[1] for item in self._completions]
        return round(sum(durations) / len(durations), 1)

    def get_stats(self) -> Dict[str, Any]:
        self._prune_window()
        return {
            "workers": {
                "total": self._total_workers,
                "active": self._active_workers,
                "idle": max(0, self._total_workers - self._active_workers),
                "utilization_percent": self.worker_utilization(),
            },
            "throughput": {
                "jobs_completed_per_hour": self.jobs_completed_per_hour(),
                "total_completed": self._total_jobs_completed,
                "total_failed": self._total_jobs_failed,
                "failure_rate_percent": self.failure_rate(),
                "avg_queue_wait_ms": self.avg_queue_wait_ms(),
                "avg_execution_latency_ms": self.avg_execution_duration_ms(),
            },
            "snapshot_at": datetime.now(timezone.utc).isoformat(),
        }

    def reset(self) -> None:
        self._total_workers = 0
        self._active_workers = 0
        self._completions.clear()
        self._failures.clear()
        self._queue_wait_times.clear()
        self._total_jobs_completed = 0
        self._total_jobs_failed = 0

    def _prune_window(self) -> None:
        cutoff = time.time() - self.WINDOW_SECONDS
        while self._completions and self._completions[0][0] < cutoff:
            self._completions.popleft()
        while self._failures and self._failures[0][0] < cutoff:
            self._failures.popleft()


# Global Singleton Reference Background Telemetry
_drug_background_telemetry_instance: Optional[DrugBackgroundTelemetry] = None

def get_drug_background_telemetry() -> DrugBackgroundTelemetry:
    global _drug_background_telemetry_instance
    if _drug_background_telemetry_instance is None:
        _drug_background_telemetry_instance = DrugBackgroundTelemetry()
    return _drug_background_telemetry_instance
