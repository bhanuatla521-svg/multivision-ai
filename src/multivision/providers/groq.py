# src/multivision/providers/groq.py
"""Groq Ultra-Fast LPU Inference Provider for MultiVision."""

import os
import time
import uuid
import json
import httpx
from typing import Dict, Any, List, Optional, AsyncIterator
from src.multivision.providers.base import AIProvider, ProviderRequest, ProviderResponse, ProviderChunk


class GroqProvider(AIProvider):
    """Groq Provider for Ultra-Fast Model Inference."""

    BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(name="groq", display_name="Groq LPU", is_demo=False)
        self.api_key = api_key or os.getenv("GROQ_API_KEY")

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json"
        }

    async def chat(self, request: ProviderRequest) -> ProviderResponse:
        if not self.is_configured():
            raise ValueError("Groq API key is not configured.")

        t0 = time.time()
        url = f"{self.BASE_URL}/chat/completions"
        model = request.model or "llama-3.3-70b-versatile"

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "stream": False
        }
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, headers=self._get_headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency = int((time.time() - t0) * 1000)
        choice = data.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "")
        usage = data.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})

        return ProviderResponse(
            id=data.get("id", f"groq-{uuid.uuid4().hex[:8]}"),
            model=model,
            provider="groq",
            content=content,
            role="assistant",
            finish_reason=choice.get("finish_reason", "stop"),
            usage=usage,
            is_demo=False,
            latency_ms=latency
        )

    async def chat_stream(self, request: ProviderRequest) -> AsyncIterator[ProviderChunk]:
        if not self.is_configured():
            raise ValueError("Groq API key is not configured.")

        url = f"{self.BASE_URL}/chat/completions"
        model = request.model or "llama-3.3-70b-versatile"

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "stream": True
        }
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, headers=self._get_headers(), json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk_json = json.loads(data_str)
                        choice = chunk_json.get("choices", [{}])[0]
                        delta = choice.get("delta", {}).get("content", "")
                        finish_reason = choice.get("finish_reason")
                        if delta or finish_reason:
                            yield ProviderChunk(
                                id=chunk_json.get("id", "groq-stream"),
                                model=model,
                                provider="groq",
                                delta=delta,
                                is_demo=False,
                                finish_reason=finish_reason
                            )
                    except Exception:
                        continue

    async def health_check(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {"provider": "groq", "status": "UNCONFIGURED", "message": "GROQ_API_KEY is not set."}
        try:
            url = f"{self.BASE_URL}/models"
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(url, headers=self._get_headers())
                if r.status_code == 200:
                    return {"provider": "groq", "status": "HEALTHY", "message": "Connected to Groq API"}
                return {"provider": "groq", "status": "ERROR", "message": f"Status {r.status_code}"}
        except Exception as e:
            return {"provider": "groq", "status": "UNREACHABLE", "message": str(e)}
