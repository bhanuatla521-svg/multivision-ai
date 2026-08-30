# src/multivision/providers/manager.py
"""MultiVision AI Provider Manager.

Coordinates all AI providers, detects credentials, enforces Demo Mode rules,
and provides seamless routing and fallback.
"""

import os
import logging
from typing import Dict, Any, List, Optional, AsyncIterator
from src.multivision.providers.base import AIProvider, ProviderRequest, ProviderResponse, ProviderChunk
from src.multivision.providers.demo import DemoProvider
from src.multivision.providers.gemini import GeminiProvider
from src.multivision.providers.openai import OpenAIProvider
from src.multivision.providers.anthropic import AnthropicProvider
from src.multivision.providers.openrouter import OpenRouterProvider
from src.multivision.providers.groq import GroqProvider
from src.multivision.providers.ollama import OllamaProvider

logger = logging.getLogger(__name__)


def is_demo_mode_forced() -> bool:
    """Check if DEMO_MODE environment variable is enabled."""
    val = os.getenv("DEMO_MODE", "").strip().lower()
    return val in ("true", "1", "yes", "on")


class ProviderManager:
    """Singleton Manager for AI Providers."""

    def __init__(self):
        self.demo_provider = DemoProvider()
        self.providers: Dict[str, AIProvider] = {
            "demo": self.demo_provider,
            "google": GeminiProvider(),
            "gemini": GeminiProvider(),
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "claude": AnthropicProvider(),
            "openrouter": OpenRouterProvider(),
            "groq": GroqProvider(),
            "ollama": OllamaProvider(),
        }

    def get_configured_providers(self) -> List[str]:
        """Return list of provider names that have active credentials."""
        configured = ["demo"]
        for name, p in self.providers.items():
            if name != "demo" and p.is_configured() and name not in configured:
                configured.append(p.name)
        return list(set(configured))

    def has_any_live_provider(self) -> bool:
        """Check if at least one live provider has credentials configured."""
        return any(p.is_configured() for name, p in self.providers.items() if name != "demo")

    def resolve_provider(self, requested_provider: Optional[str] = None, model: Optional[str] = None) -> AIProvider:
        """Resolve the appropriate provider instance, honoring DEMO_MODE and fallback."""
        if is_demo_mode_forced():
            return self.demo_provider

        # Auto-detect from model name if provider not specified
        prov_key = (requested_provider or "").lower()
        if not prov_key and model:
            m_lower = model.lower()
            if "gemini" in m_lower or "gemma" in m_lower:
                prov_key = "google"
            elif "claude" in m_lower or "anthropic" in m_lower:
                prov_key = "anthropic"
            elif "gpt" in m_lower or "o1" in m_lower or "o3" in m_lower or "openai" in m_lower:
                prov_key = "openai"
            elif "groq" in m_lower:
                prov_key = "groq"
            elif "openrouter" in m_lower or "/" in m_lower:
                prov_key = "openrouter"
            elif "ollama" in m_lower or "local" in m_lower:
                prov_key = "ollama"

        provider = self.providers.get(prov_key)
        if provider and provider.is_configured():
            return provider

        # If requested provider is not configured, fall back to DemoProvider
        logger.info(f"Provider '{prov_key}' not configured. Falling back to MultiVision DemoProvider.")
        return self.demo_provider

    async def chat(self, request: ProviderRequest, provider_hint: Optional[str] = None) -> ProviderResponse:
        """Execute chat using the resolved provider."""
        prov = self.resolve_provider(provider_hint, request.model)
        try:
            return await prov.chat(request)
        except Exception as e:
            logger.warning(f"Provider {prov.name} failed ({e}). Falling back to DemoProvider.")
            return await self.demo_provider.chat(request)

    async def chat_stream(self, request: ProviderRequest, provider_hint: Optional[str] = None) -> AsyncIterator[ProviderChunk]:
        """Execute streaming chat using the resolved provider."""
        prov = self.resolve_provider(provider_hint, request.model)
        try:
            async for chunk in prov.chat_stream(request):
                yield chunk
        except Exception as e:
            logger.warning(f"Provider {prov.name} stream failed ({e}). Streaming from DemoProvider.")
            async for chunk in self.demo_provider.chat_stream(request):
                yield chunk


# Global Manager Singleton
_provider_manager = ProviderManager()


def get_provider_manager() -> ProviderManager:
    return _provider_manager
