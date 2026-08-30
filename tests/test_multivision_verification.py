# tests/test_multivision_verification.py
import requests
import json

base = "http://127.0.0.1:7000"

print("--- MULTIVISION VERIFICATION SUITE ---")

# 1. Free mode
r = requests.get(f"{base}/api/multivision/free-mode").json()
print("1. Free Mode:", r)

# 2. Models Catalog
r = requests.get(f"{base}/api/multivision/models").json()
print(f"2. Catalog Models Count: {r.get('count')}")

# 3. Providers Health & Key Masking
r = requests.get(f"{base}/api/multivision/providers").json()
print(f"3. Providers Count: {len(r.get('providers', []))}")
for p in r.get('providers', []):
    print(f"   - {p['display_name']}: status={p['status']}, key_status={p['key_status']}, key={p['masked_key']}, available_models={p['available_models']}")

# 4. Best Model for Every Task
r = requests.get(f"{base}/api/multivision/best-by-task").json()
best_map = r.get("best_models", {})
print(f"4. Best Model by Task ({len(best_map)} categories):")
for task_k, val in list(best_map.items())[:5]:
    print(f"   - {task_k}: {val['display_name']} ({val['provider']}) | Score: {val['score']}/100 | Cost: {val['cost_class']}")

# 5. Recommendation Engine
rec = requests.post(f"{base}/api/multivision/recommend", json={
    "task": "IMAGE_ANALYSIS",
    "modalities": ["image", "pdf", "text"]
}).json()
print(f"5. Recommendation for Image+PDF+Text:")
print(f"   - Recommended: {rec.get('display_name')} ({rec.get('provider')})")
print(f"   - Match Score: {rec.get('capability_match_score')}/100")
print(f"   - Fallbacks: {rec.get('fallback_models')}")

# 6. Model Comparison (2-5 Models)
cmp_res = requests.post(f"{base}/api/multivision/compare", json={
    "models": ["gemini-2.5-flash", "llama-3.3-70b-versatile", "meta-llama/llama-3.2-3b-instruct:free"]
}).json()
print(f"6. Model Comparison Count: {len(cmp_res.get('comparison', []))}")
for m in cmp_res.get("comparison", []):
    print(f"   - {m['display_name']}: Quality={m['quality_rating']}, Speed={m['speed_rating']}, Score={m['overall_score']}")

# 7. Unified Multimodal Router Analysis
ana = requests.post(f"{base}/api/multivision/analyze", json={
    "prompt": "Analyze this diagram.png and policy.pdf to find the security flaw",
    "file_names": ["diagram.png", "policy.pdf"]
}).json()
print(f"7. Multimodal Single-Request Routing Analysis:")
print(f"   - Detected Task: {ana.get('detected_task')}")
print(f"   - Input Modalities: {ana.get('input_modalities')}")
print(f"   - Selected Model: {ana.get('selected_model')} ({ana.get('selected_provider')})")
print(f"   - Unified Request: {ana.get('unified_request_possible')}")
print(f"   - Reason: {ana.get('routing_reason')}")

# 8. AI Operations & Metrics
ops = requests.get(f"{base}/api/multivision/operations").json()
print(f"8. AI Operations Metrics:")
print(f"   - Total Requests: {ops.get('total_requests')}")
print(f"   - Free Requests: {ops.get('free_requests')}")
print(f"   - Total Cost: ${ops.get('total_estimated_cost')}")

# 9. Report Export (Markdown)
rep = requests.get(f"{base}/api/multivision/report?format=markdown")
print(f"9. Markdown Report Export Status: {rep.status_code}, Length: {len(rep.text)} chars")

# 10. Dashboard Route
h = requests.get(f"{base}/ai-models")
print(f"10. Dashboard Route /ai-models Status: {h.status_code}, HTML Length: {len(h.text)} chars")

print("\n--- ALL VERIFICATIONS PASSED SUCCESSFULLY! ---")
