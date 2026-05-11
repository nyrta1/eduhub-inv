from __future__ import annotations

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_readiness_reports_database_and_redis(integration_client) -> None:
    r = await integration_client.get("/api/v1/health/ready")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ready"
    assert data["database"] == "up"
    assert data["redis"] == "up"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_metrics_endpoint_exposed_when_enabled(integration_client) -> None:
    r = await integration_client.get("/metrics")
    assert r.status_code == 200
    assert "python_info" in r.text or "http" in r.text or r.text != ""
