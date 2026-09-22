"""Observability and testing suite for MCPserver.in.

Covers:
- Structured logging (JSON output, no sensitive payloads)
- Metrics collection and snapshots
- Health check endpoints (DB, Redis, services)
- Error tracking
- Observability middleware
"""

import json
import sys
import os
from datetime import datetime, timezone

# Add paths
sys.path.insert(0, "/Users/cyberteck/Downloads/MCP/MCP-SERVERS-master/app-mcpserver-in")
sys.path.insert(0, "/Users/cyberteck/Downloads/MCP/MCP-SERVERS-master/app-mcpserver-in/services")
sys.path.insert(0, "/Users/cyberteck/Downloads/MCP/MCP-SERVERS-master/app-mcpserver-in/services/observability")

from observability import (
    obs,
    record_request,
    record_tool_latency,
    record_model_latency,
    record_provider_fallback,
    record_workflow_execution,
    record_skill_execution,
    update_db_health,
    log_info,
    log_error,
    log_debug,
    get_metrics,
    service_health_check,
    db_health_check,
    redis_health_check,
    ErrorTracker,
    error_tracker,
    with_observability,
    LogRecord,
    with_observability,
)


def test_log_record_serialization():
    """Test LogRecord JSON serialization excludes sensitive keys."""
    record = LogRecord(
        timestamp=datetime.now(timezone.utc).isoformat(),
        level="info",
        service="test-service",
        event="test-event",
        request_id="req-123",
        duration_ms=150,
        metadata={"pan": "ABCDE1234F", "gstin": "07AAAAA1234Z1Z", "safe_key": "safe_value"},
    )
    data = json.loads(record.to_json())
    
    # Sensitive keys should be filtered out
    assert "pan" not in data.get("metadata", {})
    assert "gstin" not in data.get("metadata", {})
    # Safe key should remain
    assert data["metadata"]["safe_key"] == "safe_value"
    assert data["request_id"] == "req-123"
    assert data["duration_ms"] == 150
    print("✅ test_log_record_serialization passed")


def test_metrics_snapshot():
    """Test metrics collection and snapshot."""
    # Record some requests
    record_request(120, True, "test-event")
    record_request(200, False, "test-event")
    record_request(150, True, "another-event")
    
    # Record tool latencies
    record_tool_latency("test-tool", 80)
    record_tool_latency("test-tool", 120)
    record_tool_latency("another-tool", 200)
    
    # Record model latency
    record_model_latency(500)
    record_model_latency(600)
    
    # Record events
    record_provider_fallback()
    record_workflow_execution()
    record_skill_execution()
    
    # Update DB health
    update_db_health(True)
    
    # Get metrics
    metrics = get_metrics()
    
    assert metrics["service"] == "mcp-servers"
    assert metrics["request_count"] == 3
    assert metrics["error_count"] == 1
    assert metrics["avg_request_latency_ms"] > 0
    assert metrics["provider_fallbacks"] == 1
    assert metrics["workflow_executions"] == 1
    assert metrics["skill_executions"] == 1
    assert metrics["db_health"] == "healthy"
    
    # Check tool stats
    assert "test-tool" in metrics["tool_stats"]
    tool_stats = metrics["tool_stats"]["test-tool"]
    assert tool_stats["count"] == 2
    assert tool_stats["avg_ms"] == 100.0  # (80 + 120) / 2
    
    print("✅ test_metrics_snapshot passed")


def test_service_health_check():
    """Test service health check endpoint."""
    # Test with a mock check
    def mock_check():
        return {"healthy": True, "latency_ms": 5.0, "details": "OK"}
    
    result = service_health_check("test-service", mock_check)
    assert result["service"] == "test-service"
    assert result["healthy"] is True
    assert "timestamp" in result
    print("✅ test_service_health_check passed")


def test_db_health_check():
    """Test database health check (mock)."""
    # This just tests the function signature and structure
    # In real usage, would connect to actual DB
    result = db_health_check(None)  # None simulates no connection
    assert "healthy" in result
    assert "latency_ms" in result
    assert "details" in result
    print("✅ test_db_health_check passed")


def test_redis_health_check():
    """Test Redis health check (mock)."""
    result = redis_health_check(None)  # None simulates no connection
    assert "healthy" in result
    assert "latency_ms" in result
    assert "details" in result
    print("✅ test_redis_health_check passed")


def test_error_tracker():
    """Test error tracking."""
    tracker = ErrorTracker(max_errors=5)
    
    try:
        raise ValueError("test error 1")
    except ValueError:
        error_tracker.track(ValueError("test error 1"), {"source": "test"})
    
    try:
        raise TypeError("test error 2")
    except TypeError:
        error_tracker.track(TypeError("test error 2"), {"source": "test"})
    
    recent = error_tracker.get_recent()
    assert len(recent) == 2
    assert recent[0]["error_type"] == "ValueError"
    assert recent[1]["error_type"] == "TypeError"
    print("✅ test_error_tracker passed")


def test_with_observability_decorator():
    """Test the with_observability decorator wrapper."""
    
    @with_observability("test-decorator-event", "test-service")
    def test_func():
        return {"result": "success"}
    
    # Test async wrapper
    result = test_func()
    assert result == {"result": "success"}
    print("✅ test_with_observability_decorator passed")


def test_metrics_persistence_across_calls():
    """Test that metrics persist across multiple function calls."""
    # Clear by recording more (metrics accumulate)
    record_request(100, True, "persistent-event")
    record_request(200, True, "persistent-event")
    
    metrics = get_metrics()
    assert metrics["request_count"] >= 2
    print("✅ test_metrics_persistence_across_calls passed")


def test_safe_metadata_filtering():
    """Test that metadata filtering works correctly."""
    record = LogRecord(
        timestamp=datetime.now(timeftime.utc).isoformat(),
        level="info",
        service="test",
        event="test",
        metadata={"pan": "ABCDE1234F", "email": "user@example.com", "ssn": "123-45-6789", "safe": "keep"},
    )
    data = json.loads(record.to_json())
    
    metadata = data.get("metadata", {})
    assert "pan" not in metadata
    assert "email" not in metadata
    assert "ssn" not in metadata
    assert metadata["safe"] == "keep"
    print("✅ test_safe_metadata_filtering passed")


# ============================
# Main: Run all tests
# ============================

if __name__ == "__main__":
    tests = [
        test_log_record_serialization,
        test_metrics_snapshot,
        test_service_health_check,
        test_db_health_check,
        test_redis_health_check,
        test_error_tracker,
        test_with_observability_decorator,
        test_metrics_persistence_across_calls,
        test_safe_metadata_filtering,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    
    if failed > 0:
        sys.exit(1)
    else:
        print("All Phase 9 observability tests passed ✅")
        sys.exit(0)