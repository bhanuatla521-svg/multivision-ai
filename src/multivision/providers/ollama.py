# src/multivision/providers/ollama.py
"""Ollama Local Model Provider for MultiVision."""

import os
import time
import uuid
import json
import httpx
from typing import Dict, Any, List, Optional, AsyncIterator
from src.multivision.providers.base import AIProvider, ProviderRequest, ProviderResponse, ProviderChunk


class OllamaProvider(AIProvider):
    """Ollama Local Model Provider."""

    DEFAULT_BASE_URL = "http://localhost:11434/v1"

    def __init__(self, base_url: Optional[str] = None):
        super().__init__(name="ollama", display_name="Ollama Local", is_demo=False)
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL") or self.DEFAULT_BASE_URL).rstrip("/")

    def is_configured(self) -> bool:
        return True

    def _get_headers(self) -> Dict[str, str]:
        return {"Content-Type": "application/json"}

    async def chat(self, request: ProviderRequest) -> ProviderResponse:
        t0 = time.time()
        url = f"{self.base_url}/chat/completions"
        model = request.model or "llama3.2"

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "stream": False
        }
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, headers=self._get_headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency = int((time.time() - t0) * 1000)
        choice = data.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "")
        usage = data.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})

        return ProviderResponse(
            id=data.get("id", f"ollama-{uuid.uuid4().hex[:8]}"),
            model=model,
            provider="ollama",
            content=content,
            role="assistant",
            finish_reason=choice.get("finish_reason", "stop"),
            usage=usage,
            is_demo=False,
            latency_ms=latency
        )

    async def chat_stream(self, request: ProviderRequest) -> AsyncIterator[ProviderChunk]:
        url = f"{self.base_url}/chat/completions"
        model = request.model or "llama3.2"

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "stream": True
        }
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        async with httpx.AsyncClient(timeout=180.0) as client:
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
                                id=chunk_json.get("id", "ollama-stream"),
                                model=model,
                                provider="ollama",
                                delta=delta,
                                is_demo=False,
                                finish_reason=finish_reason
                            )
                    except Exception:
                        continue

    async def health_check(self) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/models"
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(url, headers=self._get_headers())
                if r.status_code == 200:
                    return {"provider": "ollama", "status": "HEALTHY", "message": "Connected to Ollama local server"}
                return {"provider": "ollama", "status": "ERROR", "message": f"Status {r.status_code}"}
        except Exception as e:
            return {"provider": "ollama", "status": "OFFLINE", "message": "Ollama local server not detected on localhost:11434"}
