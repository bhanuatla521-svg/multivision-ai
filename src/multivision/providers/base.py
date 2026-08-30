# src/multivision/providers/base.py
"""Abstract base class for AI Providers in MultiVision AI."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncIterator
from pydantic import BaseModel, Field
import time


class ProviderMessage(BaseModel):
    role: str  # "system", "user", "assistant"
    content: Any  # str or structured list for multimodal parts
    name: Optional[str] = None


class ProviderRequest(BaseModel):
    model: str
    messages: List[ProviderMessage]
    temperature: float = 0.7
    max_tokens: Optional[int] = 4096
    stream: bool = False
    modalities: List[str] = ["text"]
    attachments: List[Dict[str, Any]] = []
    session_id: Optional[str] = None
    extra_params: Dict[str, Any] = Field(default_factory=dict)


class ProviderResponse(BaseModel):
    id: str
    model: str
    provider: str
    content: str
    role: str = "assistant"
    finish_reason: str = "stop"
    usage: Dict[str, int] = Field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
    is_demo: bool = False
    latency_ms: int = 0
    created_at: float = Field(default_factory=time.time)


class ProviderChunk(BaseModel):
    id: str
    model: str
    provider: str
    delta: str
    is_demo: bool = False
    finish_reason: Optional[str] = None


class AIProvider(ABC):
    """Abstract Base Class for all AI model providers."""

    def __init__(self, name: str, display_name: str, is_demo: bool = False):
        self.name = name
        self.display_name = display_name
        self.is_demo = is_demo

    @abstractmethod
    def is_configured(self) -> bool:
        """Check whether the provider has valid credentials/endpoint configured."""
        pass

    @abstractmethod
    async def chat(self, request: ProviderRequest) -> ProviderResponse:
        """Execute a synchronous chat completion."""
        pass

    @abstractmethod
    async def chat_stream(self, request: ProviderRequest) -> AsyncIterator[ProviderChunk]:
        """Execute a streaming chat completion."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Verify reachability and status of the provider."""
        pass
