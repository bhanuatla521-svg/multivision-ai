# tests/test_multivision_health_api.py
"""Automated API integration tests for MultiVision health, models, and chat endpoints."""

import pytest
from fastapi.testclient import TestClient
from app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoints(client):
    r1 = client.get("/health")
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["status"] == "ok"
    assert data1["service"] == "multivision-api"
    assert data1["product"] == "MultiVision AI"

    r2 = client.get("/api/health")
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["status"] == "ok"


def test_multivision_models_catalog(client):
    r = client.get("/api/multivision/models")
    assert r.status_code == 200
    data = r.json()
    assert "models" in data
    assert len(data["models"]) >= 10

    # Ensure key catalog models are present
    model_ids = [m["model_id"] for m in data["models"]]
    assert any("gemini" in mid for mid in model_ids)
    assert any("claude" in mid for mid in model_ids)
    assert any("gpt-4o" in mid for mid in model_ids)


def test_multivision_chat_api(client):
    payload = {
        "prompt": "Explain how multi-model routing works in MultiVision AI",
        "model": "gemini-2.5-flash",
        "modalities": ["text"]
    }
    r = client.post("/api/multivision/chat", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "content" in data
    assert len(data["content"]) > 0


def test_multivision_generate_image_demo(client):
    payload = {"prompt": "Futuristic control center dashboard"}
    r = client.post("/api/multivision/generate-image", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "url" in data
    assert "filename" in data
