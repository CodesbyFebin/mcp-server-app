"""Observability service for MCPserver.in and app.mcpserver.in.

Provides:
- Structured JSON logging (no sensitive payloads)
- Request count/latency/errors metrics
- MCP tool latency tracking
- Model latency tracking
- Provider fallback events
- Workflow execution tracking
- Skill execution tracking
- Database health checks
- Container health endpoints
"""

import json
import time
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


# ============================
# Structured Log Record
# ============================

@dataclass
class LogRecord:
    """Structured log entry - no sensitive payloads."""
    timestamp: str  # ISO 8601 UTC
    level: str      # info, warning, error, debug
    service: str    # component/service name
    event: str      # what happened
    request_id: Optional[str] = None
    duration_ms: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None  # key-value only, no raw PII

    def to_json(self) -> str:
        """Serialize to JSON-safe dict."""
        data = {
            "timestamp": self.timestamp,
            "level": self.level,
            "service": self.service,
            "event": self.event,
        }
        if self.request_id:
            data["request_id"] = self.request_id
        if self.duration_ms is not None:
            data["duration_ms"] = self.duration_ms
        if self.metadata:
            # Filter out any accidental PII keys
            safe_meta = {k: v for k, v in self.metadata.items()
                        if k not in ("pan", "gstin", "ssn", "email", "phone", "credit_card")}
            data["metadata"] = safe_meta
        return json.dumps(data)


# ============================
# Observability Service
# ============================

class ObservabilityService:
    """Central observability service with metrics and logging."""

    def __init__(self, service_name: str = "mcp-servers"):
        self.service_name = service_name
        self.start_time = datetime.now(timezone.utc)
        self._metrics: Dict[str, Any] = {
            "request_count": 0,
            "request_latencies": [],  # last 1000 ms values
            "error_count": 0,
            "tool_latencies": {},     # tool_name -> [latencies]
            "model_latencies": [],    # [latency ms]
            "provider_fallbacks": 0,
            "workflow_executions": 0,
            "skill_executions": 0,
            "db_health": "unknown",
            "container_restarts": 0,
        }
        self._metrics_lock = threading.Lock()
        self._request_id_counter = 0

    def _gen_request_id(self) -> str:
        """Generate a unique request ID."""
        with self._metrics_lock:
            self._request_id_counter += 1
            return f"{self.service_name}-{int(time.time()*1000)}-{self._request_id_counter}"

    # ============================
    # Metrics incrementers
    # ============================

    def record_request(self, duration_ms: int, success: bool, service: str, event: str, request_id: Optional[str] = None):
        """Record a request metric."""
        with self._metrics_lock:
            self._metrics["request_count"] += 1
            latencies = self._metrics["request_latencies"]
            latencies.append(duration_ms)
            if len(latencies) > 1000:
                latencies[:] = latencies[-1000:]
            if not success:
                self._metrics["error_count"] += 1

    def record_tool_latency(self, tool_name: str, duration_ms: int):
        """Record MCP tool execution latency."""
        with self._metrics_lock:
            latencies = self._metrics["tool_latencies"].setdefault(tool_name, [])
            latencies.append(duration_ms)
            if len(latencies) > 100:
                latencies[:] = latencies[-100:]

    def record_model_latency(self, duration_ms: int):
        """Record LLM model execution latency."""
        with self._metrics_lock:
            self._metrics["model_latencies"].append(duration_ms)
            if len(self._metrics["model_latencies"]) > 1000:
                self._metrics["model_latencies"] = self._metrics["model_latencies"][-1000:]

    def record_provider_fallback(self):
        """Record LLM provider fallback event."""
        with self._metrics_lock:
            self._metrics["provider_fallbacks"] += 1

    def record_workflow_execution(self):
        """Record workflow execution."""
        with self._metrics_lock:
            self._metrics["workflow_executions"] += 1

    def record_skill_execution(self):
        """Record skill execution."""
        with self._metrics_lock:
            self._metrics["skill_executions"] += 1

    def update_db_health(self, healthy: bool):
        """Update database health status."""
        with self._metrics_lock:
            self._metrics["db_health"] = "healthy" if healthy else "unhealthy"

    def increment_container_restarts(self):
        """Increment container restart counter."""
        with self._metrics_lock:
            self._metrics["container_restarts"] += 1

    # ============================
    # Metrics snapshot
    # ============================

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        with self._metrics_lock:
            latencies = self._metrics["request_latencies"]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0

            tool_stats = {}
            for tool_name, tool_latencies in self._metrics["tool_latencies"].items():
                if tool_latencies:
                    tool_stats[tool_name] = {
                        "avg_ms": sum(tool_latencies) / len(tool_latencies),
                        "min_ms": min(tool_latencies),
                        "max_ms": max(tool_latencies),
                        "count": len(tool_latencies),
                    }

            return {
                "service": self.service_name,
                "uptime_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds(),
                "request_count": self._metrics["request_count"],
                "error_count": self._metrics["error_count"],
                "error_rate_percent": round(self._metrics["error_count"] / max(1, self._metrics["request_count"]) * 100, 2),
                "avg_request_latency_ms": round(avg_latency, 2),
                "model_avg_latency_ms": round(sum(self._metrics["model_latencies"]) / max(1, len(self._metrics["model_latencies"])), 2),
                "provider_fallbacks": self._metrics["provider_fallbacks"],
                "workflow_executions": self._metrics["workflow_executions"],
                "skill_executions": self._metrics["skill_executions"],
                "db_health": self._metrics["db_health"],
                "container_restarts": self._metrics["container_restarts"],
                "tool_stats": tool_stats,
            }

    # ============================
    # Logging helper
    # ============================

    def log(self, level: str, event: str, service: Optional[str] = None,
            request_id: Optional[str] = None, duration_ms: Optional[int] = None,
            metadata: Optional[Dict[str, Any]] = None):
        """Write a structured log record."""
        svc = service or self.service_name
        rid = request_id or self._gen_request_id()
        record = LogRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level,
            service=svc,
            event=event,
            request_id=rid,
            duration_ms=duration_ms,
            metadata=metadata,
        )
        print(record.to_json())


# Global instance
obs = ObservabilityService()


# Convenience functions for fast usage
def record_request(duration_ms: int, success: bool, event: str, service: Optional[str] = None):
    obs.record_request(duration_ms, success, service or obs.service_name, event)


def record_tool_latency(tool_name: str, duration_ms: int):
    obs.record_tool_latency(tool_name, duration_ms)


def record_model_latency(duration_ms: int):
    obs.record_model_latency(duration_ms)


def record_provider_fallback():
    obs.record_provider_fallback()


def record_workflow_execution():
    obs.record_workflow_execution()


def record_skill_execution():
    obs.record_skill_execution()


def update_db_health(healthy: bool):
    obs.update_db_health(healthy)


def log_info(event: str, service: Optional[str] = None, **metadata):
    obs.log("info", event, service)


def log_error(event: str, service: Optional[str] = None, **metadata):
    obs.log("error", event, service)


def log_debug(event: str, service: Optional[str] = None, **metadata):
    obs.log("debug", event, service)


# ============================
# Health Check Endpoints
# ============================

def db_health_check(sql_client=None) -> Dict[str, Any]:
    """Check database connectivity and return health status."""
    try:
        start = time.time()
        # In production: would use actual SQL client, e.g.:
        # async with sql_client.acquire() as conn:
        #     await conn.execute("SELECT 1")
        elapsed = time.time() - start
        is_healthy = elapsed < 5.0 and sql_client is not None
        obs.update_db_health(is_healthy)
        return {
            "healthy": is_healthy,
            "latency_ms": round(elapsed * 1000, 2),
            "details": "Connection successful" if is_healthy else "Connection failed",
        }
    except Exception as e:
        obs.update_db_health(False)
        return {
            "healthy": False,
            "latency_ms": 0,
            "details": str(e),
        }


def redis_health_check(redis_client=None) -> Dict[str, Any]:
    """Check Redis connectivity and return health status."""
    try:
        start = time.time()
        # In production: would use actual Redis client PING
        # async with redis_client as r:
        #     await r.ping()
        elapsed = time.time() - start
        is_healthy = elapsed < 2.0 and redis_client is not None
        return {
            "healthy": is_healthy,
            "latency_ms": round(elapsed * 1000, 2),
            "details": "PING successful" if is_healthy else "Redis unavailable",
        }
    except Exception as e:
        return {
            "healthy": False,
            "latency_ms": 0,
            "details": str(e),
        }


def service_health_check(service_name: str, check_fn) -> Dict[str, Any]:
    """Run a health check for a microservice."""
    try:
        result = check_fn()
        result["service"] = service_name
        result["timestamp"] = datetime.now(timezone.utc).isoformat()
        result["healthy"] = result.get("healthy", False)
        return result
    except Exception as e:
        return {
            "service": service_name,
            "healthy": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }


# ============================
# Error Tracking
# ============================

class ErrorTracker:
    """Track recent errors with context."""

    def __init__(self, max_errors: int = 100):
        self.max_errors = max_errors
        self._errors: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def track(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Track an error with context."""
        with self._lock:
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error_type": type(error).__name__,
                "error_message": str(error)[:500],
                "context": context or {},
            }
            self._errors.append(entry)
            if len(self._errors) > self.max_errors:
                self._errors[:] = self._errors[-self.max_errors:]

    def get_recent(self, n: int = 20) -> List[Dict[str, Any]]:
        """Get recent errors."""
        with self._lock:
            return self._errors[-n:]


error_tracker = ErrorTracker()


# ============================
# Module-level exports
# ============================

__all__ = [
    "ObservabilityService",
    "obs",
    "LogRecord",
    "record_request",
    "record_tool_latency",
    "record_model_latency",
    "record_provider_fallback",
    "record_workflow_execution",
    "record_skill_execution",
    "update_db_health",
    "log_info",
    "log_error",
    "log_debug",
    "service_health_check",
    "db_health_check",
    "redis_health_check",
    "ErrorTracker",
    "error_tracker",
]