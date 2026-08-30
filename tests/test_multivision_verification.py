# tests/test_multivision_verification.py
import pytest
from starlette.testclient import TestClient
from app import app

client = TestClient(app)


def test_multivision_full_verification():
    # 1. Free mode
    r = client.get("/api/multivision/free-mode")
    assert r.status_code == 200
    assert "free_only" in r.json()

    # 2. Models Catalog
    r = client.get("/api/multivision/models")
    assert r.status_code == 200
    data = r.json()
    assert data.get("count", 0) > 0
    assert len(data.get("models", [])) > 0

    # 3. Providers Health & Key Masking
    r = client.get("/api/multivision/providers")
    assert r.status_code == 200
    providers = r.json().get("providers", [])
    assert len(providers) > 0
    for p in providers:
        assert "display_name" in p
        assert "status" in p
        assert "key_status" in p

    # 4. Best Model for Every Task
    r = client.get("/api/multivision/best-by-task")
    assert r.status_code == 200
    best_map = r.json().get("best_models", {})
    assert len(best_map) >= 5

    # 5. Recommendation Engine
    rec = client.post("/api/multivision/recommend", json={
        "task": "IMAGE_ANALYSIS",
        "modalities": ["image", "pdf", "text"]
    })
    assert rec.status_code == 200
    rec_json = rec.json()
    assert "recommended_model" in rec_json or "display_name" in rec_json

    # 6. Model Comparison (2-5 Models)
    cmp_res = client.post("/api/multivision/compare", json={
        "models": ["gemini-2.5-flash", "llama-3.3-70b-versatile", "meta-llama/llama-3.2-3b-instruct:free"]
    })
    assert cmp_res.status_code == 200
    assert len(cmp_res.json().get("comparison", [])) >= 2

    # 7. Unified Multimodal Router Analysis
    ana = client.post("/api/multivision/analyze", json={
        "prompt": "Analyze this diagram.png and policy.pdf to find the security flaw",
        "file_names": ["diagram.png", "policy.pdf"]
    })
    assert ana.status_code == 200
    ana_json = ana.json()
    assert "detected_task" in ana_json
    assert "selected_model" in ana_json

    # 8. AI Operations & Metrics
    ops = client.get("/api/multivision/operations")
    assert ops.status_code == 200
    ops_json = ops.json()
    assert "total_requests" in ops_json

    # 9. Report Export (Markdown)
    rep = client.get("/api/multivision/report?format=markdown")
    assert rep.status_code == 200
    assert len(rep.text) > 0

    # 10. Dashboard Route
    h = client.get("/ai-models")
    assert h.status_code == 200
    assert "MultiVision" in h.text or "Control Center" in h.text

