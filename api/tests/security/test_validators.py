from __future__ import annotations

from decimal import Decimal

import pytest
from app.security.validators import (
    clamp_pagination,
    sanitize_filename_component,
    validate_score_range,
)


def test_clamp_pagination() -> None:
    assert clamp_pagination(-5, 999, max_limit=100) == (0, 100)


def test_sanitize_filename_traversal() -> None:
    assert sanitize_filename_component("..\\..\\etc\\passwd") == "passwd"


def test_score_range() -> None:
    validate_score_range(Decimal("50"))
    with pytest.raises(ValueError):
        validate_score_range(Decimal("101"))
