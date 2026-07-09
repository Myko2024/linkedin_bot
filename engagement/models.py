"""Plain data types shared across layers."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Post:
    """One feed post, plus everything we compute/decide about it."""
    author: str
    author_sub: str                 # the grey headline line under the name
    text: str
    reactions: int
    promoted: bool
    profile_url: str | None
    key: str = ""                   # dedup id: profile_url + text[:60]
    reacted: bool = False           # already liked before we ran
    score: float = 0.0              # filled by scoring
    outcome: str = "-"              # filled by the like step (LIKED / SKIPPED / ...)
    author_context: str = ""        # filled by the Level-3 profile visit
    comment: str = ""               # filled by the AI draft (Level 2/3)
