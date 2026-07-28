"""Tests for SSL context and TLS error handling."""

import ssl

import httpx
import pytest

from github_mcp.utils.errors import _handle_api_error
from github_mcp.utils import ssl_context


@pytest.fixture(autouse=True)
def clear_ssl_context_cache():
    ssl_context.reset_ssl_context()
    yield
    ssl_context.reset_ssl_context()


def test_get_ssl_context_returns_cached_instance():
    ctx1 = ssl_context.get_ssl_context()
    ctx2 = ssl_context.get_ssl_context()
    assert isinstance(ctx1, ssl.SSLContext)
    assert ctx1 is ctx2


def test_get_ssl_context_loads_custom_ca_file(monkeypatch):
    import certifi

    monkeypatch.setenv("GITHUB_MCP_SSL_CA_FILE", certifi.where())

    ctx = ssl_context.get_ssl_context()
    assert isinstance(ctx, ssl.SSLContext)


def test_handle_api_error_tls_verification():
    error = httpx.ConnectError(
        "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: "
        "unable to get local issuer certificate (_ssl.c:1006)"
    )
    result = _handle_api_error(error)

    assert "TLS certificate verification failed" in result
    assert "GITHUB_MCP_SSL_CA_FILE" in result


def test_handle_api_error_generic_connection():
    error = httpx.ConnectError("Connection refused")
    result = _handle_api_error(error)

    assert "Network error occurred" in result
