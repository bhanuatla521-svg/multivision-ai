# tests/test_multivision_providers.py
"""Automated unit tests for MultiVision AI Provider Layer."""

import pytest
from src.multivision.providers.base import ProviderRequest, ProviderMessage
from src.multivision.providers.demo import DemoProvider
from src.multivision.providers.manager import ProviderManager, get_provider_manager


@pytest.mark.asyncio
async def test_demo_provider_chat():
    provider = DemoProvider()
    assert provider.is_configured() is True
    assert provider.is_demo is True

    req = ProviderRequest(
        model="gemini-2.5-flash",
        messages=[ProviderMessage(role="user", content="Hello MultiVision AI!")]
    )
    resp = await provider.chat(req)

    assert resp.provider == "demo"
    assert resp.is_demo is True
    assert "[DEMO MODE]" in resp.content
    assert "MultiVision" in resp.content


@pytest.mark.asyncio
async def test_demo_provider_multimodal_vision():
    provider = DemoProvider()
    req = ProviderRequest(
        model="gemini-2.5-flash",
        messages=[ProviderMessage(role="user", content="Analyze this architecture diagram image")],
        modalities=["image"]
    )
    resp = await provider.chat(req)

    assert resp.is_demo is True
    assert "Multimodal Vision Analysis" in resp.content


@pytest.mark.asyncio
async def test_demo_provider_streaming():
    provider = DemoProvider()
    req = ProviderRequest(
        model="gemini-2.5-flash",
        messages=[ProviderMessage(role="user", content="Write a python function to route models")]
    )
    chunks = []
    async for chunk in provider.chat_stream(req):
        chunks.append(chunk.delta)

    full_text = "".join(chunks)
    assert len(full_text) > 20
    assert "[DEMO MODE]" in full_text


def test_provider_manager_fallback():
    mgr = ProviderManager()
    resolved = mgr.resolve_provider(requested_provider="unknown-provider", model="non-existent-model")
    assert resolved.is_demo is True
    assert resolved.name == "demo"
