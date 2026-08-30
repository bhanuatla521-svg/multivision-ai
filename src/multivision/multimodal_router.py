# src/multivision/multimodal_router.py
"""MultiVision AI Unified Multimodal Routing, Intent Analysis, and Free-Only Guard."""

import os
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel

from src.multivision.models import (
    TaskCategory, PricingStatus, ModelInfo, list_all_models,
    get_model_info, is_free_model_info
)
from src.multivision.model_recommender import recommend_model, calculate_model_score

logger = logging.getLogger(__name__)

# Global Free Mode state (Defaults to True per project requirement)
_FREE_ONLY_GLOBAL: bool = True


def get_free_only_mode() -> bool:
    """Return whether Free Mode is currently enabled."""
    global _FREE_ONLY_GLOBAL
    env_val = os.getenv("FREE_ONLY", "").strip().lower()
    if env_val in ("true", "1", "yes", "on"):
        return True
    elif env_val in ("false", "0", "no", "off"):
        return False
    return _FREE_ONLY_GLOBAL


def set_free_only_mode(enabled: bool) -> bool:
    """Set Free Mode globally."""
    global _FREE_ONLY_GLOBAL
    _FREE_ONLY_GLOBAL = bool(enabled)
    os.environ["FREE_ONLY"] = "true" if _FREE_ONLY_GLOBAL else "false"
    logger.info(f"MultiVision Free Mode set to: {_FREE_ONLY_GLOBAL}")
    return _FREE_ONLY_GLOBAL


class MultimodalAnalysisPlan(BaseModel):
    user_intent: str
    detected_task: TaskCategory
    input_modalities: List[str]
    file_types: List[str]
    is_multimodal: bool
    unified_request_possible: bool
    selected_model: str
    selected_provider: str
    routing_reason: str
    fallback_chain: List[str]
    is_free: bool
    free_mode_blocked: bool = False
    block_reason: Optional[str] = None


def extract_modalities_and_task(
    message: str,
    attachments: Optional[List[Dict[str, Any]]] = None,
    file_names: Optional[List[str]] = None
) -> Tuple[TaskCategory, List[str], List[str]]:
    """Inspect user message and file metadata to determine task category and modalities."""
    modalities = set(["text"])
    file_types = set()
    
    # Process attachments
    for att in attachments or []:
        mime = (att.get("mime") or "").lower()
        name = (att.get("name") or att.get("original_name") or "").lower()
        ext = os.path.splitext(name)[1].lstrip(".")
        if ext: file_types.add(ext)

        if mime.startswith("image/") or ext in ("jpg", "jpeg", "png", "webp", "gif", "bmp", "svg"):
            modalities.add("image")
        elif mime == "application/pdf" or ext == "pdf":
            modalities.add("pdf")
        elif mime.startswith("audio/") or ext in ("mp3", "wav", "m4a", "ogg", "flac", "aac"):
            modalities.add("audio")
        elif mime.startswith("video/") or ext in ("mp4", "webm", "mov", "avi", "mkv"):
            modalities.add("video")
        elif ext in ("doc", "docx", "txt", "md", "csv", "json", "xlsx"):
            modalities.add("document")

    for fn in file_names or []:
        low = fn.lower()
        ext = os.path.splitext(low)[1].lstrip(".")
        if ext: file_types.add(ext)
        if ext in ("jpg", "jpeg", "png", "webp", "gif"): modalities.add("image")
        elif ext == "pdf": modalities.add("pdf")
        elif ext in ("mp3", "wav", "m4a", "ogg"): modalities.add("audio")
        elif ext in ("mp4", "webm", "mov", "avi"): modalities.add("video")

    low_msg = message.lower()
    
    # Classify Task Category
    if "video" in modalities:
        task = TaskCategory.VIDEO_ANALYSIS
    elif "audio" in modalities:
        task = TaskCategory.AUDIO_TRANSCRIPTION if any(w in low_msg for w in ("transcribe", "speech", "listen", "audio")) else TaskCategory.AUDIO_ANALYSIS
    elif "pdf" in modalities and len(modalities) == 2:
        task = TaskCategory.PDF_ANALYSIS
    elif "image" in modalities and len(modalities) == 2:
        task = TaskCategory.IMAGE_ANALYSIS
    elif any(w in low_msg for w in ("def ", "function", "class ", "bug", "code", "python", "javascript", "typescript", "sql", "error")):
        task = TaskCategory.CODING
    elif any(w in low_msg for w in ("why", "prove", "step by step", "reason", "calculate", "logic", "solve")):
        task = TaskCategory.REASONING
    elif any(w in low_msg for w in ("search", "find online", "latest", "news", "google", "web")):
        task = TaskCategory.RESEARCH
    elif any(w in low_msg for w in ("compare", "difference between", "versus", "vs")):
        task = TaskCategory.COMPARISON
    elif any(w in low_msg for w in ("summarize", "summary", "tldr", "brief")):
        task = TaskCategory.SUMMARIZATION
    elif any(w in low_msg for w in ("json", "extract fields", "schema", "table")):
        task = TaskCategory.STRUCTURED_OUTPUT
    else:
        task = TaskCategory.CHAT

    return task, list(modalities), list(file_types)


def plan_multimodal_routing(
    message: str,
    attachments: Optional[List[Dict[str, Any]]] = None,
    file_names: Optional[List[str]] = None,
    requested_model: Optional[str] = None,
    free_only: Optional[bool] = None
) -> MultimodalAnalysisPlan:
    """Build a complete Multimodal Analysis Plan and select the single best unified model."""
    if free_only is None:
        free_only = get_free_only_mode()

    task, modalities, file_types = extract_modalities_and_task(message, attachments, file_names)
    is_multimodal = len(modalities) > 1

    # Check if a specific model was requested
    selected_info = None
    if requested_model:
        selected_info = get_model_info(requested_model)

    # If requested model is paid and free_only is active, BLOCK
    if selected_info and free_only and not is_free_model_info(selected_info):
        return MultimodalAnalysisPlan(
            user_intent=message[:120],
            detected_task=task,
            input_modalities=modalities,
            file_types=file_types,
            is_multimodal=is_multimodal,
            unified_request_possible=False,
            selected_model=selected_info.model_id,
            selected_provider=selected_info.provider,
            routing_reason="Paid model blocked by Free Mode.",
            fallback_chain=["gemini-2.5-flash", "gemini-3.1-flash-lite", "meta-llama/llama-3.2-3b-instruct:free", "ollama/llama3.2"],
            is_free=False,
            free_mode_blocked=True,
            block_reason="Paid model blocked by Free Mode."
        )

    # Perform intelligent recommendation
    recommendation = recommend_model(
        task=task,
        modalities=modalities,
        file_types=file_types,
        free_only=free_only
    )

    chosen_model = selected_info or recommendation.model_info
    
    # Check if selected model can handle ALL required modalities in ONE request
    caps = chosen_model.capabilities
    can_handle_all = True
    for m in modalities:
        if m == "image" and not caps.image_input: can_handle_all = False
        elif m == "pdf" and not (caps.pdf_input or caps.document_input): can_handle_all = False
        elif m == "audio" and not caps.audio_input: can_handle_all = False
        elif m == "video" and not caps.video_input: can_handle_all = False

    # If chosen model lacks capabilities, auto-switch to highest scoring multimodal model
    if not can_handle_all and is_multimodal:
        chosen_model = recommendation.model_info
        can_handle_all = True

    # Fallback chain
    fallback_chain = list(recommendation.fallback_models)
    if chosen_model.model_id in fallback_chain:
        fallback_chain.remove(chosen_model.model_id)

    # Explain reasoning
    if is_multimodal:
        mod_str = " + ".join(m.upper() for m in modalities)
        reason = (
            f"Detected combined multimodal inputs: [{mod_str}]. "
            f"Routing as ONE unified multimodal request to {chosen_model.display_name} "
            f"to eliminate duplicate model calls, minimize token overhead, and prevent quota fragmentation."
        )
    else:
        reason = f"Routed to {chosen_model.display_name} based on high capability match for {task.value} and verified free-first tier."

    return MultimodalAnalysisPlan(
        user_intent=message[:120],
        detected_task=task,
        input_modalities=modalities,
        file_types=file_types,
        is_multimodal=is_multimodal,
        unified_request_possible=can_handle_all,
        selected_model=chosen_model.model_id,
        selected_provider=chosen_model.provider,
        routing_reason=reason,
        fallback_chain=fallback_chain,
        is_free=is_free_model_info(chosen_model),
        free_mode_blocked=False
    )
