"""SSL/TLS context helpers for outbound HTTPS clients.

httpx defaults to certifi's Mozilla CA bundle, which does not include
corporate or antivirus TLS-intercept roots (Norton, Zscaler, etc.) that
are often present in the OS trust store. We prefer the system store instead.
"""

from __future__ import annotations

import os
import ssl
from typing import Optional

_ssl_context: Optional[ssl.SSLContext] = None


def get_ssl_context() -> ssl.SSLContext:
    """Return a cached SSL context that trusts the OS certificate store.

    Override order for custom CA bundles:
    1. GITHUB_MCP_SSL_CA_FILE
    2. SSL_CERT_FILE (standard Python/OpenSSL convention)
    """
    global _ssl_context
    if _ssl_context is not None:
        return _ssl_context

    ca_file = os.environ.get("GITHUB_MCP_SSL_CA_FILE") or os.environ.get(
        "SSL_CERT_FILE"
    )

    try:
        import truststore

        ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except ImportError:
        ctx = ssl.create_default_context()

    if ca_file and os.path.isfile(ca_file):
        ctx.load_verify_locations(cafile=ca_file)

    _ssl_context = ctx
    return ctx


def reset_ssl_context() -> None:
    """Clear cached SSL context (for tests)."""
    global _ssl_context
    _ssl_context = None
