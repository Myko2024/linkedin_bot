"""Orchestration: wire LinkedIn + scoring + AI together and print the results.

This is the only layer that knows the three "levels" of the task and how they fit
together. It holds no Playwright, no selectors, and no API calls of its own.
"""
from __future__ import annotations

from .ai import CommentWriter
from .config import Config
from .linkedin import LinkedIn
from .models import Post
from .scoring import score_post


class EngagementManager:
    def __init__(self, config: Config, linkedin: LinkedIn, writer: CommentWriter):
        self.cfg = config
        self.li = linkedin
        self.writer = writer

    async def run(self) -> None:
        await self.li.ensure_logged_in()
        posts = await self.li.read_and_engage(
            top_n=self.cfg.top_n,
            like_min_score=self.cfg.like_min_score,
            dry_run=self.cfg.dry_run,
            score_fn=lambda p: score_post(p, self.cfg.interests),
        )
        self._print_level1(posts)
        if self.cfg.comment_n:
            await self._draft_comments(posts)

    # -- Level 1: read + react -------------------------------------------- #

    def _print_level1(self, posts: list[Post]) -> None:
        engaged = sorted((p for p in posts if p.outcome != "-"),
                         key=lambda p: p.score, reverse=True)
        liked_n = sum(1 for p in posts if p.outcome == "LIKED")
        verb = "would-like" if self.cfg.dry_run else "liked"
        extra = "" if self.cfg.dry_run else f" ({liked_n} newly liked)"
        print(f"\n=== Level 1: {verb} the top {len(engaged)} interesting "
              f"of {len(posts)} loaded posts{extra} ===")
        if not posts:
            print("(!) No posts found in the feed. If this is a new/sparse account, "
                  "follow more active accounts or set FEED_URL to a hashtag feed, "
                  "e.g. FEED_URL=https://www.linkedin.com/feed/hashtag/python/")
        for n, p in enumerate(engaged, 1):
            print(f"[{n:2}] {p.outcome:<28} score={p.score:<5} {p.author}")
            print(f"     {p.text[:200]}")

    # -- Levels 2 & 3: draft (never post) comments ------------------------ #

    async def _draft_comments(self, posts: list[Post]) -> None:
        top = sorted((p for p in posts if p.score > 0),
                     key=lambda p: p.score, reverse=True)[:self.cfg.comment_n]
        level = 3 if self.cfg.profile_aware else 2
        print(f"\n=== Level {level}: drafting comments (NOT posting) for top {len(top)} ===")
        if not self.writer.enabled:
            print("(!) No valid ANTHROPIC_API_KEY set -- 'assistant mode': the script "
                  "prints the exact prompt for each post so you can paste it into "
                  "whatever AI assistant you use. With a valid key it drafts itself.")
        for p in top:
            if self.cfg.profile_aware and p.profile_url:
                p.author_context = await self.li.fetch_author_context(p.profile_url)
            print(f"\n--- {p.author} (score {p.score}) ---")
            print(f"POST:     {p.text[:200]}")
            if p.author_sub:
                print(f"HEADLINE: {p.author_sub[:200]}")
            if p.author_context:
                print(f"CONTEXT:  {p.author_context[:200].replace(chr(10), ' | ')}")
            await self._emit_comment(p)

    async def _emit_comment(self, p: Post) -> None:
        _, prompt = self.writer.build_prompt(p)
        if self.writer.enabled:
            try:
                p.comment = await self.writer.draft(p)
                print(f"DRAFT:    {p.comment}")
                return
            except Exception as e:  # surface API errors (e.g. bad key) without dying
                print(f"DRAFT:    (API call failed: {type(e).__name__}: {e})")
        print("PROMPT (paste into your AI assistant):\n"
              + "\n".join("    " + ln for ln in prompt.splitlines()))
