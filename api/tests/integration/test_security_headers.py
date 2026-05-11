from __future__ import annotations

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_security_headers_present_on_api_response(integration_client) -> None:
    r = await integration_client.get("/api/v1/health/live")
    assert r.status_code == 200
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert "Content-Security-Policy" in r.headers
