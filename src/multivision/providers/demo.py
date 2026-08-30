# src/multivision/providers/demo.py
"""MultiVision AI Demo Provider.

Provides deterministic, high-quality, transparently labeled demo responses
when DEMO_MODE=true or when live provider API keys are unconfigured.
"""

import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional, AsyncIterator
from src.multivision.providers.base import AIProvider, ProviderRequest, ProviderResponse, ProviderChunk


class DemoProvider(AIProvider):
    """Deterministic Demo Provider for MultiVision AI."""

    def __init__(self):
        super().__init__(name="demo", display_name="MultiVision Demo Engine", is_demo=True)

    def is_configured(self) -> bool:
        return True

    def _generate_demo_content(self, request: ProviderRequest) -> str:
        prompt_text = ""
        for m in reversed(request.messages):
            if m.role == "user":
                if isinstance(m.content, str):
                    prompt_text = m.content
                elif isinstance(m.content, list):
                    parts = [p.get("text", "") for p in m.content if isinstance(p, dict) and "text" in p]
                    prompt_text = " ".join(parts)
                break

        p_lower = prompt_text.lower()
        model_name = request.model or "gemini-2.5-flash"

        # Check for multimodal attachments
        attachments = request.attachments or []
        has_image = any(a.get("type", "").startswith("image") or "image" in str(a).lower() for a in attachments) or "image" in request.modalities
        has_pdf = any(a.get("type", "").endswith("pdf") or "pdf" in str(a).lower() for a in attachments) or "pdf" in request.modalities
        has_audio = any(a.get("type", "").startswith("audio") or "audio" in str(a).lower() for a in attachments) or "audio" in request.modalities
        has_video = any(a.get("type", "").startswith("video") or "video" in str(a).lower() for a in attachments) or "video" in request.modalities

        header = f"> ℹ️ **[DEMO MODE]** *Running deterministic response for model `{model_name}`. Live provider credentials are not configured or Demo Mode is active.*\n\n"

        if has_image or "image" in p_lower or "photo" in p_lower or "diagram" in p_lower:
            return header + f"""### 🖼️ Multimodal Vision Analysis
- **Detected Visual Elements**: Architectural schematic with 3 UI viewport layers, active navbar, and responsive CSS grid.
- **Color Palette**: Claude warm-dark background (`#181614`), Terracotta accent (`#d97757`), Emerald indicator (`#4ade80`).
- **OCR / Text Extracted**: *"MultiVision AI — Model Intelligence & Operations Control Center"*.
- **Quality Score**: 98/100 (Optimal contrast and hierarchy).

> **Vision Synthesis**: The provided visual artifact represents an operational dashboard optimized for unified multi-model routing and observability."""

        if has_pdf or "pdf" in p_lower or "document" in p_lower or "contract" in p_lower or "report" in p_lower:
            return header + f"""### 📄 Document Intelligence Analysis
- **Document Type**: Technical Specification & Operations Plan
- **Estimated Pages**: 14 Pages | **Word Count**: 4,820 words
- **Executive Summary**:
  1. **Unified Gateway**: Consolidates 16 cataloged AI models across 6 provider backends.
  2. **Zero-Latency Normalizer**: Eliminates split-call overhead by passing multimodal tokens in a single request envelope.
  3. **Cost Analytics**: Tracks token utilization and verifies free-tier limits before routing.
- **Key Action Items**:
  - Deploy local provider gateways (Ollama/llama.cpp) for offline environments.
  - Enable API keys in Settings to unlock live cloud model streaming."""

        if has_audio or "audio" in p_lower or "voice" in p_lower or "transcript" in p_lower:
            return header + f"""### 🎙️ Audio Transcription & Intelligence
- **Audio Duration**: 00:42 | **Language**: English (en-US, Confidence: 99.4%)
- **Transcript**: *"MultiVision AI combines multi-model routing, research synthesis, and cost observability into a single control plane."*
- **Key Topics**: Unified multimodal AI, low latency routing, observability."""

        if has_video or "video" in p_lower:
            return header + f"""### 🎬 Video Understanding & Scene Decomposition
- **Scene 1 (00:00 - 00:15)**: Interface initialization, theme styling load, and model catalog cache population.
- **Scene 2 (00:16 - 00:32)**: User query routing to Vision-capable LLM with attachment verification.
- **Scene 3 (00:33 - 00:42)**: Stream completion and metrics logging in Operations Inspector."""

        if "code" in p_lower or "python" in p_lower or "function" in p_lower or "script" in p_lower:
            return header + f"""### 💻 MultiVision Code Synthesizer
Here is a clean implementation for capability-aware model routing:

```python
from src.multivision.multimodal_router import plan_multimodal_routing

# Plan optimal multimodal execution
plan = plan_multimodal_routing(
    prompt="{prompt_text.replace('"', '')[:80]}",
    file_names=["document.pdf", "sample.png"]
)

print(f"Optimal Model: {{plan.selected_model}} ({{plan.selected_provider}})")
print(f"Rationale: {{plan.routing_reason}}")
```
- **Execution**: Unified multimodal payload envelope.
- **Latency**: Simulated 142ms."""

        if "research" in p_lower or "investigate" in p_lower or "search" in p_lower:
            return header + f"""### 🔍 MultiVision Deep Research Synthesis
**Topic**: {prompt_text[:120]}

#### 1. Background & Architecture
MultiVision AI provides unified orchestration across multi-vendor AI providers (Gemini, Claude, GPT, Groq, Ollama). By normalizing multimodal inputs into an adaptive capability router, it dynamically selects the highest quality and most cost-effective model for every task.

#### 2. Synthesized Sources
1. *MultiVision Model Catalog (2026)* — Benchmark ratings across reasoning, vision, audio, and coding.
2. *Cloud Provider API Specifications* — Free tier quotas and context window scaling limits.
3. *Unified Multimodal Protocol* — Zero-split single request execution.

#### 3. Recommendation
For complex reasoning tasks, route to **Gemini 2.5 Pro** or **Claude 3.5 Sonnet**; for high-frequency queries, leverage **Gemini 2.5 Flash** or **Groq Llama 3.3 70B**."""

        # Default conversational response
        return header + f"""Hello! I am **MultiVision AI** (*Multimodal Intelligence, Unified*).

I received your prompt:
> *"{prompt_text}"*

### MultiVision Capabilities:
- 🚀 **Multi-Model Routing**: Auto-selects the optimal model for text, vision, audio, video, and documents.
- 💡 **Model Intelligence**: 16 cataloged models, side-by-side comparison, and benchmark ratings.
- 📊 **Operations & Cost Control**: Per-request latency, token tracking, and cost analytics.
- 🛠️ **Live Mode**: Configure your Google Gemini, OpenAI, Anthropic, or OpenRouter API key in **Settings > Add Models** to switch from Demo Mode to live AI."""

    async def chat(self, request: ProviderRequest) -> ProviderResponse:
        t0 = time.time()
        await asyncio.sleep(0.08)  # simulate rapid processing
        content = self._generate_demo_content(request)
        latency = int((time.time() - t0) * 1000)

        prompt_tokens = sum(len(str(m.content).split()) for m in request.messages) * 2
        completion_tokens = len(content.split()) * 2

        return ProviderResponse(
            id=f"demo-{uuid.uuid4().hex[:8]}",
            model=request.model or "gemini-2.5-flash",
            provider="demo",
            content=content,
            role="assistant",
            finish_reason="stop",
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            },
            is_demo=True,
            latency_ms=latency
        )

    async def chat_stream(self, request: ProviderRequest) -> AsyncIterator[ProviderChunk]:
        content = self._generate_demo_content(request)
        words = content.split(" ")
        req_id = f"demo-{uuid.uuid4().hex[:8]}"
        model = request.model or "gemini-2.5-flash"

        # Stream words in chunks
        chunk_size = 4
        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            delta = " ".join(chunk_words) + (" " if i + chunk_size < len(words) else "")
            await asyncio.sleep(0.02)
            yield ProviderChunk(
                id=req_id,
                model=model,
                provider="demo",
                delta=delta,
                is_demo=True,
                finish_reason=None
            )

        yield ProviderChunk(
            id=req_id,
            model=model,
            provider="demo",
            delta="",
            is_demo=True,
            finish_reason="stop"
        )

    async def health_check(self) -> Dict[str, Any]:
        return {
            "provider": "demo",
            "status": "HEALTHY",
            "message": "MultiVision Demo Engine active and ready.",
            "demo_mode": True
        }
