"""AI comment generation (Anthropic).

Owns the API call and key handling. The prompt itself lives in `prompts.py`;
`build_prompt` is re-exposed here so the manager can print it verbatim in
"assistant mode" (no key) for you to paste into whatever AI assistant you use --
the task allows "any AI assistant you actually use".
"""
from __future__ import annotations

from ..models import Post
from .prompts import build_prompt


class CommentWriter:
    def __init__(self, api_key: str | None, model: str, persona: str):
        # a bare placeholder counts as "no key"
        self._api_key = api_key if (api_key and api_key != "sk-ant-...") else None
        self.model = model
        self.persona = persona
        self._client = None

    @property
    def enabled(self) -> bool:
        """Whether we can draft automatically (a usable key is configured)."""
        return self._api_key is not None

    def build_prompt(self, post: Post) -> tuple[str, str]:
        """The exact (system, user) prompt used to draft a comment."""
        return build_prompt(post, self.persona)

    async def draft(self, post: Post) -> str:
        """Draft one comment via the Anthropic API. Raises on API error."""
        if self._client is None:
            from anthropic import AsyncAnthropic  # lazy: Level 1 runs without it
            self._client = AsyncAnthropic(api_key=self._api_key)
        system, user = self.build_prompt(post)
        msg = await self._client.messages.create(
            model=self.model,
            max_tokens=200,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text.strip()
