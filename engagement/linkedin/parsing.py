"""Turn the raw dicts returned by the in-page scrapers into `Post` objects."""
from __future__ import annotations

from ..models import Post
from ..scoring import parse_count


def post_key(profile_url: str | None, text: str) -> str:
    """Dedup id for a feed post: profile url + a slice of its text."""
    return f"{profile_url or ''}|{text[:60]}"


def post_from_raw(raw: dict) -> Post:
    """Build a `Post` from one `POST_FROM_BTN_JS` result."""
    return Post(
        author=raw["author"] or "(unknown)",
        author_sub=raw.get("sub", ""),
        text=raw["text"],
        reactions=parse_count(raw["reactions"]),
        promoted=raw["promoted"],
        profile_url=raw["href"],
        key=post_key(raw["href"], raw["text"]),
        reacted=raw["reacted"],
    )
