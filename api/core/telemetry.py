"""
Telemetry & Observability Module
================================
Provides LLM call tracing via LangSmith and structured application metrics.

Usage:
    from api.core.telemetry import configure_telemetry, trace_llm_call

    # At application startup
    configure_telemetry()

    # Wrap any LLM invocation
    with trace_llm_call("summarize_document", metadata={"doc_id": 123}):
        result = chain.invoke(...)
"""

import os
import time
import logging
from contextlib import contextmanager
from functools import wraps
from typing import Any, Optional

logger = logging.getLogger("ai_lawyer.telemetry")


def configure_telemetry() -> None:
    """
    Configure LangSmith tracing if credentials are available.
    Call this once at application startup (e.g., in FastAPI lifespan).
    """
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")

    if langsmith_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "ai-lawyer-prod")
        logger.info(
            "LangSmith tracing enabled",
            extra={"project": os.environ["LANGCHAIN_PROJECT"]},
        )
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        logger.warning("LangSmith API key not found. Tracing is disabled.")


# ── Metrics Counters (In-memory; swap for Prometheus in production) ──

_metrics: dict[str, Any] = {
    "llm_calls_total": 0,
    "llm_errors_total": 0,
    "llm_latency_seconds": [],
    "cache_hits_total": 0,
    "cache_misses_total": 0,
    "documents_indexed_total": 0,
}


def get_metrics() -> dict[str, Any]:
    """Return a snapshot of current application metrics."""
    latencies = _metrics["llm_latency_seconds"]
    return {
        "llm_calls_total": _metrics["llm_calls_total"],
        "llm_errors_total": _metrics["llm_errors_total"],
        "llm_avg_latency_seconds": (
            round(sum(latencies) / len(latencies), 3) if latencies else 0
        ),
        "llm_p99_latency_seconds": (
            round(sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0, 3)
        ),
        "cache_hits_total": _metrics["cache_hits_total"],
        "cache_misses_total": _metrics["cache_misses_total"],
        "documents_indexed_total": _metrics["documents_indexed_total"],
    }


def record_cache_hit() -> None:
    _metrics["cache_hits_total"] += 1


def record_cache_miss() -> None:
    _metrics["cache_misses_total"] += 1


def record_document_indexed() -> None:
    _metrics["documents_indexed_total"] += 1


@contextmanager
def trace_llm_call(operation: str, metadata: Optional[dict] = None):
    """
    Context manager that traces an LLM call with timing and error tracking.

    Usage:
        with trace_llm_call("answer_query", metadata={"session_id": "abc"}):
            response = chain.invoke(...)
    """
    start = time.perf_counter()
    _metrics["llm_calls_total"] += 1

    logger.info(
        "LLM call started",
        extra={"operation": operation, "metadata": metadata or {}},
    )

    try:
        yield
    except Exception as exc:
        _metrics["llm_errors_total"] += 1
        logger.error(
            "LLM call failed",
            extra={
                "operation": operation,
                "error": str(exc),
                "latency_seconds": round(time.perf_counter() - start, 3),
            },
        )
        raise
    else:
        latency = round(time.perf_counter() - start, 3)
        _metrics["llm_latency_seconds"].append(latency)
        logger.info(
            "LLM call completed",
            extra={"operation": operation, "latency_seconds": latency},
        )
