from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from sqlalchemy import Column, UnaryExpression, asc, desc
from sqlalchemy.orm import InstrumentedAttribute


_IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def assert_safe_identifier(name: str, *, label: str = "identifier") -> str:
    """Reject SQL injection via dynamic identifiers (order/group aliases)."""
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Unsafe {label}: {name!r}")
    return name


def apply_safe_order_by(
    allowed: dict[str, InstrumentedAttribute[Any] | Column[Any]],
    sort_param: str | None,
    *,
    default_column: InstrumentedAttribute[Any] | Column[Any],
    default_desc: bool = False,
) -> UnaryExpression[Any]:
    """
    Map an external sort key to a concrete SQLAlchemy column.

    `sort_param` format: ``field`` or ``-field`` for descending. Unknown fields fall back.
    """
    if not sort_param:
        return desc(default_column) if default_desc else asc(default_column)

    desc_flag = sort_param.startswith("-")
    key = sort_param[1:] if desc_flag else sort_param
    assert_safe_identifier(key, label="sort_field")

    column = allowed.get(key)
    if column is None:
        return desc(default_column) if default_desc else asc(default_column)

    return desc(column) if desc_flag else asc(column)


def columns_allowlist_only(requested: Iterable[str], allowed: frozenset[str]) -> list[str]:
    """Return only identifiers present in the allow-list (stable order)."""
    out: list[str] = []
    for name in requested:
        assert_safe_identifier(name)
        if name in allowed:
            out.append(name)
    return out
