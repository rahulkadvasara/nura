"""
Nura - Memory Telemetry Tracker
Handles thread-safe tracking of memory syncs, scores, and latencies
"""

import threading
from typing import Dict, Any


class MemoryTelemetryTracker:
    """Thread-safe statistics logger for chat memory and synchronization metrics"""

    def __init__(self):
        self._lock = threading.Lock()
        self.evaluations_count = 0
        self.stored_count = 0
        self.skipped_count = 0
        self.patient_memory_updates = 0
        self.qdrant_updates = 0
        self.total_evaluation_latency = 0.0
        self.total_summary_latency = 0.0
        self.evaluation_latencies_count = 0
        self.summary_latencies_count = 0
        
        # Buckets for memory scores: 0-0.2, 0.2-0.4, 0.4-0.6, 0.6-0.8, 0.8-1.0
        self.score_distribution = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0
        }
        
        # Accumulating total scores to calculate average
        self.total_memory_score = 0.0
        self.total_semantic_score = 0.0
        self.total_clinical_score = 0.0

    def record_evaluation(
        self,
        memory_score: float,
        semantic_score: float,
        clinical_score: float,
        stored: bool,
        patient_update: bool
    ):
        """Records score outputs and updates storage/skip metrics"""
        with self._lock:
            self.evaluations_count += 1
            if stored or patient_update:
                self.stored_count += 1
            else:
                self.skipped_count += 1

            self.total_memory_score += memory_score
            self.total_semantic_score += semantic_score
            self.total_clinical_score += clinical_score

            # Place memory score in bucket
            if memory_score <= 0.2:
                self.score_distribution["0.0-0.2"] += 1
            elif memory_score <= 0.4:
                self.score_distribution["0.2-0.4"] += 1
            elif memory_score <= 0.6:
                self.score_distribution["0.4-0.6"] += 1
            elif memory_score <= 0.8:
                self.score_distribution["0.6-0.8"] += 1
            else:
                self.score_distribution["0.8-1.0"] += 1

    def record_latencies(self, eval_lat: float = 0.0, sum_lat: float = 0.0):
        """Records latency measurements for background evaluations and LLM summary builds"""
        with self._lock:
            if eval_lat > 0.0:
                self.total_evaluation_latency += eval_lat
                self.evaluation_latencies_count += 1
            if sum_lat > 0.0:
                self.total_summary_latency += sum_lat
                self.summary_latencies_count += 1

    def record_qdrant_update(self):
        """Increments point upsert counters for Qdrant collection"""
        with self._lock:
            self.qdrant_updates += 1

    def record_patient_memory_update(self):
        """Increments structured document update counters for MongoDB"""
        with self._lock:
            self.patient_memory_updates += 1

    def get_statistics(self) -> Dict[str, Any]:
        """Calculates current average values and returns telemetry payload"""
        with self._lock:
            avg_eval_lat = (self.total_evaluation_latency / self.evaluation_latencies_count) if self.evaluation_latencies_count > 0 else 0.0
            avg_sum_lat = (self.total_summary_latency / self.summary_latencies_count) if self.summary_latencies_count > 0 else 0.0
            
            avg_mem = (self.total_memory_score / self.evaluations_count) if self.evaluations_count > 0 else 0.0
            avg_sem = (self.total_semantic_score / self.evaluations_count) if self.evaluations_count > 0 else 0.0
            avg_clin = (self.total_clinical_score / self.evaluations_count) if self.evaluations_count > 0 else 0.0

            return {
                "evaluations_count": self.evaluations_count,
                "stored_count": self.stored_count,
                "skipped_count": self.skipped_count,
                "patient_memory_updates": self.patient_memory_updates,
                "qdrant_updates": self.qdrant_updates,
                "average_evaluation_latency": round(avg_eval_lat, 2),
                "average_summary_latency": round(avg_sum_lat, 2),
                "memory_score_distribution": self.score_distribution.copy(),
                "avg_scores": {
                    "memory_score": round(avg_mem, 2),
                    "semantic_score": round(avg_sem, 2),
                    "clinical_score": round(avg_clin, 2)
                }
            }

    def reset(self):
        """Resets all metrics counters to zero"""
        with self._lock:
            self.evaluations_count = 0
            self.stored_count = 0
            self.skipped_count = 0
            self.patient_memory_updates = 0
            self.qdrant_updates = 0
            self.total_evaluation_latency = 0.0
            self.total_summary_latency = 0.0
            self.evaluation_latencies_count = 0
            self.summary_latencies_count = 0
            self.total_memory_score = 0.0
            self.total_semantic_score = 0.0
            self.total_clinical_score = 0.0
            for k in self.score_distribution:
                self.score_distribution[k] = 0


# Singleton global instance
memory_telemetry = MemoryTelemetryTracker()
