from __future__ import annotations

import pytest
from app.security.safe_query import apply_safe_order_by, assert_safe_identifier
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Widget(Base):
    __tablename__ = "widgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))


def test_rejects_sql_injection_identifier() -> None:
    with pytest.raises(ValueError):
        assert_safe_identifier("name;drop")


def test_safe_order_known_field() -> None:
    allowed = {"name": Widget.name, "id": Widget.id}
    expr = apply_safe_order_by(allowed, "-name", default_column=Widget.id, default_desc=False)
    assert expr is not None


def test_safe_order_unknown_falls_back() -> None:
    allowed = {"name": Widget.name}
    expr = apply_safe_order_by(allowed, "unknown", default_column=Widget.id, default_desc=True)
    assert expr is not None
