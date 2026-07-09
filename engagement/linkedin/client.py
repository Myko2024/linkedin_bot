"""What to DO on LinkedIn: sign in, read + like the feed, fetch author context.

The high-level actions, expressed via a generic `Browser`. The site-specific
details it depends on are split out: selectors (`selectors.py`), the in-page
scrapers (`scripts.py`), and raw->Post parsing (`parsing.py`).
"""
from __future__ import annotations

import sys
from typing import Callable

from ..browser import Browser
from ..models import Post
from .parsing import post_from_raw, post_key
from .scripts import POST_FROM_BTN_JS, PROFILE_CONTEXT_JS
from .selectors import (
    FEED_READY_SEL,
    LOGGED_IN_SEL,
    LOGIN_FORM_SEL,
    REACT_BTN,
)


class LinkedIn:
    """High-level LinkedIn actions, expressed via a generic Browser."""

    def __init__(self, browser: Browser, feed_url: str):
        self.browser = browser
        self.feed_url = feed_url

    async def ensure_logged_in(self) -> None:
        """Detect login via obfuscation-proof signals (composer / feed container),
        never a churny post class. On first run, wait for a manual login."""
        await self.browser.goto(self.feed_url)
        if await self.browser.wait_for(LOGGED_IN_SEL, timeout=12_000):
            return
        # feed may just be slow: treat "no login form + not on a login URL" as OK
        no_form = await self.browser.count(LOGIN_FORM_SEL) == 0
        if no_form and "login" not in self.browser.url and "authwall" not in self.browser.url:
            return
        print(">> Not logged in. Log in manually in the browser window "
              "(you have 5 minutes). The session will be saved for next runs.",
              file=sys.stderr)
        await self.browser.wait_for(FEED_READY_SEL, timeout=300_000)

    async def read_and_engage(self, *, top_n: int, like_min_score: float,
                              dry_run: bool,
                              score_fn: Callable[[Post], float]) -> list[Post]:
        """Single scroll pass that reads, scores, AND likes inline.

        Liking happens while a post's Like button is in the (virtualized) DOM, so
        there's no fragile re-location step -- the fix for feeds that reshuffle on
        scroll. A post is liked when `score_fn(post) >= like_min_score`, capped at
        `top_n`. Real clicks, each verified by re-reading the button state. A
        transient not-actionable button is retried on a later pass, not failed.
        Returns every post seen (with .score and .outcome filled in)."""
        collected: dict[str, Post] = {}
        attempts: dict[str, int] = {}
        liked = 0
        stagnant = 0
        await self.browser.scroll_to_top()
        await self.browser.pause(0.6, 1.2)
        for _ in range(40):
            before = len(collected)
            for loc in await self.browser.find_all(REACT_BTN):
                if liked >= top_n:
                    break
                raw = await self.browser.eval_on(loc, POST_FROM_BTN_JS)
                if not raw or not raw.get("text"):
                    continue  # image/reshare with no commentary -- nothing to judge
                key = post_key(raw["href"], raw["text"])
                post = collected.get(key)
                if post is None:
                    post = post_from_raw(raw)
                    post.score = score_fn(post)
                    collected[key] = post
                if post.outcome != "-" or post.score < like_min_score:
                    continue
                res = await self._try_like(loc, dry_run)
                if res == "RETRY":
                    attempts[key] = attempts.get(key, 0) + 1
                    if attempts[key] >= 5:
                        post.outcome = "FAILED (never actionable)"
                    continue
                post.outcome = res
                if res in ("LIKED", "DRY-RUN (would like)"):
                    liked += 1
            if liked >= top_n:
                break
            await self.browser.scroll_step()
            await self.browser.pause(1.0, 1.8)
            stagnant = stagnant + 1 if len(collected) == before else 0
            if stagnant >= 4:  # feed exhausted ("You're all caught up")
                break
        return list(collected.values())

    async def _try_like(self, loc, dry_run: bool) -> str:
        """Verified Like on one reaction button. 'RETRY' == transient (off-screen
        / covered / detached) -> caller leaves it for a later pass; only a landed
        click that doesn't flip the state is a hard FAILED."""
        label = (await self.browser.attr(loc, "aria-label")) or ""
        if "no reaction" not in label.lower():
            return "SKIPPED (already liked)"
        if dry_run:
            return "DRY-RUN (would like)"
        if not await self.browser.click(loc):
            return "RETRY"
        await self.browser.pause(0.8, 1.6)
        after = (await self.browser.attr(loc, "aria-label")) or ""
        return "LIKED" if "no reaction" not in after.lower() else "FAILED (state did not change)"

    async def fetch_author_context(self, url: str) -> str:
        """Level 3: best-effort profile context (name from <title>, headline from
        the top card). Returns a short blob for the comment prompt, or ''."""
        data = await self.browser.scrape_tab(url, PROFILE_CONTEXT_JS) or {}
        title, headline = (data.get("title") or "").strip(), (data.get("headline") or "").strip()
        parts = [x for x in (f"Name/title: {title}" if title else "",
                             f"Headline: {headline}" if headline else "") if x]
        return "\n".join(parts)
