# src/multivision/media_providers.py
"""MultiVision AI Media Generation Providers & Capability Layer."""

import os
import base64
import time
import uuid
import logging
from typing import Dict, Any, Optional
from src.media_helpers import save_media

logger = logging.getLogger(__name__)


def generate_demo_svg_image(prompt: str) -> bytes:
    """Generate a clean, modern SVG banner image preview for demo mode."""
    safe_prompt = prompt.replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")[:60]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#181614"/>
      <stop offset="50%" stop-color="#282421"/>
      <stop offset="100%" stop-color="#1f1d1a"/>
    </linearGradient>
    <linearGradient id="accentGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#d97757"/>
      <stop offset="100%" stop-color="#e08465"/>
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="8" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>
  <rect width="800" height="600" fill="url(#bgGrad)" rx="16"/>
  <circle cx="400" cy="240" r="120" fill="url(#accentGrad)" opacity="0.15" filter="url(#glow)"/>
  <circle cx="400" cy="240" r="60" fill="none" stroke="#d97757" stroke-width="3"/>
  <path d="M370 240 L430 240 M400 210 L400 270" stroke="#ede8e3" stroke-width="3" stroke-linecap="round"/>
  <text x="400" y="380" font-family="system-ui, -apple-system, sans-serif" font-size="22" font-weight="700" fill="#ede8e3" text-anchor="middle">MultiVision AI — Media Studio</text>
  <text x="400" y="415" font-family="system-ui, -apple-system, sans-serif" font-size="15" font-weight="500" fill="#d97757" text-anchor="middle">[DEMO PREVIEW]</text>
  <text x="400" y="455" font-family="monospace" font-size="13" fill="#b8b0a6" text-anchor="middle">Prompt: &quot;{safe_prompt}&quot;</text>
  <rect x="250" y="490" width="300" height="34" rx="17" fill="rgba(217, 119, 87, 0.12)" stroke="rgba(217, 119, 87, 0.35)" stroke-width="1"/>
  <text x="400" y="512" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="600" fill="#ede8e3" text-anchor="middle">Configure HF/NVIDIA key for live generation</text>
</svg>"""
    return svg.encode("utf-8")


class ImageGenerationProvider:
    """Capability layer for Image Generation."""

    @staticmethod
    def is_available() -> bool:
        return bool(
            os.getenv("NVIDIA_API_KEY") or
            os.getenv("HF_API_KEY") or
            os.getenv("HUGGINGFACE_API_KEY") or
            os.getenv("STABILITY_API_KEY")
        )

    @staticmethod
    def generate(prompt: str, is_demo: bool = False) -> Dict[str, Any]:
        """Generate an image or return demo preview with clear status."""
        nvidia_key = os.getenv("NVIDIA_API_KEY")
        hf_key = os.getenv("HF_API_KEY") or os.getenv("HUGGINGFACE_API_KEY")
        from src.multivision.providers.manager import is_demo_mode_forced

        if not is_demo and not is_demo_mode_forced() and nvidia_key:
            try:
                from src.nvidia_image_helper import generate_image
                filename = generate_image(prompt)
                return {
                    "status": "success",
                    "filename": filename,
                    "url": f"/api/generated-images/{filename}",
                    "provider": "nvidia",
                    "is_demo": False
                }
            except Exception as e:
                logger.warning(f"Live NVIDIA image generation failed: {e}. Falling back to Demo Preview.")

        # Demo Preview fallback
        img_bytes = generate_demo_svg_image(prompt)
        filename = save_media(img_bytes, ext=".svg", prefix="demo_img_")
        return {
            "status": "demo",
            "filename": filename,
            "url": f"/api/generated-images/{filename}",
            "provider": "demo",
            "is_demo": True,
            "message": "Image generation is currently in Demo Mode. Configure NVIDIA_API_KEY or HF_API_KEY for live generation."
        }
