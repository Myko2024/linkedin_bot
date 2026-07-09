"""The comment prompt: the system template and how a post becomes a user message.

Kept separate from the API client (`writer.py`) so the prompt can be built and
inspected without any Anthropic dependency -- the manager prints it verbatim in
"assistant mode" when no key is configured.
"""
from __future__ import annotations

from ..models import Post

COMMENT_SYSTEM = """You ghost-write LinkedIn comments for me. Hard rules:
- 1-2 sentences, under 40 words total.
- React to ONE concrete point in the post; add a specific thought,
  experience, or sharp question of my own. Never summarise the post back.
- Banned: praise openers ("Great post", "Love this"), emojis, hashtags,
  em-dashes, "As a...", "This resonates", rhetorical fluff.
- Voice: a busy engineer typing quickly. Plain words, contractions ok,
  mild imperfection ok. It must not smell like AI.
My background: {persona}
Reply with the comment text only."""


def build_prompt(post: Post, persona: str) -> tuple[str, str]:
    """The exact (system, user) prompt used to draft a comment for `post`."""
    user = f"Post by {post.author} ({post.author_sub}):\n{post.text[:1500]}"
    if post.author_context:
        user += (
            f"\n\nAuthor profile context (use it to make the comment more "
            f"specific to them, without being creepy):\n{post.author_context}"
        )
    return COMMENT_SYSTEM.format(persona=persona), user
