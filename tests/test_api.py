"""Test we do not break the public API."""

from aiohttp_asyncmdnsresolver import _impl, api


def test_api() -> None:
    """Verify the public API is accessible."""
    assert api.AsyncMDNSResolver is not None
    assert api.AsyncMDNSResolver is _impl.AsyncMDNSResolver
