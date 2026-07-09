"""Generic browser automation layer (Playwright).

Knows nothing about LinkedIn -- just "how to drive a browser". Everything
site-specific lives in the `linkedin` package.
"""
from __future__ import annotations

from .driver import Browser

__all__ = ["Browser"]
