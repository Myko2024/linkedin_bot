#!/usr/bin/env python3
"""
LinkedIn feed engagement prototype (test task) -- entrypoint.

Level 1: like the top-N most interesting feed posts
Level 2: draft (never post) human-sounding comments for the best 2-3
Level 3: enrich each comment with the author's profile context

The work is split into layers under engagement/ (see engagement/__init__.py):
  browser  -> generic Playwright wrapper (find / click / scroll / eval)
  linkedin -> what to do on LinkedIn (login / read+like / profile)
  ai       -> draft comments
  scoring  -> the "interesting" rule
  manager  -> orchestrate the above and print results

Auth: no credentials in code. First run opens a headful Chromium window; you log
in by hand and the session persists in ./user_data. Automated logins are the
fastest way to trip LinkedIn's bot detection, so we don't do them.
"""
from __future__ import annotations

import asyncio

from engagement.ai import CommentWriter
from engagement.browser import Browser
from engagement.config import Config
from engagement.linkedin import LinkedIn
from engagement.manager import EngagementManager


async def main() -> None:
    cfg = Config.from_env()
    async with Browser(cfg.user_data_dir) as browser:
        linkedin = LinkedIn(browser, feed_url=cfg.feed_url)
        writer = CommentWriter(cfg.anthropic_api_key, cfg.model, cfg.persona)
        await EngagementManager(cfg, linkedin, writer).run()


if __name__ == "__main__":
    asyncio.run(main())
