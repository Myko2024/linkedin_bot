"""Env-driven configuration, loaded once at startup."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

_DEFAULT_PERSONA = (
    "Senior backend Python engineer (FastAPI, PostgreSQL, Redis, AWS) who also "
    "builds LLM agent systems with LangGraph, RAG and pgvector."
)
_DEFAULT_INTERESTS = "python,backend,fastapi,postgres,ai,llm,rag,agents,aws"


@dataclass
class Config:
    feed_url: str
    user_data_dir: str
    top_n: int                 # posts to like (Level 1)
    comment_n: int             # posts to draft comments for (Level 2)
    profile_aware: bool        # Level 3 toggle
    dry_run: bool              # score/print but never click Like
    like_min_score: float      # only like posts scoring above this
    model: str
    interests: list[str]
    persona: str
    anthropic_api_key: str | None

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        return cls(
            feed_url=os.getenv("FEED_URL", "https://www.linkedin.com/feed/"),
            user_data_dir=os.getenv("USER_DATA_DIR", "./user_data"),
            top_n=int(os.getenv("TOP_N", "5")),
            comment_n=int(os.getenv("COMMENT_N", "3")),
            profile_aware=os.getenv("PROFILE_AWARE", "1") == "1",
            dry_run=os.getenv("DRY_RUN", "0") == "1",
            like_min_score=float(os.getenv("LIKE_MIN_SCORE", "0")),
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            interests=[k.strip().lower()
                       for k in os.getenv("INTERESTS", _DEFAULT_INTERESTS).split(",")
                       if k.strip()],
            persona=os.getenv("PERSONA", _DEFAULT_PERSONA),
            anthropic_api_key=(os.getenv("ANTHROPIC_API_KEY") or None),
        )
