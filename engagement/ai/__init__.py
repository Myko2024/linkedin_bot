"""AI layer: draft human-sounding LinkedIn comments (Anthropic)."""
from __future__ import annotations

from .prompts import COMMENT_SYSTEM, build_prompt
from .writer import CommentWriter

__all__ = ["CommentWriter", "COMMENT_SYSTEM", "build_prompt"]
