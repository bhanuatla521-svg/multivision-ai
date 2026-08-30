# routes/multivision_routes.py
"""FastAPI Routes for MultiVision Multimodal AI Intelligence, Operations, and Cost Control."""

import io
import time
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Body, Response, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel

from src.multivision.models import (
    TaskCategory, PricingStatus, list_all_models, get_model_info, is_free_model_info
)
from src.multivision.provider_health import list_all_provider_health, get_provider_health
from src.multivision.model_recommender import (
    recommend_model, get_best_model_by_task_catalog, compare_models
)
from src.multivision.multimodal_router import (
    plan_multimodal_routing, get_free_only_mode, set_free_only_mode
)
from src.multivision.usage_logger import (
    get_usage_metrics_summary, get_recent_usage_logs, log_ai_usage
)
from src.multivision.report_generator import (
    generate_comprehensive_report_data, export_report_markdown, export_report_csv
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/multivision", tags=["MultiVision AI"])


class RecommendRequest(BaseModel):
    task: str = "CHAT"
    modalities: List[str] = ["text"]
    file_types: List[str] = []
    free_only: Optional[bool] = None
    quality_preference: str = "balanced"


class CompareRequest(BaseModel):
    models: List[str]


class AnalyzeRequest(BaseModel):
    prompt: str
    modalities: List[str] = ["text"]
    file_names: List[str] = []
    requested_model: Optional[str] = None


class ToggleFreeModeRequest(BaseModel):
    enabled: bool


@router.get("/free-mode")
def api_get_free_mode():
    """Get current global Free Mode setting."""
    return {"free_only": get_free_only_mode()}


@router.post("/toggle-free-mode")
def api_toggle_free_mode(req: ToggleFreeModeRequest):
    """Toggle global Free Mode (Hackathon Mode)."""
    current = set_free_only_mode(req.enabled)
    return {"free_only": current, "status": "updated"}


@router.get("/models")
def api_list_models(
    free_only: bool = False,
    vision: bool = False,
    audio: bool = False,
    video: bool = False,
    pdf: bool = False,
    coding: bool = False,
    reasoning: bool = False
):
    """Search and filter the Model Catalog with capabilities and pricing."""
    models = list_all_models()
    filtered = []

    for m in models:
        if free_only and not is_free_model_info(m):
            continue
        caps = m.capabilities
        if vision and not caps.image_input:
            continue
        if audio and not caps.audio_input:
            continue
        if video and not caps.video_input:
            continue
        if pdf and not (caps.pdf_input or caps.document_input):
            continue
        if coding and not caps.coding:
            continue
        if reasoning and not caps.reasoning:
            continue

        filtered.append({
            "model_id": m.model_id,
            "display_name": m.display_name,
            "provider": m.provider,
            "pricing_status": m.pricing.pricing_status.value,
            "input_price": m.pricing.input_price,
            "output_price": m.pricing.output_price,
            "context_window": m.context_window,
            "quality_rating": m.quality_rating,
            "speed_rating": m.speed_rating,
            "reliability_rating": m.reliability_rating,
            "description": m.description,
            "capabilities": caps.to_dict()
        })

    return {"count": len(filtered), "models": filtered}


@router.get("/providers")
def api_list_providers():
    """Get provider health, API key status (masked), and request metrics."""
    records = list_all_provider_health()
    all_models = list_all_models()

    out = []
    for r in records:
        prov_models = [m for m in all_models if m.provider == r.provider]
        free_count = sum(1 for m in prov_models if is_free_model_info(m))
        paid_count = sum(1 for m in prov_models if m.pricing.pricing_status == PricingStatus.PAID)
        unknown_count = sum(1 for m in prov_models if m.pricing.pricing_status == PricingStatus.UNKNOWN)

        d = r.model_dump()
        d["available_models"] = len(prov_models)
        d["free_models"] = free_count
        d["paid_models"] = paid_count
        d["unknown_models"] = unknown_count
        out.append(d)

    return {"providers": out}


@router.get("/best-by-task")
def api_best_by_task():
    """Get the Recommended Best Model for Every Task category."""
    catalog = get_best_model_by_task_catalog(free_only=get_free_only_mode())
    return {"best_models": catalog}


@router.post("/recommend")
def api_recommend_model(req: RecommendRequest):
    """Run the Model Recommendation Engine for a specific task and input modalities."""
    try:
        task_enum = TaskCategory(req.task.upper())
    except Exception:
        task_enum = TaskCategory.CHAT

    free_mode = req.free_only if req.free_only is not None else get_free_only_mode()

    rec = recommend_model(
        task=task_enum,
        modalities=req.modalities,
        file_types=req.file_types,
        free_only=free_mode,
        quality_preference=req.quality_preference
    )
    return rec.model_dump()


@router.post("/compare")
def api_compare_models(req: CompareRequest):
    """Compare 2 to 5 models side-by-side."""
    if len(req.models) < 2:
        raise HTTPException(400, "Please specify at least 2 models to compare.")
    matrix = compare_models(req.models)
    return {"comparison": matrix}


@router.get("/operations")
def api_operations_summary():
    """AI Operations Dashboard statistics."""
    summary = get_usage_metrics_summary()
    return summary


@router.get("/requests")
def api_recent_requests(limit: int = 50):
    """Per-Request Inspector query endpoint."""
    logs = get_recent_usage_logs(limit=limit)
    return {"count": len(logs), "requests": logs}


@router.get("/cost")
def api_cost_summary():
    """Cost Control dashboard statistics."""
    summary = get_usage_metrics_summary()
    return {
        "total_estimated_cost": summary.get("total_estimated_cost", 0.0),
        "total_requests": summary.get("total_requests", 0),
        "free_requests": summary.get("free_requests", 0),
        "paid_requests": summary.get("paid_requests", 0),
        "free_percentage": round((summary.get("free_requests", 0) / max(1, summary.get("total_requests", 1))) * 100, 1)
    }


@router.post("/analyze")
def api_multimodal_analyze(req: AnalyzeRequest):
    """Unified Multimodal Planning & Routing Analysis."""
    start_time = time.time()
    plan = plan_multimodal_routing(
        message=req.prompt,
        file_names=req.file_names,
        requested_model=req.requested_model
    )

    elapsed_ms = (time.time() - start_time) * 1000.0

    # Log in AI Usage Logger
    log_ai_usage(
        provider=plan.selected_provider,
        model=plan.selected_model,
        task=plan.detected_task.value,
        input_modalities=plan.input_modalities,
        file_types=plan.file_types,
        latency_ms=elapsed_ms,
        status="BLOCKED" if plan.free_mode_blocked else "SUCCESS",
        error_code=403 if plan.free_mode_blocked else None,
        error_message=plan.block_reason,
        routing_reason=plan.routing_reason,
        prompt_preview=req.prompt
    )

    return plan.model_dump()


@router.get("/report")
def api_generate_report(format: str = Query("json", pattern="^(json|markdown|csv)$")):
    """Generate and export comprehensive AI Usage Report."""
    data = generate_comprehensive_report_data()

    if format == "markdown":
        md_text = export_report_markdown(data)
        return PlainTextResponse(md_text, media_type="text/markdown")
    elif format == "csv":
        csv_text = export_report_csv(data)
        return PlainTextResponse(csv_text, media_type="text/csv")
    else:
        return JSONResponse(data)
