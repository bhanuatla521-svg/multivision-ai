# src/ai_operations.py
"""AI Operations logger and resilience metrics tracker."""

import json
import logging
import os
import time
from typing import Optional, Dict, Any, List

logger = logging.getLogger("ai_operations")

_OPERATIONS_LOG_PATH = os.path.join("data", "ai_operations.jsonl")
_OPERATIONS_BUFFER: List[Dict[str, Any]] = []
_MAX_BUFFER_SIZE = 500


def record_ai_operation(
    provider: str,
    model: str,
    error_code: Optional[int] = None,
    retry_count: int = 0,
    fallback_model: Optional[str] = None,
    fallback_reason: Optional[str] = None,
    latency: float = 0.0,
    status: str = "success",
    session_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Record an AI operational event with provider resilience tracking."""
    event = {
        "timestamp": time.time(),
        "provider": provider or "unknown",
        "model": model or "unknown",
        "error_code": error_code,
        "retry_count": retry_count,
        "fallback_model": fallback_model,
        "fallback_reason": fallback_reason,
        "latency": round(latency, 4),
        "status": status,
        "session_id": session_id,
    }
    if extra:
        event["extra"] = extra

    # Log structured event
    if error_code or fallback_model or status != "success":
        logger.warning(
            "[AI-OPERATIONS] status=%s provider=%s model=%s error_code=%s retries=%s fallback=%s reason=%s latency=%.3fs",
            status,
            provider,
            model,
            error_code,
            retry_count,
            fallback_model,
            fallback_reason,
            latency,
        )
    else:
        logger.info(
            "[AI-OPERATIONS] status=%s provider=%s model=%s latency=%.3fs",
            status,
            provider,
            model,
            latency,
        )

    # In-memory buffer
    _OPERATIONS_BUFFER.append(event)
    if len(_OPERATIONS_BUFFER) > _MAX_BUFFER_SIZE:
        _OPERATIONS_BUFFER.pop(0)

    # Append to disk log
    try:
        os.makedirs(os.path.dirname(_OPERATIONS_LOG_PATH), exist_ok=True)
        with open(_OPERATIONS_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as e:
        logger.debug("Failed to write to ai_operations.jsonl: %s", e)

    return event


def get_recent_operations(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve the most recent AI operation events."""
    return list(reversed(_OPERATIONS_BUFFER[-limit:]))
