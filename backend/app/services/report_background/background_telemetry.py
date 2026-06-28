"""
Nura - Background Telemetry Service
Tracks queue depth, worker utilization, cache hit ratios, and processing throughput.
"""

import time
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger("nura.report_background.telemetry")


class BackgroundTelemetry:
    """
    In-memory telemetry collector for the background processing system.
    Tracks queue depth, worker utilization, cache hit ratios, and throughput.
    A rolling 1-hour window is maintained for failure and throughput calculations.
    """

    WINDOW_SECONDS = 3600  # 1 hour rolling window

    def __init__(self):
        # Worker tracking
        self._total_workers: int = 0
        self._active_workers: int = 0

        # Throughput tracking — stores completion timestamps
        self._completions: deque = deque()  # (timestamp,)
        self._failures: deque = deque()     # (timestamp, error)

        # Queue wait times
        self._queue_wait_times: deque = deque()  # (wait_ms,)

        # Cache hit/miss counters
        self._cache_stats: Dict[str, Dict[str, int]] = {
            "ocr": {"hits": 0, "misses": 0},
            "embedding": {"hits": 0, "misses": 0},
            "summary": {"hits": 0, "misses": 0},
        }

        # Page stats
        self._total_pages_processed: int = 0
        self._total_reports_processed: int = 0

    # ------------------------------------------------------------------
    # Worker state
    # ------------------------------------------------------------------

    def set_worker_counts(self, total: int, active: int) -> None:
        self._total_workers = total
        self._active_workers = active

    def worker_utilization(self) -> float:
        """Return worker utilization percentage (0-100)."""
        if self._total_workers == 0:
            return 0.0
        return round((self._active_workers / self._total_workers) * 100, 1)

    # ------------------------------------------------------------------
    # Queue wait time
    # ------------------------------------------------------------------

    def record_queue_wait(self, wait_ms: float) -> None:
        """Record the time a job spent waiting in the queue before being picked up."""
        self._queue_wait_times.append(wait_ms)
        if len(self._queue_wait_times) > 1000:
            self._queue_wait_times.popleft()

    def avg_queue_wait_ms(self) -> float:
        if not self._queue_wait_times:
            return 0.0
        return round(sum(self._queue_wait_times) / len(self._queue_wait_times), 1)

    # ------------------------------------------------------------------
    # Throughput
    # ------------------------------------------------------------------

    def record_completion(self, pages: int = 0) -> None:
        """Record a successfully completed report."""
        now = time.time()
        self._completions.append(now)
        self._total_reports_processed += 1
        self._total_pages_processed += pages
        self._prune_window()

    def record_failure(self, error: str) -> None:
        """Record a pipeline failure."""
        now = time.time()
        self._failures.append((now, error))
        self._prune_window()

    def reports_per_hour(self) -> float:
        """Reports completed in the last rolling hour."""
        self._prune_window()
        return float(len(self._completions))

    def failure_rate(self) -> float:
        """Failure rate in last hour as a percentage."""
        self._prune_window()
        total = len(self._completions) + len(self._failures)
        if total == 0:
            return 0.0
        return round(len(self._failures) / total * 100, 1)

    def avg_pages_per_report(self) -> float:
        if self._total_reports_processed == 0:
            return 0.0
        return round(self._total_pages_processed / self._total_reports_processed, 1)

    # ------------------------------------------------------------------
    # Cache tracking
    # ------------------------------------------------------------------

    def record_cache_hit(self, cache_type: str) -> None:
        """Record a cache hit for the given type (ocr, embedding, summary)."""
        if cache_type in self._cache_stats:
            self._cache_stats[cache_type]["hits"] += 1

    def record_cache_miss(self, cache_type: str) -> None:
        """Record a cache miss for the given type."""
        if cache_type in self._cache_stats:
            self._cache_stats[cache_type]["misses"] += 1

    def cache_hit_ratio(self, cache_type: str) -> float:
        """Return cache hit ratio for the given type (0.0 – 1.0)."""
        stats = self._cache_stats.get(cache_type, {})
        total = stats.get("hits", 0) + stats.get("misses", 0)
        if total == 0:
            return 0.0
        return round(stats["hits"] / total, 3)

    # ------------------------------------------------------------------
    # Stats snapshot
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return a full statistics snapshot."""
        self._prune_window()
        return {
            "workers": {
                "total": self._total_workers,
                "active": self._active_workers,
                "idle": self._total_workers - self._active_workers,
                "utilization_percent": self.worker_utilization(),
            },
            "throughput": {
                "reports_per_hour": self.reports_per_hour(),
                "total_reports_processed": self._total_reports_processed,
                "failure_rate_percent": self.failure_rate(),
                "avg_pages_per_report": self.avg_pages_per_report(),
                "avg_queue_wait_ms": self.avg_queue_wait_ms(),
            },
            "cache": {
                "ocr": {
                    "hit_ratio": self.cache_hit_ratio("ocr"),
                    **self._cache_stats["ocr"],
                },
                "embedding": {
                    "hit_ratio": self.cache_hit_ratio("embedding"),
                    **self._cache_stats["embedding"],
                },
                "summary": {
                    "hit_ratio": self.cache_hit_ratio("summary"),
                    **self._cache_stats["summary"],
                },
            },
            "snapshot_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _prune_window(self) -> None:
        """Remove entries older than the rolling window from throughput queues."""
        cutoff = time.time() - self.WINDOW_SECONDS
        while self._completions and self._completions[0] < cutoff:
            self._completions.popleft()
        while self._failures and self._failures[0][0] < cutoff:
            self._failures.popleft()
