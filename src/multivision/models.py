# src/multivision/models.py
"""MultiVision AI Model Catalog, Capabilities, Pricing Definitions, and Task Enums.

Provides normalized capability schemas, pricing metadata, and task classification.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import time


class TaskCategory(str, Enum):
    CHAT = "CHAT"
    REASONING = "REASONING"
    IMAGE_ANALYSIS = "IMAGE_ANALYSIS"
    IMAGE_GENERATION = "IMAGE_GENERATION"
    PDF_ANALYSIS = "PDF_ANALYSIS"
    DOCUMENT_ANALYSIS = "DOCUMENT_ANALYSIS"
    AUDIO_TRANSCRIPTION = "AUDIO_TRANSCRIPTION"
    AUDIO_ANALYSIS = "AUDIO_ANALYSIS"
    VIDEO_ANALYSIS = "VIDEO_ANALYSIS"
    VIDEO_UNDERSTANDING = "VIDEO_UNDERSTANDING"
    OCR = "OCR"
    SUMMARIZATION = "SUMMARIZATION"
    INFORMATION_EXTRACTION = "INFORMATION_EXTRACTION"
    COMPARISON = "COMPARISON"
    RESEARCH = "RESEARCH"
    WEB_RESEARCH = "WEB_RESEARCH"
    CODING = "CODING"
    AGENT = "AGENT"
    STRUCTURED_OUTPUT = "STRUCTURED_OUTPUT"
    TRANSLATION = "TRANSLATION"
    CLASSIFICATION = "CLASSIFICATION"


class PricingStatus(str, Enum):
    FREE = "FREE"
    FREE_TIER = "FREE_TIER"
    PAID = "PAID"
    UNKNOWN = "UNKNOWN"
    LOCAL_NO_API_USAGE = "LOCAL_NO_API_USAGE"


class ModelCapabilities(BaseModel):
    text_input: bool = True
    text_output: bool = True
    image_input: bool = False
    image_output: bool = False
    audio_input: bool = False
    audio_output: bool = False
    video_input: bool = False
    video_output: bool = False
    pdf_input: bool = False
    document_input: bool = False
    structured_output: bool = False
    tool_calling: bool = False
    web_search: bool = False
    reasoning: bool = False
    coding: bool = False
    long_context: bool = False

    def to_dict(self) -> Dict[str, bool]:
        return self.model_dump()


class ModelPricing(BaseModel):
    pricing_status: PricingStatus = PricingStatus.UNKNOWN
    input_price: Optional[float] = None     # USD per 1M tokens
    output_price: Optional[float] = None    # USD per 1M tokens
    audio_price: Optional[float] = None     # USD per minute / unit
    image_price: Optional[float] = None     # USD per image
    video_price: Optional[float] = None     # USD per second
    currency: str = "USD"
    pricing_source: str = "official_provider_meta"
    pricing_checked_at: float = Field(default_factory=time.time)


class ModelInfo(BaseModel):
    model_id: str
    provider: str                           # "google", "openrouter", "groq", "ollama", "openai", "anthropic"
    display_name: str
    capabilities: ModelCapabilities
    pricing: ModelPricing
    context_window: int = 8192
    max_output_tokens: int = 4096
    speed_rating: int = 80                  # 0 - 100
    quality_rating: int = 80                # 0 - 100
    reliability_rating: int = 90            # 0 - 100
    description: str = ""
    recommended_tasks: List[TaskCategory] = []


# ========================================================================= #
# OFFICIAL MODEL REGISTRY
# ========================================================================= #

_DEFAULT_CATALOG: Dict[str, ModelInfo] = {
    # --------------------------------------------------------------------- #
    # GOOGLE GEMINI MODELS (Official Google AI Studio Free Tier & API)
    # --------------------------------------------------------------------- #
    "gemini-2.5-flash": ModelInfo(
        model_id="gemini-2.5-flash",
        provider="google",
        display_name="Gemini 2.5 Flash",
        capabilities=ModelCapabilities(
            text_input=True, text_output=True,
            image_input=True, image_output=False,
            audio_input=True, audio_output=False,
            video_input=True, video_output=False,
            pdf_input=True, document_input=True,
            structured_output=True, tool_calling=True,
            web_search=True, reasoning=True, coding=True,
            long_context=True
        ),
        pricing=ModelPricing(
            pricing_status=PricingStatus.FREE_TIER,
            input_price=0.075, output_price=0.30,
            pricing_source="Google AI Studio Free Tier (15 RPM / 1M TPM free)"
        ),
        context_window=1048576,
        max_output_tokens=8192,
        speed_rating=95,
        quality_rating=92,
        reliability_rating=94,
        description="Ultra-fast, state-of-the-art multimodal model with 1M context. Native support for audio, video, image, and PDF.",
        recommended_tasks=[
            TaskCategory.CHAT, TaskCategory.IMAGE_ANALYSIS, TaskCategory.PDF_ANALYSIS,
            TaskCategory.VIDEO_ANALYSIS, TaskCategory.VIDEO_UNDERSTANDING,
            TaskCategory.AUDIO_TRANSCRIPTION, TaskCategory.AUDIO_ANALYSIS,
            TaskCategory.OCR, TaskCategory.SUMMARIZATION, TaskCategory.INFORMATION_EXTRACTION,
            TaskCategory.CODING, TaskCategory.WEB_RESEARCH
        ]
    ),
    "gemini-2.5-pro": ModelInfo(
        model_id="gemini-2.5-pro",
        provider="google",
        display_name="Gemini 2.5 Pro",
        capabilities=ModelCapabilities(
            text_input=True, text_output=True,
            image_input=True, image_output=False,
            audio_input=True, audio_output=False,
            video_input=True, video_output=False,
            pdf_input=True, document_input=True,
            structured_output=True, tool_calling=True,
            web_search=True, reasoning=True, coding=True,
            long_context=True
        ),
        pricing=ModelPricing(
            pricing_status=PricingStatus.FREE_TIER,
            input_price=1.25, output_price=5.00,
            pricing_source="Google AI Studio Free Tier (2 RPM free)"
        ),
        context_window=2097152,
        max_output_tokens=8192,
        speed_rating=75,
        quality_rating=98,
        reliability_rating=95,
        description="Top-tier reasoning and coding model with 2M token context window and native multimodal comprehension.",
        recommended_tasks=[
            TaskCategory.REASONING, TaskCategory.CODING, TaskCategory.RESEARCH,
            TaskCategory.COMPARISON, TaskCategory.PDF_ANALYSIS, TaskCategory.VIDEO_UNDERSTANDING
        ]
    ),
    "gemini-3.7-flash": ModelInfo(
        model_id="gemini-3.7-flash",
        provider="google",
        display_name="Gemini 3.7 Flash",
        capabilities=ModelCapabilities(
            text_input=True, text_output=True,
            image_input=True, image_output=False,
            audio_input=True, audio_output=False,
            video_input=True, video_output=False,
            pdf_input=True, document_input=True,
            structured_output=True, tool_calling=True,
            web_search=True, reasoning=True, coding=True,
            long_context=True
        ),
        pricing=ModelPricing(
            pricing_status=PricingStatus.FREE_TIER,
            input_price=0.075, output_price=0.30,
            pricing_source="Google AI Studio Preview Free Tier"
        ),
        context_window=1048576,
        max_output_tokens=8192,
        speed_rating=96,
        quality_rating=95,
        reliability_rating=91,
        description="Next-generation hybrid reasoning model with instant multimodal comprehension and extreme throughput.",
        recommended_tasks=[
            TaskCategory.CHAT, TaskCategory.REASONING, TaskCategory.IMAGE_ANALYSIS,
            TaskCategory.PDF_ANALYSIS, TaskCategory.CODING
        ]
    ),
    "gemini-3.1-flash-lite": ModelInfo(
        model_id="gemini-3.1-flash-lite",
        provider="google",
        display_name="Gemini 3.1 Flash Lite",
        capabilities=ModelCapabilities(
            text_input=True, text_output=True,
            image_input=True, image_output=False,
            audio_input=True, audio_output=False,
            video_input=True, video_output=False,
            pdf_input=True, document_input=True,
            structured_output=True, tool_calling=True,
            web_search=True, reasoning=False, coding=True,
            long_context=True
        ),
        pricing=ModelPricing(
            pricing_status=PricingStatus.FREE_TIER,
            input_price=0.0375, output_price=0.15,
            pricing_source="Google AI Studio High-Throughput Tier"
        ),
        context_window=1048576,
        max_output_tokens=8192,
        speed_rating=99,
        quality_rating=88,
        reliability_rating=96,
        description="Lightweight, ultra-fast Gemini model designed for maximum speed and cost efficiency.",
        recommended_tasks=[
            TaskCategory.CHAT, TaskCategory.SUMMARIZATION, TaskCategory.CLASSIFICATION,
            TaskCategory.TRANSLATION, TaskCategory.IMAGE_ANALYSIS
        ]
    ),

    # --------------------------------------------------------------------- #
    # GROQ MODELS (Free Tier Rate-Limited Inference)
    # --------------------------------------------------------------------- #
    "llama-3.3-70b-versatile": ModelInfo(
        model_id="llama-3.3-70b-versatile",
        provider="groq",
        display_name="Llama 3.3 70B Versatile (Groq)",
        capabilities=ModelCapabilities(
            text_input=True, text_output=True,
            image_input=False, image_output=False,
            audio_input=False, audio_output=False,
            video_input=False, video_output=False,
            pdf_input=False, document_input=False,
            structured_output=True, tool_calling=True,
            web_search=False, reasoning=True, coding=True,
            long_context=True
        ),
        pricing=ModelPricing(
            pricing_status=PricingStatus.FREE_TIER,
            input_price=0.59, output_price=0.79,
            pricing_source="Groq Developer Free Tier"
        ),
        context_window=131072,
        max_output_tokens=32768,
        speed_rating=98,
        quality_rating=94,
        reliability_rating=95,
        description="Ultra-fast LPU inference on Meta's flagship 70B open-weights model.",
        recommended_tasks=[
            TaskCategory.CHAT, TaskCategory.REASONING, TaskCategory.CODING,
            TaskCategory.SUMMARIZATION, TaskCategory.AGENT
        ]
    ),
    "llama-3.1-8b-instant": ModelInfo(
        model_id="llama-3.1-8b-instant",
        provider="groq",
        display_name="Llama 3.1 8B Instant (Groq)",
        capabilities=ModelCapabilities(
            text_input=True, text_output=True,
            image_input=False, image_output=False,
            audio_input=False, audio_output=False,
            video_input=False, video_output=False,
            pdf_input=False, document_input=False,
            structured_output=True, tool_calling=True,
            web_search=False, reasoning=False, coding=True,
            long_context=True
        ),
        pricing=ModelPricing(
            pricing_status=PricingStatus.FREE_TIER,
            input_price=0.05, output_price=0.08,
            pricing_source="Groq Developer Free Tier"
        ),
        context_window=131072,
        max_output_tokens=8192,
        speed_rating=100,
        quality_rating=85,
        reliability_rating=97,
        description="Near-instantaneous response times (~750 tokens/s) for quick chat and text extraction.",
        recommended_tasks=[
            TaskCategory.CHAT, TaskCategory.TRANSLATION, TaskCategory.CLASSIFICATION,
            TaskCategory.SUMMARIZATION
        ]
    ),
    "whisper-large-v3": ModelInfo(
        model_id="whisper-large-v3",
        provider="groq",
        display_name="Whisper Large V3 (Groq)",
        capabilities=ModelCapabilities(
            text_input=False, text_output=True,
            image_input=False, image_output=False,
            audio_input=True, audio_output=False,
            video_input=False, video_output=False,
            pdf_input=False, document_input=False,
            structured_output=False, tool_calling=False,
            web_search=False, reasoning=False, coding=False,
            long_context=False
        ),
        pricing=ModelPricing(
            pricing_status=PricingStatus.FREE_TIER,
            audio_price=0.0001,
            pricing_source="Groq Audio Free Tier"
        ),
        context_window=4096,
        max_output_tokens=4096,
        speed_rating=99,
        quality_rating=96,
        reliability_rating=96,
        description="State-of-the-art multilingual audio transcription at incredible speeds.",
        recommended_tasks=[
            TaskCategory.AUDIO_TRANSCRIPTION, TaskCategory.AUDIO_ANALYSIS
        ]
    ),

    # --------------------------------------------------------------------- #
    # OPENROUTER EXPLICITLY FREE MODELS (:free tag)
    # --------------------------------------------------------------------- #
    "meta-llama/llama-3.2-3b-instruct:free": ModelInfo(
        model_id="meta-llama/llama-3.2-3b-instruct:free",
        provider="openrouter",
        display_name="Llama 3.2 3B Instruct (Free)",
        capabilities=ModelCapabilities(
            text_input=True, text_output=True,
            image_input=False, image_output=False,
            audio_input=False, audio_output=False,
            video_input=False, video_output=False,
            pdf_input=False, document_input=False,
            structured_output=True, tool_calling=True,
            web_search=False, reasoning=False, coding=True,
            long_context=False
        ),
        pricing=ModelPricing(
            pricing_status=PricingStatus.FREE,
            input_price=0.0, output_price=0.0,
            pricing_source="OpenRouter :free catalog"
        ),
        context_window=131072,
        max_output_tokens=4096,
        speed_rating=92,
        quality_rating=82,
        reliability_rating=88,
        description="Completely free compact Llama 3.2 model hosted on OpenRouter.",
        recommended_tasks=[
            TaskCategory.CHAT, TaskCategory.SUMMARIZATION, TaskCategory.CLASSIFICATION
        ]
    ),
    "meta-llama/llama-3.2-11b-vision-instruct:free": ModelInfo(
        model_id="meta-llama/llama-3.2-11b-vision-instruct:free",
        provider="openrouter",
        display_name="Llama 3.2 11B Vision Instruct (Free)",
        capabilities=ModelCapabilities(
            text_input=True, text_output=True,
            image_input=True, image_output=False,
            audio_input=False, audio_output=False,
            video_input=False, video_output=False,
            pdf_input=False, document_input=False,
            structured_output=True, tool_calling=True,
            web_search=False, reasoning=False, coding=True,
            long_context=True
        ),
        pricing=ModelPricing(
            pricing_status=PricingStatus.FREE,
            input_price=0.0, output_price=0.0,
            pricing_source="OpenRouter :free catalog"
        ),
        context_window=131072,
        max_output_tokens=4096,
        speed_rating=88,
        quality_rating=87,
        reliability_rating=85,
        description="Completely free multimodal vision model for image captioning and visual question answering.",
        recommended_tasks=[
            TaskCategory.IMAGE_ANALYSIS, TaskCategory.OCR, TaskCategory.CHAT
        ]
    ),
    "qwen/qwen-2.5-coder-32b-instruct:free": ModelInfo(
        model_id="qwen/qwen-2.5-coder-32b-instruct:free",
        provider="openrouter",
        display_name="Qwen 2.5 Coder 32B Instruct (Free)",
        capabilities=ModelCapabilities(
            text_input=True, text_output=True,
            image_input=False, image_output=False,
            audio_input=False, audio_output=False,
            video_input=False, video_output=False,
            pdf_input=False, document_input=False,
            structured_output=True, tool_calling=True,
            web_search=False, reasoning=True, coding=True,
            long_context=True
        ),
        pricing=ModelPricing(
            pricing_status=PricingStatus.FREE,
            input_price=0.0, output_price=0.0,
            pricing_source="OpenRouter :free catalog"
        ),
        context_window=32768,
        max_output_tokens=8192,
        speed_rating=86,
        quality_rating=93,
        reliability_rating=87,
        description="Top-ranked open-weights coding model, completely free on OpenRouter.",
        recommended_tasks=[
            TaskCategory.CODING, TaskCategory.AGENT, TaskCategory.STRUCTURED_OUTPUT
        ]
    ),
    "deepseek/deepseek-r1:free": ModelInfo(
        model_id="deepseek/deepseek-r1:free",
        provider="openrouter",
        display_name="DeepSeek R1 (Free)",
        capabilities=ModelCapabilities(
            text_input=True, text_output=True,
            image_input=False, image_output=False,
            audio_input=False, audio_output=False,
            video_input=False, video_output=False,
            pdf_input=False, document_input=False,
            structured_output=True, tool_calling=False,
            web_search=False, reasoning=True, coding=True,
            long_context=True
        ),
        pricing=ModelPricing(
            pricing_status=PricingStatus.FREE,
            input_price=0.0, output_price=0.0,
            pricing_source="OpenRouter :free catalog"
        ),
        context_window=65536,
        max_output_tokens=8192,
        speed_rating=80,
        quality_rating=97,
        reliability_rating=83,
        description="Open-weights reasoning model with chain-of-thought verification.",
        recommended_tasks=[
            TaskCategory.REASONING, TaskCategory.CODING, TaskCategory.RESEARCH
        ]
    ),

    # --------------------------------------------------------------------- #
    # OLLAMA LOCAL MODELS (Hardware cost not calculated; API cost = $0)
    # --------------------------------------------------------------------- #
    "ollama/llama3.2-vision": ModelInfo(
        model_id="ollama/llama3.2-vision",
        provider="ollama",
        display_name="Llama 3.2 Vision (Local Ollama)",
        capabilities=ModelCapabilities(
            text_input=True, text_output=True,
            image_input=True, image_output=False,
            audio_input=False, audio_output=False,
            video_input=False, video_output=False,
            pdf_input=False, document_input=False,
            structured_output=True, tool_calling=True,
            web_search=False, reasoning=False, coding=False,
            long_context=False
        ),
        pricing=ModelPricing(
            pricing_status=PricingStatus.LOCAL_NO_API_USAGE,
            input_price=0.0, output_price=0.0,
            pricing_source="Local Inference (No API Usage)"
        ),
        context_window=131072,
        max_output_tokens=4096,
        speed_rating=85,
        quality_rating=84,
        reliability_rating=99,
        description="Local private vision model running directly on your machine with 0 network egress.",
        recommended_tasks=[
            TaskCategory.IMAGE_ANALYSIS, TaskCategory.OCR, TaskCategory.CHAT
        ]
    ),
    "ollama/qwen2.5-coder": ModelInfo(
        model_id="ollama/qwen2.5-coder",
        provider="ollama",
        display_name="Qwen 2.5 Coder (Local Ollama)",
        capabilities=ModelCapabilities(
            text_input=True, text_output=True,
            image_input=False, image_output=False,
            audio_input=False, audio_output=False,
            video_input=False, video_output=False,
            pdf_input=False, document_input=False,
            structured_output=True, tool_calling=True,
            web_search=False, reasoning=True, coding=True,
            long_context=True
        ),
        pricing=ModelPricing(
            pricing_status=PricingStatus.LOCAL_NO_API_USAGE,
            input_price=0.0, output_price=0.0,
            pricing_source="Local Inference (No API Usage)"
        ),
        context_window=32768,
        max_output_tokens=4096,
        speed_rating=88,
        quality_rating=89,
        reliability_rating=99,
        description="Local coding assistant with code completion and debugging capabilities.",
        recommended_tasks=[
            TaskCategory.CODING, TaskCategory.STRUCTURED_OUTPUT
        ]
    ),
    "ollama/llama3.2": ModelInfo(
        model_id="ollama/llama3.2",
        provider="ollama",
        display_name="Llama 3.2 (Local Ollama)",
        capabilities=ModelCapabilities(
            text_input=True, text_output=True,
            image_input=False, image_output=False,
            audio_input=False, audio_output=False,
            video_input=False, video_output=False,
            pdf_input=False, document_input=False,
            structured_output=True, tool_calling=True,
            web_search=False, reasoning=False, coding=False,
            long_context=False
        ),
        pricing=ModelPricing(
            pricing_status=PricingStatus.LOCAL_NO_API_USAGE,
            input_price=0.0, output_price=0.0,
            pricing_source="Local Inference (No API Usage)"
        ),
        context_window=8192,
        max_output_tokens=4096,
        speed_rating=90,
        quality_rating=80,
        reliability_rating=99,
        description="Local offline text model for completely private chat without internet connection.",
        recommended_tasks=[
            TaskCategory.CHAT, TaskCategory.SUMMARIZATION
        ]
    ),

    # --------------------------------------------------------------------- #
    # PAID MODELS (For explicit non-FREE_ONLY mode)
    # --------------------------------------------------------------------- #
    "anthropic/claude-3.5-sonnet": ModelInfo(
        model_id="anthropic/claude-3.5-sonnet",
        provider="openrouter",
        display_name="Claude 3.5 Sonnet (OpenRouter)",
        capabilities=ModelCapabilities(
            text_input=True, text_output=True,
            image_input=True, image_output=False,
            audio_input=False, audio_output=False,
            video_input=False, video_output=False,
            pdf_input=True, document_input=True,
            structured_output=True, tool_calling=True,
            web_search=False, reasoning=True, coding=True,
            long_context=True
        ),
        pricing=ModelPricing(
            pricing_status=PricingStatus.PAID,
            input_price=3.00, output_price=15.00,
            pricing_source="OpenRouter Anthropic pricing"
        ),
        context_window=200000,
        max_output_tokens=8192,
        speed_rating=82,
        quality_rating=99,
        reliability_rating=95,
        description="Benchmark-leading reasoning, vision, and coding model.",
        recommended_tasks=[
            TaskCategory.CODING, TaskCategory.REASONING, TaskCategory.RESEARCH,
            TaskCategory.PDF_ANALYSIS
        ]
    ),
    "openai/gpt-4o": ModelInfo(
        model_id="openai/gpt-4o",
        provider="openrouter",
        display_name="GPT-4o (OpenRouter)",
        capabilities=ModelCapabilities(
            text_input=True, text_output=True,
            image_input=True, image_output=False,
            audio_input=True, audio_output=False,
            video_input=False, video_output=False,
            pdf_input=True, document_input=True,
            structured_output=True, tool_calling=True,
            web_search=False, reasoning=True, coding=True,
            long_context=True
        ),
        pricing=ModelPricing(
            pricing_status=PricingStatus.PAID,
            input_price=2.50, output_price=10.00,
            pricing_source="OpenRouter OpenAI pricing"
        ),
        context_window=128000,
        max_output_tokens=4096,
        speed_rating=85,
        quality_rating=97,
        reliability_rating=95,
        description="Flagship multimodal model with vision, audio, and tool integration.",
        recommended_tasks=[
            TaskCategory.CHAT, TaskCategory.IMAGE_ANALYSIS, TaskCategory.CODING
        ]
    )
}

_DYNAMIC_REGISTRY: Dict[str, ModelInfo] = dict(_DEFAULT_CATALOG)


def get_model_info(model_id: str) -> Optional[ModelInfo]:
    """Retrieve ModelInfo by ID, normalizing aliases."""
    if not model_id:
        return None
    mid = model_id.strip()
    if mid in _DYNAMIC_REGISTRY:
        return _DYNAMIC_REGISTRY[mid]
    
    # Try normalized / fuzzy match
    low = mid.lower()
    for k, v in _DYNAMIC_REGISTRY.items():
        if k.lower() == low or k.split("/")[-1].lower() == low or low in k.lower():
            return v
    
    # Check if OpenRouter free tag
    if ":free" in low:
        return ModelInfo(
            model_id=mid,
            provider="openrouter",
            display_name=f"{mid.split('/')[-1].replace(':free', '')} (Free)",
            capabilities=ModelCapabilities(
                text_input=True, text_output=True,
                image_input="vision" in low or "vl" in low,
                coding="coder" in low or "code" in low,
                reasoning="r1" in low or "reason" in low
            ),
            pricing=ModelPricing(
                pricing_status=PricingStatus.FREE,
                input_price=0.0, output_price=0.0,
                pricing_source="OpenRouter :free tag"
            ),
            description="Dynamic OpenRouter free model."
        )

    # Fallback to UNKNOWN
    return ModelInfo(
        model_id=mid,
        provider="unknown",
        display_name=mid.split("/")[-1],
        capabilities=ModelCapabilities(text_input=True, text_output=True),
        pricing=ModelPricing(pricing_status=PricingStatus.UNKNOWN),
        description="Custom / unindexed model."
    )


def register_or_update_model(info: ModelInfo) -> None:
    """Register or dynamically update model information in the catalog."""
    _DYNAMIC_REGISTRY[info.model_id] = info


def list_all_models() -> List[ModelInfo]:
    """Return all models in the catalog."""
    return list(_DYNAMIC_REGISTRY.values())


def is_free_model_info(info: Optional[ModelInfo]) -> bool:
    """Check if model is classified as free or local."""
    if not info:
        return False
    return info.pricing.pricing_status in (
        PricingStatus.FREE,
        PricingStatus.FREE_TIER,
        PricingStatus.LOCAL_NO_API_USAGE
    )
