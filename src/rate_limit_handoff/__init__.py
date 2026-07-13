"""
rate-limit-handoff
==================

Turn AI rate limits into high-quality checkpoints.

Schedule remaining work across Claude Code, OpenAI Codex, Grok Build,
Antigravity (agy), Cursor, Hermes and more. Automatically update your
Second Brain + living handoff.md so context never evaporates.
"""

__version__ = "0.2.1"
__author__ = "Purple Orange AI"

from .models import MODELS, ModelInfo
from .scheduler import LimitScheduler

__all__ = [
    "__version__",
    "MODELS",
    "ModelInfo",
    "LimitScheduler",
]
