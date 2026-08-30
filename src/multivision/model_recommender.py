# src/multivision/model_recommender.py
"""MultiVision AI Model Recommendation Engine, 0-100 Scoring, and Model Comparison."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from src.multivision.models import (
    ModelInfo, TaskCategory, PricingStatus, list_all_models,
    get_model_info, is_free_model_info
)
from src.multivision.provider_health import get_provider_health, ProviderStatus


class ScoreBreakdown(BaseModel):
    capability_score: float     # max 40
    quality_score: float        # max 25
    cost_score: float           # max 15
    speed_score: float          # max 10
    reliability_score: float    # max 10
    total_score: int            # 0 - 100


class RecommendationResult(BaseModel):
    recommended_model: str
    display_name: str
    provider: str
    reason: str
    fallback_models: List[str]
    cost_class: str
    estimated_cost: Optional[str]
    capability_match_score: int
    score_breakdown: ScoreBreakdown
    model_info: ModelInfo


def calculate_model_score(
    model: ModelInfo,
    task: TaskCategory,
    required_modalities: List[str],
    free_only: bool = True,
    quality_preference: str = "balanced", # "high", "speed", "balanced"
) -> ScoreBreakdown:
    """Compute normalized 0-100 Model Score:
    - Capability Match: 40%
    - Quality: 25%
    - Cost: 15%
    - Speed: 10%
    - Reliability: 10%
    """
    caps = model.capabilities

    # 1. Capability Match (40 pts)
    cap_points = 40.0
    mod_checks = {
        "image": caps.image_input,
        "audio": caps.audio_input,
        "video": caps.video_input,
        "pdf": caps.pdf_input or caps.document_input,
        "document": caps.document_input,
        "coding": caps.coding,
        "reasoning": caps.reasoning,
        "tools": caps.tool_calling,
    }

    missing_caps = 0
    total_reqs = len(required_modalities)
    if total_reqs > 0:
        for m in required_modalities:
            if m.lower() in mod_checks and not mod_checks[m.lower()]:
                missing_caps += 1
        cap_ratio = max(0.0, (total_reqs - missing_caps) / total_reqs)
        cap_points = cap_ratio * 40.0
    else:
        # Generic text chat
        cap_points = 40.0 if caps.text_input else 0.0

    # 2. Quality (25 pts)
    quality_points = (model.quality_rating / 100.0) * 25.0

    # 3. Cost (15 pts)
    is_free = is_free_model_info(model)
    if is_free:
        cost_points = 15.0
    elif model.pricing.pricing_status == PricingStatus.PAID:
        cost_points = 0.0 if free_only else 7.5
    else:
        cost_points = 5.0

    # 4. Speed (10 pts)
    speed_points = (model.speed_rating / 100.0) * 10.0

    # 5. Reliability (10 pts)
    # Check provider health
    p_health = get_provider_health(model.provider)
    rel_factor = 1.0
    if p_health.status == ProviderStatus.ONLINE:
        rel_factor = 1.0
    elif p_health.status == ProviderStatus.DEGRADED:
        rel_factor = 0.7
    elif p_health.status in (ProviderStatus.RATE_LIMITED, ProviderStatus.UNAVAILABLE):
        rel_factor = 0.3
    elif p_health.status == ProviderStatus.INVALID_KEY:
        rel_factor = 0.0

    reliability_points = ((model.reliability_rating / 100.0) * 10.0) * rel_factor

    # Preference adjustment
    if quality_preference == "high":
        quality_points = min(25.0, quality_points * 1.1)
    elif quality_preference == "speed":
        speed_points = min(10.0, speed_points * 1.2)

    total = int(round(cap_points + quality_points + cost_points + speed_points + reliability_points))
    total = max(0, min(100, total))

    return ScoreBreakdown(
        capability_score=round(cap_points, 1),
        quality_score=round(quality_points, 1),
        cost_score=round(cost_points, 1),
        speed_score=round(speed_points, 1),
        reliability_score=round(reliability_points, 1),
        total_score=total
    )


def recommend_model(
    task: TaskCategory,
    modalities: Optional[List[str]] = None,
    file_types: Optional[List[str]] = None,
    free_only: bool = True,
    quality_preference: str = "balanced"
) -> RecommendationResult:
    """Recommend the optimal model for a specific task and input modalities."""
    required_mods = list(modalities or [])
    
    # Infer required modalities from file types if given
    for ft in file_types or []:
        low_ft = ft.lower()
        if low_ft in ("jpg", "jpeg", "png", "webp", "gif", "image"):
            if "image" not in required_mods: required_mods.append("image")
        elif low_ft in ("pdf", "application/pdf"):
            if "pdf" not in required_mods: required_mods.append("pdf")
        elif low_ft in ("mp3", "wav", "m4a", "ogg", "audio"):
            if "audio" not in required_mods: required_mods.append("audio")
        elif low_ft in ("mp4", "webm", "mov", "video"):
            if "video" not in required_mods: required_mods.append("video")

    all_models = list_all_models()
    scored_candidates = []

    for m in all_models:
        if free_only and not is_free_model_info(m):
            continue
        
        score_bd = calculate_model_score(
            m, task, required_mods, free_only=free_only, quality_preference=quality_preference
        )
        scored_candidates.append((score_bd.total_score, m, score_bd))

    # Sort descending by score
    scored_candidates.sort(key=lambda x: x[0], reverse=True)

    if not scored_candidates:
        # Fallback default if nothing eligible found
        default_model = get_model_info("gemini-2.5-flash") or all_models[0]
        score_bd = calculate_model_score(default_model, task, required_mods, free_only=free_only)
        return RecommendationResult(
            recommended_model=default_model.model_id,
            display_name=default_model.display_name,
            provider=default_model.provider,
            reason="Default high-performance multimodal recommendation.",
            fallback_models=["gemini-3.1-flash-lite", "meta-llama/llama-3.2-3b-instruct:free", "ollama/llama3.2"],
            cost_class=default_model.pricing.pricing_status.value,
            estimated_cost="$0.00 (Free Tier)" if is_free_model_info(default_model) else "$0.001",
            capability_match_score=score_bd.total_score,
            score_breakdown=score_bd,
            model_info=default_model
        )

    best_score, best_model, best_bd = scored_candidates[0]
    
    # Build fallback models
    fallbacks = [cand[1].model_id for cand in scored_candidates[1:4]]

    # Generate transparent reason
    reason_parts = []
    if required_mods:
        reason_parts.append(f"Direct native support for {' + '.join(required_mods).upper()}")
    else:
        reason_parts.append(f"Optimized for {task.value} workflows")
    
    if is_free_model_info(best_model):
        reason_parts.append("Free-tier verified pricing with zero API token cost")
    reason_parts.append(f"High quality score ({best_model.quality_rating}/100) and rapid throughput")

    reason_str = ". ".join(reason_parts) + "."

    cost_str = "$0.00 (Free Tier)" if is_free_model_info(best_model) else f"${(best_model.pricing.input_price or 0)/10:.4f}/10k tok"

    return RecommendationResult(
        recommended_model=best_model.model_id,
        display_name=best_model.display_name,
        provider=best_model.provider,
        reason=reason_str,
        fallback_models=fallbacks,
        cost_class=best_model.pricing.pricing_status.value,
        estimated_cost=cost_str,
        capability_match_score=best_score,
        score_breakdown=best_bd,
        model_info=best_model
    )


def get_best_model_by_task_catalog(free_only: bool = True) -> Dict[str, Dict[str, Any]]:
    """Return the Best Model for Every Task category."""
    tasks = [
        TaskCategory.CHAT,
        TaskCategory.IMAGE_ANALYSIS,
        TaskCategory.PDF_ANALYSIS,
        TaskCategory.AUDIO_TRANSCRIPTION,
        TaskCategory.VIDEO_ANALYSIS,
        TaskCategory.REASONING,
        TaskCategory.CODING,
        TaskCategory.RESEARCH,
        TaskCategory.COMPARISON,
        TaskCategory.STRUCTURED_OUTPUT,
    ]

    result = {}
    for t in tasks:
        # Infer modality
        mods = []
        if t in (TaskCategory.IMAGE_ANALYSIS, TaskCategory.OCR):
            mods = ["image"]
        elif t == TaskCategory.PDF_ANALYSIS:
            mods = ["pdf"]
        elif t in (TaskCategory.AUDIO_TRANSCRIPTION, TaskCategory.AUDIO_ANALYSIS):
            mods = ["audio"]
        elif t in (TaskCategory.VIDEO_ANALYSIS, TaskCategory.VIDEO_UNDERSTANDING):
            mods = ["video"]
        elif t == TaskCategory.CODING:
            mods = ["coding"]
        elif t == TaskCategory.REASONING:
            mods = ["reasoning"]

        rec = recommend_model(t, modalities=mods, free_only=free_only)
        result[t.value] = {
            "task": t.value,
            "recommended_model": rec.recommended_model,
            "display_name": rec.display_name,
            "provider": rec.provider,
            "reason": rec.reason,
            "cost_class": rec.cost_class,
            "estimated_cost": rec.estimated_cost,
            "score": rec.capability_match_score,
            "score_breakdown": rec.score_breakdown.model_dump(),
            "supported_inputs": [k for k, v in rec.model_info.capabilities.to_dict().items() if v and "_input" in k],
            "fallback_model": rec.fallback_models[0] if rec.fallback_models else "ollama/llama3.2"
        }

    return result


def compare_models(model_ids: List[str]) -> List[Dict[str, Any]]:
    """Compare 2 to 5 models side-by-side across quality, speed, cost, context, and capabilities."""
    results = []
    for mid in model_ids[:5]:
        info = get_model_info(mid)
        if not info:
            continue
        
        score_bd = calculate_model_score(info, TaskCategory.CHAT, required_modalities=[])
        results.append({
            "model_id": info.model_id,
            "display_name": info.display_name,
            "provider": info.provider,
            "pricing_status": info.pricing.pricing_status.value,
            "input_price": info.pricing.input_price,
            "output_price": info.pricing.output_price,
            "context_window": info.context_window,
            "quality_rating": info.quality_rating,
            "speed_rating": info.speed_rating,
            "reliability_rating": info.reliability_rating,
            "overall_score": score_bd.total_score,
            "capabilities": info.capabilities.to_dict(),
            "description": info.description
        })
    return results
