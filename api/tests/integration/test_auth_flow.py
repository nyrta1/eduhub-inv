from __future__ import annotations

import uuid

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_login_me_roundtrip(integration_client, strong_password: str) -> None:
    """Validates auth persistence, JWT issuance, and protected route access."""
    email = f"it-{uuid.uuid4().hex[:12]}@student.edu.kz"
    reg = await integration_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": strong_password,
            "full_name": "Integration Student",
        },
    )
    assert reg.status_code == 201, reg.text

    login = await integration_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": strong_password},
    )
    assert login.status_code == 200, login.text
    access = login.json()["access_token"]

    me = await integration_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == email
    assert "STUDENT" in body["roles"]
