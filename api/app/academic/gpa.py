from __future__ import annotations

from decimal import Decimal


def compute_weighted_gpa(rows: list[tuple[Decimal, Decimal]]) -> Decimal:
    """Compute GPA from (score, credits) tuples."""
    if not rows:
        return Decimal("0")
    total_points = Decimal("0")
    total_credits = Decimal("0")
    for score, credits in rows:
        total_points += score * credits
        total_credits += credits
    if total_credits == 0:
        return Decimal("0")
    return (total_points / total_credits).quantize(Decimal("0.01"))
