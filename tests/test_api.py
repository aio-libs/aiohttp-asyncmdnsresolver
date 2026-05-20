"""Test we do not break the public API."""

from aiohttp.resolver import AsyncResolver

from aiohttp_asyncmdnsresolver import _impl, api


def test_api() -> None:
    """Verify the public API is accessible."""
    assert api.AsyncMDNSResolver is not None
    assert api.AsyncMDNSResolver is _impl.AsyncMDNSResolver


def test_dual_resolver_is_exported() -> None:
    """Verify AsyncDualMDNSResolver is part of the public API."""
    assert api.AsyncDualMDNSResolver is not None
    assert api.AsyncDualMDNSResolver is _impl.AsyncDualMDNSResolver


def test_public_api_all() -> None:
    """``api.__all__`` lists exactly the supported public names."""
    assert set(api.__all__) == {"AsyncMDNSResolver", "AsyncDualMDNSResolver"}
    for name in api.__all__:
        assert hasattr(api, name)


def test_resolvers_are_drop_in_aiohttp_resolvers() -> None:
    """Both resolvers subclass aiohttp's ``AsyncResolver`` so they remain
    drop-in replacements for ``aiohttp.TCPConnector(resolver=...)``."""
    assert issubclass(api.AsyncMDNSResolver, AsyncResolver)
    assert issubclass(api.AsyncDualMDNSResolver, AsyncResolver)


def test_resolvers_support_async_context_manager() -> None:
    """Both resolvers implement the async context manager protocol."""
    for resolver_cls in (api.AsyncMDNSResolver, api.AsyncDualMDNSResolver):
        assert hasattr(resolver_cls, "__aenter__")
        assert hasattr(resolver_cls, "__aexit__")
