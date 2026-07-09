"""Small text helpers used by scoring (and feed parsing)."""
from __future__ import annotations

import re


def parse_count(raw: str) -> int:
    """'1,234' / '2.1K' / '1M' -> int."""
    raw = (raw or "").strip().upper().replace(",", "").replace(" ", "")
    m = re.match(r"([\d.]+)\s*([KM]?)", raw)
    if not m:
        return 0
    return int(float(m.group(1)) * {"": 1, "K": 1_000, "M": 1_000_000}[m.group(2)])
