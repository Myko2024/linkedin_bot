"""Scoring layer: the pure "is this post interesting?" rule."""
from __future__ import annotations

from .rules import score_post
from .text import parse_count

__all__ = ["score_post", "parse_count"]
