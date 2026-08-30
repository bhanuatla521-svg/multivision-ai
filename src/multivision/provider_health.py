# src/multivision/provider_health.py
"""Provider Health Monitoring, Status Code Classification, and API Key Masking."""

import os
import time
import logging
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ProviderStatus(str, Enum):
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    RATE_LIMITED = "RATE_LIMITED"
    UNAVAILABLE = "UNAVAILABLE"
    INVALID_KEY = "INVALID_KEY"
    UNKNOWN = "UNKNOWN"


class KeyStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"


class ProviderHealthRecord(BaseModel):
    provider: str
    display_name: str
    status: ProviderStatus = ProviderStatus.UNKNOWN
    key_configured: bool = False
    key_status: KeyStatus = KeyStatus.UNKNOWN
    masked_key: Optional[str] = None
    last_status_code: Optional[int] = None
    last_error_message: Optional[str] = None
    last_checked: float = 0.0
    consecutive_failures: int = 0
    requests_today: int = 0
    errors_today: int = 0
    estimated_cost_today: float = 0.0


# In-memory tracking
_HEALTH_RECORDS: Dict[str, ProviderHealthRecord] = {}


def mask_api_key(key: Optional[str]) -> str:
    """Safely mask API key for display without exposing secrets.
    Example: AIzaSyD...9k2a or sk-or-v1-...abcd
    """
    if not key or not isinstance(key, str):
        return "None"
    k = key.strip()
    if len(k) <= 8:
        return "****"
    if k.startswith("AIza"):
        return f"{k[:7]}...{k[-4:]}"
    if k.startswith("sk-or-v1-"):
        return f"{k[:11]}...{k[-4:]}"
    if k.startswith("sk-"):
        return f"{k[:5]}...{k[-4:]}"
    if k.startswith("gsk_"):
        return f"{k[:6]}...{k[-4:]}"
    return f"{k[:4]}...{k[-4:]}"


def classify_http_error(status_code: int, error_text: str = "") -> tuple[ProviderStatus, str]:
    """Correctly interpret HTTP status codes according to project resilience rules.
    - 503: Temporary upstream server/model availability or overload. Never an invalid key.
    - 429: Rate limit / quota exceeded.
    - 401/403: Authentication or permission error.
    - 400: Invalid request / model parameters / bad input.
    - 408 / 504: Timeout / gateway timeout.
    - 500 / 502: Upstream gateway or internal server failure.
    """
    low_text = error_text.lower()
    
    if status_code == 503:
        return ProviderStatus.UNAVAILABLE, "503 Upstream Service Temporarily Unavailable / Overloaded"
    elif status_code == 429:
        return ProviderStatus.RATE_LIMITED, "429 Rate Limit / Quota Exceeded"
    elif status_code in (401, 403):
        if "quota" in low_text or "exceeded" in low_text:
            return ProviderStatus.RATE_LIMITED, f"{status_code} Quota/Permission Limit Exceeded"
        return ProviderStatus.INVALID_KEY, f"{status_code} Authentication / Invalid API Key"
    elif status_code == 400:
        return ProviderStatus.DEGRADED, "400 Invalid Request / Model Parameter Error"
    elif status_code in (408, 504):
        return ProviderStatus.DEGRADED, f"{status_code} Request Timeout"
    elif status_code in (500, 502):
        return ProviderStatus.DEGRADED, f"{status_code} Upstream Server Error"
    
    return ProviderStatus.DEGRADED, f"HTTP {status_code} Error"


def record_provider_event(
    provider: str,
    status_code: int = 200,
    error_message: Optional[str] = None,
    latency: float = 0.0,
    cost: float = 0.0
) -> None:
    """Record an API request event for a provider to update health and metrics."""
    p_key = provider.lower().strip()
    rec = get_provider_health(p_key)
    rec.last_checked = time.time()
    rec.requests_today += 1
    rec.estimated_cost_today += cost

    if 200 <= status_code < 300:
        rec.status = ProviderStatus.ONLINE
        rec.key_status = KeyStatus.VALID
        rec.consecutive_failures = 0
        rec.last_status_code = status_code
        rec.last_error_message = None
    else:
        rec.errors_today += 1
        rec.consecutive_failures += 1
        rec.last_status_code = status_code
        rec.last_error_message = error_message or f"HTTP {status_code}"
        
        new_status, _ = classify_http_error(status_code, error_message or "")
        rec.status = new_status
        if new_status == ProviderStatus.INVALID_KEY:
            rec.key_status = KeyStatus.INVALID


def get_provider_health(provider_name: str) -> ProviderHealthRecord:
    """Retrieve or initialize health record for a provider."""
    p_key = provider_name.lower().strip()
    if p_key not in _HEALTH_RECORDS:
        display_names = {
            "google": "Google Gemini / AI Studio",
            "openrouter": "OpenRouter",
            "groq": "Groq",
            "ollama": "Ollama (Local)",
            "openai": "OpenAI",
            "anthropic": "Anthropic"
        }
        
        # Check env keys
        raw_key = None
        if p_key == "google":
            raw_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("PALM_API_KEY")
        elif p_key == "openrouter":
            raw_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_KEY")
        elif p_key == "groq":
            raw_key = os.getenv("GROQ_API_KEY")
        elif p_key == "openai":
            raw_key = os.getenv("OPENAI_API_KEY")
        elif p_key == "anthropic":
            raw_key = os.getenv("ANTHROPIC_API_KEY")
        elif p_key == "ollama":
            raw_key = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        is_configured = bool(raw_key)
        _HEALTH_RECORDS[p_key] = ProviderHealthRecord(
            provider=p_key,
            display_name=display_names.get(p_key, p_key.title()),
            status=ProviderStatus.ONLINE if is_configured else ProviderStatus.UNKNOWN,
            key_configured=is_configured,
            key_status=KeyStatus.UNKNOWN if is_configured else KeyStatus.MISSING,
            masked_key=mask_api_key(raw_key) if (raw_key and p_key != "ollama") else ("Local URL" if p_key == "ollama" else "None"),
            last_checked=time.time()
        )
    
    return _HEALTH_RECORDS[p_key]


def list_all_provider_health() -> List[ProviderHealthRecord]:
    """List health status of all primary providers."""
    providers = ["google", "openrouter", "groq", "ollama"]
    return [get_provider_health(p) for p in providers]
