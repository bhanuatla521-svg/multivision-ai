import os
import hashlib
import time
from pathlib import Path
from typing import List

from src.constants import GENERATED_IMAGES_DIR

# Base directory for generated media files (images, videos, documents)
BASE_MEDIA_DIR = Path(GENERATED_IMAGES_DIR)
BASE_MEDIA_DIR.mkdir(parents=True, exist_ok=True)

def _hash_content(content: bytes) -> str:
    """Return a short hash for the given bytes (used for unique filenames)."""
    return hashlib.sha256(content).hexdigest()[:12]

def save_media(content: bytes, ext: str, prefix: str = "") -> str:
    """Save binary content to the media directory and return the filename.

    The filename is ``{prefix}{hash}.{ext}``. If ``prefix`` is empty a hash‑only name is used.
    """
    if not ext.startswith('.'):
        ext = f'.{ext}'
    h = _hash_content(content + str(time.time()).encode())
    filename = f"{prefix}{h}{ext}"
    path = BASE_MEDIA_DIR / filename
    with open(path, 'wb') as f:
        f.write(content)
    return filename

def get_media_path(filename: str) -> Path:
    """Resolve a safe absolute path for a stored media file."""
    return BASE_MEDIA_DIR / filename

def cleanup_old_media(max_age_hours: int = 24) -> List[Path]:
    """Delete files older than ``max_age_hours`` and return list of deleted paths."""
    now = time.time()
    cutoff = now - max_age_hours * 3600
    deleted: List[Path] = []
    for p in BASE_MEDIA_DIR.iterdir():
        if p.is_file() and p.stat().st_mtime < cutoff:
            try:
                p.unlink()
                deleted.append(p)
            except Exception:
                pass
    return deleted
