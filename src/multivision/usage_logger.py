# src/multivision/usage_logger.py
"""MultiVision AI Usage Logger, Cost Calculator, and Per-Request Transparency Inspector."""

import os
import json
import uuid
import time
import sqlite3
import logging
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from src.multivision.models import (
    PricingStatus, get_model_info, is_free_model_info
)
from src.multivision.provider_health import record_provider_event

logger = logging.getLogger(__name__)

# DB File path
_DATA_DIR = os.getenv("ODYSSEUS_DATA_DIR", "data")
_LOG_FILE = os.path.join(_DATA_DIR, "ai_usage_logs.jsonl")
_DB_FILE = os.path.join(_DATA_DIR, "multivision_usage.db")


class AIUsageLogEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    provider: str
    model: str
    task: str
    input_modalities: List[str] = []
    file_types: List[str] = []
    request_id: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: float = 0.0
    status: str = "SUCCESS"                 # "SUCCESS", "FAILED", "FALLBACK_RESOLVED", "BLOCKED"
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    fallback_used: bool = False
    fallback_from: Optional[str] = None
    fallback_to: Optional[str] = None
    pricing_status: str = "FREE"            # "FREE", "FREE_TIER", "PAID", "UNKNOWN", "LOCAL_NO_API_USAGE"
    estimated_cost: Optional[float] = 0.0   # USD
    currency: str = "USD"
    routing_reason: Optional[str] = None
    prompt_preview: Optional[str] = None


def _init_db():
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        conn = sqlite3.connect(_DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_usage_logs (
                id TEXT PRIMARY KEY,
                timestamp REAL,
                provider TEXT,
                model TEXT,
                task TEXT,
                input_modalities TEXT,
                file_types TEXT,
                request_id TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                latency_ms REAL,
                status TEXT,
                error_code INTEGER,
                error_message TEXT,
                retry_count INTEGER,
                fallback_used INTEGER,
                fallback_from TEXT,
                fallback_to TEXT,
                pricing_status TEXT,
                estimated_cost REAL,
                currency TEXT,
                routing_reason TEXT,
                prompt_preview TEXT
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to initialize MultiVision usage DB: {e}")

_init_db()


def compute_request_cost(
    model_id: str,
    input_tokens: Optional[int],
    output_tokens: Optional[int]
) -> Tuple[str, Optional[float]]:
    """Compute accurate cost according to verified pricing metadata.
    - Free models -> 0.00
    - Paid models -> (input_tokens / 1,000,000 * input_price) + (output_tokens / 1,000,000 * output_price)
    - Unknown models -> NULL (None)
    """
    info = get_model_info(model_id)
    if not info:
        return PricingStatus.UNKNOWN.value, None

    status = info.pricing.pricing_status

    if status in (PricingStatus.FREE, PricingStatus.FREE_TIER, PricingStatus.LOCAL_NO_API_USAGE):
        return status.value, 0.0

    if status == PricingStatus.PAID:
        if input_tokens is None and output_tokens is None:
            return status.value, None
        
        in_price = info.pricing.input_price or 0.0
        out_price = info.pricing.output_price or 0.0
        it = input_tokens or 0
        ot = output_tokens or 0
        
        cost = (it / 1_000_000.0 * in_price) + (ot / 1_000_000.0 * out_price)
        return status.value, round(cost, 6)

    return PricingStatus.UNKNOWN.value, None


def log_ai_usage(
    provider: str,
    model: str,
    task: str = "CHAT",
    input_modalities: Optional[List[str]] = None,
    file_types: Optional[List[str]] = None,
    request_id: Optional[str] = None,
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    latency_ms: float = 0.0,
    status: str = "SUCCESS",
    error_code: Optional[int] = None,
    error_message: Optional[str] = None,
    retry_count: int = 0,
    fallback_used: bool = False,
    fallback_from: Optional[str] = None,
    fallback_to: Optional[str] = None,
    routing_reason: Optional[str] = None,
    prompt_preview: Optional[str] = None
) -> AIUsageLogEntry:
    """Log an AI request event persistently in both SQLite and JSONL."""
    pricing_status, cost = compute_request_cost(model, input_tokens, output_tokens)

    entry = AIUsageLogEntry(
        provider=provider,
        model=model,
        task=task,
        input_modalities=input_modalities or ["text"],
        file_types=file_types or [],
        request_id=request_id or str(uuid.uuid4())[:8],
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=round(latency_ms, 2),
        status=status,
        error_code=error_code,
        error_message=error_message,
        retry_count=retry_count,
        fallback_used=fallback_used,
        fallback_from=fallback_from,
        fallback_to=fallback_to,
        pricing_status=pricing_status,
        estimated_cost=cost,
        currency="USD",
        routing_reason=routing_reason,
        prompt_preview=prompt_preview[:120] if prompt_preview else None
    )

    # 1. Update in SQLite
    try:
        conn = sqlite3.connect(_DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ai_usage_logs VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (
            entry.id, entry.timestamp, entry.provider, entry.model, entry.task,
            json.dumps(entry.input_modalities), json.dumps(entry.file_types),
            entry.request_id, entry.input_tokens, entry.output_tokens,
            entry.latency_ms, entry.status, entry.error_code, entry.error_message,
            entry.retry_count, 1 if entry.fallback_used else 0,
            entry.fallback_from, entry.fallback_to, entry.pricing_status,
            entry.estimated_cost, entry.currency, entry.routing_reason,
            entry.prompt_preview
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to insert into MultiVision SQLite usage log: {e}")

    # 2. Append to JSONL
    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")
    except Exception as e:
        logger.error(f"Failed to append to MultiVision JSONL log: {e}")

    # 3. Update Provider Health
    record_provider_event(
        provider=provider,
        status_code=error_code or (200 if status == "SUCCESS" else 500),
        error_message=error_message,
        latency=latency_ms / 1000.0,
        cost=cost or 0.0
    )

    return entry


def get_recent_usage_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve recent usage logs for the AI Operations Inspector."""
    try:
        conn = sqlite3.connect(_DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ai_usage_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()

        results = []
        for r in rows:
            d = dict(r)
            try: d["input_modalities"] = json.loads(d["input_modalities"])
            except Exception: pass
            try: d["file_types"] = json.loads(d["file_types"])
            except Exception: pass
            results.append(d)
        return results
    except Exception as e:
        logger.error(f"Failed to query usage logs: {e}")
        return []


def get_usage_metrics_summary() -> Dict[str, Any]:
    """Compute overall AI Operations dashboard metrics."""
    try:
        conn = sqlite3.connect(_DB_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM ai_usage_logs")
        total_reqs = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM ai_usage_logs WHERE pricing_status IN ('FREE', 'FREE_TIER', 'LOCAL_NO_API_USAGE')")
        free_reqs = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM ai_usage_logs WHERE pricing_status = 'PAID'")
        paid_reqs = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM ai_usage_logs WHERE status = 'FAILED' OR error_code >= 400")
        failed_reqs = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM ai_usage_logs WHERE fallback_used = 1")
        fallback_reqs = cursor.fetchone()[0] or 0

        cursor.execute("SELECT AVG(latency_ms) FROM ai_usage_logs WHERE latency_ms > 0")
        avg_latency = round(cursor.fetchone()[0] or 0.0, 2)

        cursor.execute("SELECT SUM(estimated_cost) FROM ai_usage_logs WHERE estimated_cost IS NOT NULL")
        total_cost = round(cursor.fetchone()[0] or 0.0, 4)

        # By Provider
        cursor.execute("SELECT provider, COUNT(*) FROM ai_usage_logs GROUP BY provider")
        provider_counts = dict(cursor.fetchall())

        # By Task
        cursor.execute("SELECT task, COUNT(*) FROM ai_usage_logs GROUP BY task")
        task_counts = dict(cursor.fetchall())

        conn.close()

        return {
            "total_requests": total_reqs,
            "free_requests": free_reqs,
            "paid_requests": paid_reqs,
            "failed_requests": failed_reqs,
            "fallback_requests": fallback_reqs,
            "average_latency_ms": avg_latency,
            "total_estimated_cost": total_cost,
            "provider_counts": provider_counts,
            "task_counts": task_counts
        }
    except Exception as e:
        logger.error(f"Failed to compute usage metrics: {e}")
        return {
            "total_requests": 0, "free_requests": 0, "paid_requests": 0,
            "failed_requests": 0, "fallback_requests": 0, "average_latency_ms": 0.0,
            "total_estimated_cost": 0.0, "provider_counts": {}, "task_counts": {}
        }
