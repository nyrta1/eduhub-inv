"""Global pytest configuration: markers, integration gating, shared hooks."""

from __future__ import annotations

import os

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: Postgres+Redis+migrations (RUN_INTEGRATION=1)",
    )
    config.addinivalue_line("markers", "slow: load/performance oriented")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.getenv("RUN_INTEGRATION") == "1":
        return
    skip_int = pytest.mark.skip(
        reason="set RUN_INTEGRATION=1 for docker-compose.test / CI integration job"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_int)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Placeholder for future coverage merge hooks."""
    _ = session
    _ = exitstatus
