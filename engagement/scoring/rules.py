"""The "interesting" rule -- pure functions, no I/O, easy to unit-test."""
from __future__ import annotations

import math

from ..models import Post

# Engagement-bait markers: long-but-worthless posts that would otherwise win on
# length alone (link-dump listicles, CTA spam, arrow-bait).
_BAIT = ("100% free", "comment below", "dm me", "link in bio", "in my bio",
         "say goodbye to your", "follow me", "tag someone", "repost this",
         "here are 5 ", "here are 7 ", "👇", "⤵")


def score_post(p: Post, interests: list[str]) -> float:
    """My rule for 'interesting', in priority order:

    1. Never engage ads (promoted -> disqualified).
    2. Substance: longer original text usually means a real thought, not a repost
       caption. Capped so essays don't win on length alone.
    3. Relevance: keyword affinity with my interests (capped at 3 so keyword
       stuffing can't game it).
    4. Signal: log of reaction count -- some social proof, log-scaled so a viral
       one-liner can't outrank a substantive niche post.
    5. Penalise sub-120-char one-liners (usually bait / link drops).
    6. Penalise engagement-bait (link-dump listicles, "100% FREE", arrow-bait).
    """
    if p.promoted:
        return -100.0
    text_l = p.text.lower()
    substance = min(len(p.text), 900) / 900 * 3.0
    affinity = 2.0 * min(sum(k in text_l for k in interests), 3)
    signal = 0.6 * math.log1p(p.reactions)
    short_penalty = -1.5 if len(p.text) < 120 else 0.0
    link_penalty = -2.5 if text_l.count("http") >= 2 else 0.0
    bait_penalty = -3.0 if any(b in text_l for b in _BAIT) else 0.0
    return round(substance + affinity + signal + short_penalty
                 + link_penalty + bait_penalty, 2)
