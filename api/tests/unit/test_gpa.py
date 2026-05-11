from __future__ import annotations

from decimal import Decimal

from app.academic.gpa import compute_weighted_gpa


def test_gpa_empty() -> None:
    assert compute_weighted_gpa([]) == Decimal("0")


def test_gpa_single_course() -> None:
    assert compute_weighted_gpa([(Decimal("80"), Decimal("3"))]) == Decimal("80.00")


def test_gpa_weighted_average() -> None:
    rows = [
        (Decimal("90"), Decimal("4")),
        (Decimal("70"), Decimal("2")),
    ]
    assert compute_weighted_gpa(rows) == Decimal("83.33")


def test_gpa_zero_total_credits_returns_zero() -> None:
    assert compute_weighted_gpa([(Decimal("50"), Decimal("0"))]) == Decimal("0")
