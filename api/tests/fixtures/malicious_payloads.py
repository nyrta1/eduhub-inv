"""Adversarial strings for validation / fuzz regression tests."""

from __future__ import annotations

SQL_INJECTION_SNIPPETS: tuple[str, ...] = (
    "'; DROP TABLE students;--",
    "1 OR 1=1",
    "UNION SELECT null,null,null--",
)

OVERSIZED_STRING_2MB: str = "A" * (2 * 1024 * 1024)

PATH_TRAVERSAL_NAMES: tuple[str, ...] = (
    "../../../etc/passwd",
    "..\\..\\windows\\system32\\config\\sam",
)
