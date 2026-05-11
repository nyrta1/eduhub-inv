from __future__ import annotations

import re
from decimal import Decimal

# Safe printable slug / code tokens for academic identifiers (no Unicode tricks).
SAFE_CODE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def clamp_pagination(skip: int, limit: int, *, max_limit: int = 200) -> tuple[int, int]:
    if skip < 0:
        skip = 0
    if limit < 1:
        limit = 1
    if limit > max_limit:
        limit = max_limit
    return skip, limit


def validate_score_range(score: Decimal) -> Decimal:
    if score < 0 or score > 100:
        raise ValueError("Score must be between 0 and 100.")
    return score


def sanitize_filename_component(name: str, *, max_length: int = 120) -> str:
    """
    Reduce path traversal / control characters for future upload pipelines.

    Returns a basename-safe fragment; callers still MUST validate MIME and scan content.
    """
    base = name.replace("\\", "/").split("/")[-1]
    cleaned = "".join(c for c in base if c.isalnum() or c in "._-")
    cleaned = cleaned.strip("._") or "file"
    return cleaned[:max_length]
