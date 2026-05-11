"""Integration-only fixtures: migrations, HTTP client over ASGI."""

from __future__ import annotations

import os
import subprocess

import pytest
import pytest_asyncio


def pytest_sessionstart(session: pytest.Session) -> None:
    if os.getenv("RUN_INTEGRATION") != "1":
        return
    subprocess.run(
        ["alembic", "upgrade", "head"],
        check=True,
        env=os.environ.copy(),
        cwd=os.getcwd(),
    )


@pytest_asyncio.fixture
async def integration_client():
    from app.main import app
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app, lifespan="on")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def strong_password() -> str:
    """Meets PasswordPolicyViolation rules (length + character classes)."""
    return "Aa1!StrongPassOk"
