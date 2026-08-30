# src/multivision/providers/anthropic.py
"""Anthropic Claude Provider for MultiVision."""

import os
import time
import uuid
import json
import httpx
from typing import Dict, Any, List, Optional, AsyncIterator
from src.multivision.providers.base import AIProvider, ProviderRequest, ProviderResponse, ProviderChunk


class AnthropicProvider(AIProvider):
    """Anthropic Claude AI Provider."""

    BASE_URL = "https://api.anthropic.com/v1"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(name="anthropic", display_name="Anthropic Claude", is_demo=False)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def _get_headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self.api_key.strip(),
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

    async def chat(self, request: ProviderRequest) -> ProviderResponse:
        if not self.is_configured():
            raise ValueError("Anthropic API key is not configured.")

        t0 = time.time()
        url = f"{self.BASE_URL}/messages"
        model = request.model or "claude-3-5-sonnet-20241022"

        # Separate system prompt from messages
        system_prompt = ""
        user_messages = []
        for m in request.messages:
            if m.role == "system":
                system_prompt += f"{m.content}\n"
            else:
                user_messages.append({"role": m.role, "content": m.content})

        payload: Dict[str, Any] = {
            "model": model,
            "messages": user_messages,
            "max_tokens": request.max_tokens or 4096,
            "temperature": request.temperature,
            "stream": False
        }
        if system_prompt:
            payload["system"] = system_prompt.strip()

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=self._get_headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency = int((time.time() - t0) * 1000)
        content_blocks = data.get("content", [])
        text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        usage_data = data.get("usage", {})
        usage = {
            "prompt_tokens": usage_data.get("input_tokens", 0),
            "completion_tokens": usage_data.get("output_tokens", 0),
            "total_tokens": usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0)
        }

        return ProviderResponse(
            id=data.get("id", f"claude-{uuid.uuid4().hex[:8]}"),
            model=model,
            provider="anthropic",
            content=text,
            role="assistant",
            finish_reason=data.get("stop_reason", "end_turn"),
            usage=usage,
            is_demo=False,
            latency_ms=latency
        )

    async def chat_stream(self, request: ProviderRequest) -> AsyncIterator[ProviderChunk]:
        if not self.is_configured():
            raise ValueError("Anthropic API key is not configured.")

        url = f"{self.BASE_URL}/messages"
        model = request.model or "claude-3-5-sonnet-20241022"

        system_prompt = ""
        user_messages = []
        for m in request.messages:
            if m.role == "system":
                system_prompt += f"{m.content}\n"
            else:
                user_messages.append({"role": m.role, "content": m.content})

        payload: Dict[str, Any] = {
            "model": model,
            "messages": user_messages,
            "max_tokens": request.max_tokens or 4096,
            "temperature": request.temperature,
            "stream": True
        }
        if system_prompt:
            payload["system"] = system_prompt.strip()

        async with httpx.AsyncClient(timeout=90.0) as client:
            async with client.stream("POST", url, headers=self._get_headers(), json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    try:
                        chunk_json = json.loads(data_str)
                        ev_type = chunk_json.get("type")
                        if ev_type == "content_block_delta":
                            delta_text = chunk_json.get("delta", {}).get("text", "")
                            if delta_text:
                                yield ProviderChunk(
                                    id=chunk_json.get("id", "claude-stream"),
                                    model=model,
                                    provider="anthropic",
                                    delta=delta_text,
                                    is_demo=False
                                )
                        elif ev_type == "message_stop":
                            yield ProviderChunk(
                                id="claude-stream",
                                model=model,
                                provider="anthropic",
                                delta="",
                                is_demo=False,
                                finish_reason="stop"
                            )
                    except Exception:
                        continue

    async def health_check(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {"provider": "anthropic", "status": "UNCONFIGURED", "message": "ANTHROPIC_API_KEY is not set."}
        return {"provider": "anthropic", "status": "HEALTHY", "message": "Anthropic Claude API configured"}
