# src/multivision/report_generator.py
"""MultiVision AI Comprehensive Usage Report Generator (JSON, CSV, Markdown)."""

import io
import csv
import json
import time
from datetime import datetime
from typing import Dict, Any, List

from src.multivision.models import list_all_models, PricingStatus
from src.multivision.provider_health import list_all_provider_health
from src.multivision.model_recommender import get_best_model_by_task_catalog
from src.multivision.usage_logger import get_usage_metrics_summary, get_recent_usage_logs
from src.multivision.multimodal_router import get_free_only_mode


def generate_comprehensive_report_data() -> Dict[str, Any]:
    """Compile complete MultiVision system analytics into structured report data."""
    models = list_all_models()
    providers = list_all_provider_health()
    best_by_task = get_best_model_by_task_catalog(free_only=get_free_only_mode())
    metrics = get_usage_metrics_summary()
    recent_logs = get_recent_usage_logs(limit=100)

    # Classify models
    free_models = [m.model_id for m in models if m.pricing.pricing_status in (PricingStatus.FREE, PricingStatus.FREE_TIER, PricingStatus.LOCAL_NO_API_USAGE)]
    paid_models = [m.model_id for m in models if m.pricing.pricing_status == PricingStatus.PAID]
    unknown_models = [m.model_id for m in models if m.pricing.pricing_status == PricingStatus.UNKNOWN]

    # Quota warnings
    quota_warnings = []
    for p in providers:
        if p.status.value == "RATE_LIMITED":
            quota_warnings.append(f"Provider {p.display_name} is currently RATE_LIMITED (HTTP 429). Recommended: switch to backup free tier.")
        elif p.status.value == "UNAVAILABLE":
            quota_warnings.append(f"Provider {p.display_name} returned HTTP 503 (Overloaded). Automatic fallback active.")

    return {
        "report_id": f"mv-report-{int(time.time())}",
        "generated_at": datetime.now().isoformat(),
        "free_mode_enabled": get_free_only_mode(),
        "provider_summary": [p.model_dump() for p in providers],
        "model_catalog": {
            "total_models": len(models),
            "free_count": len(free_models),
            "paid_count": len(paid_models),
            "unknown_count": len(unknown_models),
            "free_models": free_models,
            "paid_models": paid_models,
            "unknown_models": unknown_models
        },
        "best_model_by_task": best_by_task,
        "actual_usage": metrics,
        "quota_warnings": quota_warnings,
        "recommendations": [
            "Keep FREE_ONLY=true enabled for cost-free multimodal workflows using Gemini 2.5/3.7 Free Tiers and OpenRouter :free models.",
            "Utilize Gemini multimodal single-request architecture when combining Image + PDF + Text to reduce quota usage.",
            "For offline private execution, ensure Ollama is running locally on http://localhost:11434."
        ],
        "recent_logs": recent_logs
    }


def export_report_markdown(data: Dict[str, Any]) -> str:
    """Format full AI Usage Report in Github Markdown."""
    lines = []
    lines.append("# 🌐 MultiVision AI — System Intelligence & Usage Report")
    lines.append(f"**Generated:** {data['generated_at']}  ")
    lines.append(f"**Free Mode Active:** `{'ENABLED' if data['free_mode_enabled'] else 'DISABLED'}`\n")

    lines.append("## 1. Provider Health & API Keys")
    lines.append("| Provider | Key Status | Health Status | Masked Key | Requests Today | Errors | Cost ($) |")
    lines.append("|---|---|---|---|---|---|---|")
    for p in data["provider_summary"]:
        lines.append(f"| **{p['display_name']}** | `{p['key_status']}` | `{p['status']}` | `{p['masked_key']}` | {p['requests_today']} | {p['errors_today']} | ${p['estimated_cost_today']:.4f} |")
    lines.append("")

    lines.append("## 2. Model Catalog Breakdown")
    cat = data["model_catalog"]
    lines.append(f"- **Total Cataloged Models:** {cat['total_models']}")
    lines.append(f"- **Verified Free / Free-Tier Models:** {cat['free_count']}")
    lines.append(f"- **Paid Models:** {cat['paid_count']}")
    lines.append(f"- **Unknown Pricing Models:** {cat['unknown_count']}\n")

    lines.append("## 3. Best Model for Every Task")
    lines.append("| Task | Recommended Model | Provider | Cost Class | Score | Fallback Model |")
    lines.append("|---|---|---|---|---|---|")
    for task_name, info in data["best_model_by_task"].items():
        lines.append(f"| **{task_name}** | `{info['display_name']}` | {info['provider'].title()} | `{info['cost_class']}` | {info['score']}/100 | `{info['fallback_model']}` |")
    lines.append("")

    lines.append("## 4. Actual Usage & Cost Metrics")
    u = data["actual_usage"]
    lines.append(f"- **Total Requests:** {u['total_requests']}")
    lines.append(f"- **Free Requests:** {u['free_requests']} ({round((u['free_requests']/u['total_requests'])*100, 1) if u['total_requests'] else 100}%)")
    lines.append(f"- **Paid Requests:** {u['paid_requests']}")
    lines.append(f"- **Failed Requests:** {u['failed_requests']}")
    lines.append(f"- **Fallback Routed Requests:** {u['fallback_requests']}")
    lines.append(f"- **Average Latency:** {u['average_latency_ms']} ms")
    lines.append(f"- **Total Estimated Cost:** `${u['total_estimated_cost']:.4f}`\n")

    if data["quota_warnings"]:
        lines.append("## ⚠️ Quota & System Warnings")
        for w in data["quota_warnings"]:
            lines.append(f"> [!WARNING]\n> {w}\n")
    else:
        lines.append("## ✅ Quota & System Status")
        lines.append("All primary free-first providers are functioning within normal operational limits.\n")

    lines.append("## 💡 System Recommendations")
    for rec in data["recommendations"]:
        lines.append(f"- {rec}")
    lines.append("")

    return "\n".join(lines)


def export_report_csv(data: Dict[str, Any]) -> str:
    """Format AI Usage Logs in CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Timestamp", "Provider", "Model", "Task", "Input Modalities",
        "Status", "Error Code", "Latency (ms)", "Fallback Used", "Fallback To",
        "Pricing Status", "Estimated Cost ($)", "Routing Reason"
    ])
    for log in data.get("recent_logs", []):
        writer.writerow([
            log.get("id"),
            datetime.fromtimestamp(log.get("timestamp", time.time())).isoformat(),
            log.get("provider"),
            log.get("model"),
            log.get("task"),
            ",".join(log.get("input_modalities", [])),
            log.get("status"),
            log.get("error_code") or "",
            log.get("latency_ms"),
            1 if log.get("fallback_used") else 0,
            log.get("fallback_to") or "",
            log.get("pricing_status"),
            f"{log.get('estimated_cost', 0.0):.6f}" if log.get("estimated_cost") is not None else "NULL",
            log.get("routing_reason") or ""
        ])
    return output.getvalue()
