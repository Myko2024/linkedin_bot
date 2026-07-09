#!/usr/bin/env python3
"""Offline verification for the pure/decomposed logic -- no LinkedIn, no API key.

Run: python test_logic.py
Covers scoring (scoring.py), the AI prompt shape + a mocked draft (ai.py), so the
core decision logic is tested without a browser or a live Anthropic call.
"""
from __future__ import annotations

import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock

from engagement.ai import CommentWriter
from engagement.models import Post
from engagement import scoring

INTERESTS = ["python", "backend", "fastapi", "postgres", "ai", "llm", "rag", "agents", "aws"]
PERSONA = "Senior backend Python engineer building LLM agent systems."
MODEL = "claude-sonnet-4-6"


def check(name: str, got, want) -> bool:
    ok = got == want
    print(f"  [{'ok' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")
    return ok


def _post(**kw) -> Post:
    base = dict(author="A", author_sub="", text="", reactions=0,
                promoted=False, profile_url=None)
    base.update(kw)
    return Post(**base)


def test_parse_count() -> bool:
    print("parse_count:")
    cases = [("", 0), ("0", 0), ("1,234", 1234), ("2.1K", 2100), ("3K", 3000),
             ("1M", 1_000_000), ("1.5M", 1_500_000), (" 12 ", 12), ("garbage", 0)]
    return all(check(f"parse_count({raw!r})", scoring.parse_count(raw), want)
               for raw, want in cases)


def _score(p: Post) -> float:
    return scoring.score_post(p, INTERESTS)


def test_score_post() -> bool:
    print("score_post:")
    ok = True
    ok &= check("promoted", _score(_post(promoted=True, text="python backend " * 50)), -100.0)
    good = _score(_post(text=("Rethinking our FastAPI + postgres RAG pipeline. "
                              "We moved embeddings to pgvector and cut latency. " * 8),
                        reactions=120))
    bait = _score(_post(text="Agree?", reactions=5000))
    print(f"    substantive={good}  bait={bait}")
    ok &= check("substantive > bait", good > bait, True)
    ok &= check("short penalty applied", _score(_post(text="short")) < 0, True)
    stuffed = _score(_post(text=" ".join(INTERESTS * 20)))
    ok &= check("affinity capped", stuffed < 12, True)
    bait_text = ("Say goodbye to your 9 to 5. Here are 5 sites paying in USD 👇 "
                 "https://a.co https://b.co 100% FREE, comment below! " * 4)
    real_text = ("We replaced Celery with a Postgres job table using SELECT FOR "
                 "UPDATE SKIP LOCKED and got exactly-once semantics. " * 4)
    b, r = _score(_post(text=bait_text, reactions=500)), _score(_post(text=real_text, reactions=50))
    print(f"    bait={b}  real={r}")
    ok &= check("bait demoted below real post", r > b, True)
    return bool(ok)


def test_comment_writer() -> bool:
    print("CommentWriter:")
    ok = True
    ok &= check("no key -> disabled", CommentWriter(None, MODEL, PERSONA).enabled, False)
    ok &= check("placeholder -> disabled", CommentWriter("sk-ant-...", MODEL, PERSONA).enabled, False)
    ok &= check("real key -> enabled", CommentWriter("sk-ant-real", MODEL, PERSONA).enabled, True)

    writer = CommentWriter("sk-ant-real", MODEL, PERSONA)
    post = _post(author="Dana", author_sub="Staff Eng", text="We cut RAG latency with pgvector.",
                 author_context="Headline: Staff Eng at Foo")
    system, user = writer.build_prompt(post)
    ok &= check("system has ghost-write rule", "ghost-write" in system, True)
    ok &= check("persona interpolated", PERSONA in system, True)
    ok &= check("post text in user msg", "pgvector" in user, True)
    ok &= check("author context in user msg", "Foo" in user, True)

    # mock the Anthropic client so draft() makes no network call
    block = MagicMock(); block.text = "  moving embeddings to pgvector is the move  "
    msg = MagicMock(); msg.content = [block]
    writer._client = MagicMock()
    writer._client.messages.create = AsyncMock(return_value=msg)
    out = asyncio.run(writer.draft(post))
    ok &= check("draft stripped", out, "moving embeddings to pgvector is the move")
    kwargs = writer._client.messages.create.call_args.kwargs
    ok &= check("model passed", kwargs["model"], MODEL)
    ok &= check("system passed", "ghost-write" in kwargs["system"], True)
    ok &= check("post in messages", "pgvector" in kwargs["messages"][0]["content"], True)
    return bool(ok)


if __name__ == "__main__":
    results = [test_parse_count(), test_score_post(), test_comment_writer()]
    print()
    print("ALL LOGIC TESTS PASSED" if all(results) else "SOME TESTS FAILED")
    sys.exit(0 if all(results) else 1)
