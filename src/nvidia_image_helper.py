import os
import requests
import base64
from .media_helpers import save_media

NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY')
INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

def generate_image(prompt: str) -> str:
    """Generate an image via NVIDIA API and return saved filename.

    The request mirrors the video generation but expects a base64‑encoded image in
    the ``image_base64`` field of the response.
    """
    if not NVIDIA_API_KEY:
        raise RuntimeError("NVIDIA_API_KEY not configured in environment")

    payload = {
        "model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048,
        "temperature": 0.8,
        "top_p": 0.95,
        "stream": False,
    }

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Accept": "application/json",
    }

    response = requests.post(INVOKE_URL, headers=headers, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    img_b64 = data.get("image_base64")
    if not img_b64:
        raise RuntimeError("NVIDIA response missing 'image_base64' field")
    img_bytes = base64.b64decode(img_b64)
    filename = save_media(img_bytes, ext=".png", prefix="img_")
    return filename
