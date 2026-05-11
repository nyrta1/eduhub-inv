from __future__ import annotations

import pytest
from app.security.secure_http import SecureHttpError, assert_url_allowed


def test_blocks_loopback_ip_url() -> None:
    with pytest.raises(SecureHttpError):
        assert_url_allowed("http://127.0.0.1:8080/hook")


def test_blocks_private_range() -> None:
    with pytest.raises(SecureHttpError):
        assert_url_allowed("http://10.0.0.5/metadata")


def test_blocks_metadata_host() -> None:
    with pytest.raises(SecureHttpError):
        assert_url_allowed("http://169.254.169.254/latest/meta-data/")


def test_allows_public_https_when_allowlist_none() -> None:
    assert_url_allowed("https://example.edu/resource")


def test_allowlist_enforced() -> None:
    assert_url_allowed("https://partner.edu/api", allowed_hosts=frozenset({"partner.edu"}))
    with pytest.raises(SecureHttpError):
        assert_url_allowed("https://evil.com/x", allowed_hosts=frozenset({"partner.edu"}))
