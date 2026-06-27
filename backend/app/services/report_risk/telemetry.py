"""
Nura - Clinical Risk Telemetry
"""

import threading
from typing import Dict, Any


class ReportRiskTelemetry:
    """Thread-safe statistics tracker for clinical risk analysis pipeline runs"""

    def __init__(self):
        self._lock = threading.Lock()
        self.total_analyses = 0
        self.successful_analyses = 0
        self.failed_analyses = 0
        self.severity_counts = {
            "NORMAL": 0,
            "LOW": 0,
            "MEDIUM": 0,
            "HIGH": 0,
            "CRITICAL": 0
        }
        self.flag_counts = {}
        self.recommendation_type_counts = {}

    def record_analysis(self, severity: str, flags: list, recommendations: list, success: bool) -> None:
        with self._lock:
            self.total_analyses += 1
            if success:
                self.successful_analyses += 1
                sev = severity.upper()
                if sev in self.severity_counts:
                    self.severity_counts[sev] += 1
                else:
                    self.severity_counts[sev] = self.severity_counts.get(sev, 0) + 1

                for flg in flags:
                    self.flag_counts[flg] = self.flag_counts.get(flg, 0) + 1

                for rec in recommendations:
                    t = rec.get("recommendation_type")
                    if t:
                        self.recommendation_type_counts[t] = self.recommendation_type_counts.get(t, 0) + 1
            else:
                self.failed_analyses += 1

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_analyses": self.total_analyses,
                "successful_analyses": self.successful_analyses,
                "failed_analyses": self.failed_analyses,
                "severity_distribution": dict(self.severity_counts),
                "clinical_flags_triggered": dict(self.flag_counts),
                "recommendation_metrics": dict(self.recommendation_type_counts)
            }

    def reset(self) -> None:
        with self._lock:
            self.total_analyses = 0
            self.successful_analyses = 0
            self.failed_analyses = 0
            self.severity_counts = {
                "NORMAL": 0,
                "LOW": 0,
                "MEDIUM": 0,
                "HIGH": 0,
                "CRITICAL": 0
            }
            self.flag_counts.clear()
            self.recommendation_type_counts.clear()


# Singleton reference
_telemetry_instance = ReportRiskTelemetry()


def get_report_risk_telemetry() -> ReportRiskTelemetry:
    """Retrieve singleton clinical risk telemetry instance"""
    return _telemetry_instance
