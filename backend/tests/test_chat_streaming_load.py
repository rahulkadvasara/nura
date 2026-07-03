import pytest
from app.services.chat.telemetry_service import ExtendedTelemetryTracker


def test_streaming_telemetry_counters():
    tracker = ExtendedTelemetryTracker()
    
    tracker.record_stream("start")
    tracker.record_stream("start")
    
    stats = tracker.get_stats()
    assert stats["streaming"]["started"] == 2
    assert stats["streaming"]["completed"] == 0

    tracker.record_stream("complete", duration_ms=500.0)
    tracker.record_stream("fail")
    tracker.record_stream("cancel")

    stats = tracker.get_stats()
    assert stats["streaming"]["completed"] == 1
    assert stats["streaming"]["failed"] == 1
    assert stats["streaming"]["cancelled"] == 1
    assert stats["performance"]["average_streaming_latency_ms"] == 500.0
