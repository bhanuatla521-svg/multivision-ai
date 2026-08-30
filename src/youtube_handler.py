"""Compatibility wrapper for the canonical services.youtube.youtube_handler module.

MultiVision uses services.youtube for centralized transcript and comment analysis.
"""

import importlib
import sys

# Import the canonical module directly (services.youtube.youtube_handler)
# without triggering the heavy services/__init__.py top-level imports.
_youtube_handler = importlib.import_module("services.youtube.youtube_handler")

sys.modules[__name__] = _youtube_handler
