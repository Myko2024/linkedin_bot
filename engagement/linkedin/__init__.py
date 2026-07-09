"""LinkedIn domain layer: what to DO on the site (login / read+like / profile).

Owns every LinkedIn-specific detail -- selectors, in-page JS, the meaning of a
"Like" -- and drives the site through a generic `Browser`.
"""
from __future__ import annotations

from .client import LinkedIn

__all__ = ["LinkedIn"]
