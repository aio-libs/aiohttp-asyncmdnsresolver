from aiohttp_asyncmdnsresolver.api import AsyncMDNSResolver
from aiohttp.resolver import ResolveResult
import pytest
import pytest_asyncio
from zeroconf.asyncio import AsyncZeroconf
from collections.abc import AsyncGenerator
from unittest.mock import patch
from ipaddress import IPv6Address, IPv4Address
import socket
from aiohttp_asyncmdnsresolver._impl import (
    IPv4HostResolver,
    IPv6HostResolver,
    IPv6orIPv4HostResolver,
)


@pytest_asyncio.fixture
async def resolver() -> AsyncGenerator[AsyncMDNSResolver]:
    """Return a resolver."""
    resolver = AsyncMDNSResolver(timeout=0.1)
    yield resolver
    await resolver.close()


@pytest_asyncio.fixture
async def custom_resolver() -> AsyncGenerator[AsyncMDNSResolver]:
    """Return a resolver."""
    aiozc = AsyncZeroconf()
    resolver = AsyncMDNSResolver(timeout=0.1, async_zeroconf=aiozc)
    yield resolver
    await resolver.close()
    await aiozc.async_close()


@pytest.mark.asyncio
async def test_resolve_localhost(resolver: AsyncMDNSResolver) -> None:
    """Test the resolve method delegates to AsyncResolver for non MDNS."""
    with patch(
        "aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve",
        return_value=[ResolveResult(hostname="localhost", host="127.0.0.1")],  # type: ignore[typeddict-item]
    ):
        results = await resolver.resolve("localhost")
    assert results is not None
    assert len(results) == 1
    result = results[0]
    assert result["hostname"] == "localhost"
    assert result["host"] == "127.0.0.1"


@pytest.mark.asyncio
async def test_resolve_mdns_name_unspec(resolver: AsyncMDNSResolver) -> None:
    """Test the resolve method with unspecified family."""
    with (
        patch.object(IPv6orIPv4HostResolver, "async_request", return_value=True),
        patch.object(
            IPv6orIPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv4Address("127.0.0.1"), IPv6Address("::1")],
        ),
    ):
        result = await resolver.resolve("localhost.local", family=socket.AF_UNSPEC)

    assert result is not None
    assert len(result) == 2
    assert result[0]["hostname"] == "localhost.local."
    assert result[0]["host"] == "127.0.0.1"
    assert result[1]["hostname"] == "localhost.local."
    assert result[1]["host"] == "::1"


@pytest.mark.asyncio
async def test_resolve_mdns_name_unspec_from_cache(resolver: AsyncMDNSResolver) -> None:
    """Test the resolve method from_cache."""
    with (
        patch.object(IPv6orIPv4HostResolver, "load_from_cache", return_value=True),
        patch.object(
            IPv6orIPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv4Address("127.0.0.1"), IPv6Address("::1")],
        ),
    ):
        result = await resolver.resolve("localhost.local", 80, family=socket.AF_UNSPEC)

    assert result is not None
    assert len(result) == 2
    assert result[0]["hostname"] == "localhost.local."
    assert result[0]["host"] == "127.0.0.1"
    assert result[0]["port"] == 80
    assert result[1]["hostname"] == "localhost.local."
    assert result[1]["host"] == "::1"
    assert result[1]["port"] == 80


@pytest.mark.asyncio
async def test_resolve_mdns_name_unspec_no_results(resolver: AsyncMDNSResolver) -> None:
    """Test the resolve method no results."""
    with (
        patch.object(IPv6orIPv4HostResolver, "async_request", return_value=True),
        patch.object(
            IPv6orIPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[],
        ),
        pytest.raises(OSError, match="MDNS lookup failed"),
    ):
        await resolver.resolve("localhost.local", family=socket.AF_UNSPEC)


@pytest.mark.asyncio
async def test_resolve_mdns_name_unspec_trailing_dot(
    resolver: AsyncMDNSResolver,
) -> None:
    """Test the resolve method with unspecified family with trailing dot."""
    with (
        patch.object(IPv6orIPv4HostResolver, "async_request", return_value=True),
        patch.object(
            IPv6orIPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv4Address("127.0.0.1"), IPv6Address("::1")],
        ),
    ):
        result = await resolver.resolve("localhost.local.", family=socket.AF_UNSPEC)

    assert result is not None
    assert len(result) == 2
    assert result[0]["hostname"] == "localhost.local."
    assert result[0]["host"] == "127.0.0.1"
    assert result[1]["hostname"] == "localhost.local."
    assert result[1]["host"] == "::1"


@pytest.mark.asyncio
async def test_resolve_mdns_name_af_inet(resolver: AsyncMDNSResolver) -> None:
    """Test the resolve method with socket.AF_INET family."""
    with (
        patch.object(IPv4HostResolver, "async_request", return_value=True),
        patch.object(
            IPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv4Address("127.0.0.1")],
        ),
    ):
        result = await resolver.resolve("localhost.local", family=socket.AF_INET)

    assert result is not None
    assert len(result) == 1
    assert result[0]["hostname"] == "localhost.local."
    assert result[0]["host"] == "127.0.0.1"


@pytest.mark.asyncio
async def test_resolve_mdns_name_af_inet6(resolver: AsyncMDNSResolver) -> None:
    """Test the resolve method with socket.AF_INET6 family."""
    with (
        patch.object(IPv6HostResolver, "async_request", return_value=True),
        patch.object(
            IPv6HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv6Address("::1")],
        ),
    ):
        result = await resolver.resolve("localhost.local", family=socket.AF_INET6)

    assert result is not None
    assert len(result) == 1
    assert result[0]["hostname"] == "localhost.local."
    assert result[0]["host"] == "::1"


@pytest.mark.asyncio
async def test_resolve_mdns_passed_in_asynczeroconf(
    custom_resolver: AsyncMDNSResolver,
) -> None:
    """Test the resolve method with unspecified family with a passed in zeroconf."""
    assert custom_resolver._aiozc_owner is False
    assert custom_resolver._aiozc is not None
    with (
        patch.object(IPv6orIPv4HostResolver, "async_request", return_value=True),
        patch.object(
            IPv6orIPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv4Address("127.0.0.1"), IPv6Address("::1")],
        ),
    ):
        result = await custom_resolver.resolve(
            "localhost.local", family=socket.AF_UNSPEC
        )

    assert result is not None
    assert len(result) == 2
    assert result[0]["hostname"] == "localhost.local."
    assert result[0]["host"] == "127.0.0.1"
    assert result[1]["hostname"] == "localhost.local."
    assert result[1]["host"] == "::1"


@pytest.mark.asyncio
async def test_create_destroy_resolver() -> None:
    """Test the resolver can be created and destroyed."""
    aiozc = AsyncZeroconf()
    resolver = AsyncMDNSResolver(timeout=0.1, async_zeroconf=aiozc)
    await resolver.close()
    await aiozc.async_close()
    assert resolver._aiozc is None
    assert resolver._aiozc_owner is False


@pytest.mark.asyncio
async def test_create_destroy_resolver_no_aiozc() -> None:
    """Test the resolver can be created and destroyed."""
    resolver = AsyncMDNSResolver(timeout=0.1)
    await resolver.close()
    assert resolver._aiozc is None
    assert resolver._aiozc_owner is True
