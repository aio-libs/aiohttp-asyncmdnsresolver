import asyncio
import socket
from collections.abc import AsyncGenerator, Callable, Generator
from ipaddress import IPv4Address, IPv6Address
from typing import Any, NoReturn
from unittest.mock import patch

import pytest
import pytest_asyncio
from aiohttp.resolver import ResolveResult
from zeroconf.asyncio import AsyncZeroconf

from aiohttp_asyncmdnsresolver._impl import (
    _FAMILY_TO_RESOLVER_CLASS,
    AddressResolver,
    AddressResolverIPv4,
    AddressResolverIPv6,
)
from aiohttp_asyncmdnsresolver.api import AsyncDualMDNSResolver, AsyncMDNSResolver


class IPv6orIPv4HostResolver(AddressResolver):
    """Patchable class for testing."""


class IPv4HostResolver(AddressResolverIPv4):
    """Patchable class for testing."""


class IPv6HostResolver(AddressResolverIPv6):
    """Patchable class for testing."""


@pytest.fixture(autouse=True)
def make_resolvers_patchable() -> Generator[None, None, None]:
    """Patch the resolvers."""
    with patch.dict(
        _FAMILY_TO_RESOLVER_CLASS,
        {
            socket.AF_INET: IPv4HostResolver,
            socket.AF_INET6: IPv6HostResolver,
            socket.AF_UNSPEC: IPv6orIPv4HostResolver,
        },
    ):
        yield


@pytest_asyncio.fixture
async def resolver() -> AsyncGenerator[AsyncMDNSResolver]:
    """Return a resolver."""
    resolver = AsyncMDNSResolver(mdns_timeout=0.1)
    yield resolver
    await resolver.close()


@pytest_asyncio.fixture
async def mdns_resolver() -> AsyncGenerator[Callable[..., AsyncMDNSResolver]]:
    """Return a factory that builds AsyncMDNSResolver instances.

    Each resolver is constructed through the public constructor, so tests can
    select ``mdns_timeout`` (or other options) without poking private state,
    and every instance is closed during teardown.
    """
    resolvers: list[AsyncMDNSResolver] = []

    def _factory(**kwargs: Any) -> AsyncMDNSResolver:
        kwargs.setdefault("mdns_timeout", 0.1)
        resolver = AsyncMDNSResolver(**kwargs)
        resolvers.append(resolver)
        return resolver

    yield _factory
    for resolver in resolvers:
        await resolver.close()


@pytest_asyncio.fixture
async def dual_resolver() -> AsyncGenerator[AsyncDualMDNSResolver]:
    """Return a dual resolver."""
    dual_resolver = AsyncDualMDNSResolver(mdns_timeout=0.1)
    yield dual_resolver
    await dual_resolver.close()


@pytest_asyncio.fixture
async def custom_resolver() -> AsyncGenerator[AsyncMDNSResolver]:
    """Return a resolver."""
    aiozc = AsyncZeroconf()
    resolver = AsyncMDNSResolver(mdns_timeout=0.1, async_zeroconf=aiozc)
    yield resolver
    await resolver.close()
    await aiozc.async_close()


@pytest.mark.asyncio
async def test_resolve_localhost_with_async_mdns_resolver(
    resolver: AsyncMDNSResolver,
) -> None:
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
async def test_resolve_localhost_with_async_dual_mdns_resolver(
    dual_resolver: AsyncMDNSResolver,
) -> None:
    """Test the resolve method delegates to AsyncDualMDNSResolver for non MDNS."""
    with patch(
        "aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve",
        return_value=[ResolveResult(hostname="localhost", host="127.0.0.1")],  # type: ignore[typeddict-item]
    ):
        results = await dual_resolver.resolve("localhost")
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
async def test_resolve_mdns_name_mixed_case(resolver: AsyncMDNSResolver) -> None:
    """Test the .local suffix is matched case-insensitively (RFC 6762)."""
    with (
        patch.object(IPv6orIPv4HostResolver, "async_request", return_value=True),
        patch.object(
            IPv6orIPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv4Address("127.0.0.1"), IPv6Address("::1")],
        ),
    ):
        result = await resolver.resolve("Localhost.LOCAL", family=socket.AF_UNSPEC)

    assert result is not None
    assert len(result) == 2
    assert result[0]["host"] == "127.0.0.1"
    assert result[1]["host"] == "::1"


@pytest.mark.asyncio
async def test_resolve_mdns_name_mixed_case_trailing_dot_async_dual_mdns_resolver(
    dual_resolver: AsyncDualMDNSResolver,
) -> None:
    """Test the dual resolver matches .local case-insensitively (RFC 6762).

    Uses a mixed-case host with a trailing dot to cover both the
    AsyncDualMDNSResolver routing path and the ``.local.`` suffix branch.
    """
    with (
        patch(
            "aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve",
            return_value=[
                ResolveResult(hostname="MyHost.Local.", host="127.0.0.1", port=0)  # type: ignore[typeddict-item]
            ],
        ),
        patch.object(IPv4HostResolver, "async_request", return_value=True),
        patch.object(
            IPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv4Address("127.0.0.1")],
        ),
    ):
        results = await dual_resolver.resolve("MyHost.Local.")
    assert results is not None
    assert len(results) == 1
    assert results[0]["host"] == "127.0.0.1"


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
async def test_resolve_mdns_name_zero_timeout_cache_miss_no_network(
    mdns_resolver: Callable[..., AsyncMDNSResolver],
) -> None:
    """Test mdns_timeout=0 raises on a cache miss without a network query.

    With a falsy ``mdns_timeout`` the resolver is cache-only: a cache miss must
    not fall back to an mDNS request on the network, so the lookup fails.
    """
    resolver = mdns_resolver(mdns_timeout=0)
    with (
        patch.object(IPv4HostResolver, "load_from_cache", return_value=False),
        patch.object(IPv4HostResolver, "async_request") as async_request,
        patch.object(
            IPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[],
        ),
        pytest.raises(OSError, match="MDNS lookup failed"),
    ):
        await resolver.resolve("localhost.local")

    async_request.assert_not_called()


@pytest.mark.asyncio
async def test_resolve_mdns_name_none_timeout_cache_miss_no_network(
    mdns_resolver: Callable[..., AsyncMDNSResolver],
) -> None:
    """Test mdns_timeout=None behaves cache-only like mdns_timeout=0."""
    resolver = mdns_resolver(mdns_timeout=None)
    with (
        patch.object(IPv4HostResolver, "load_from_cache", return_value=False),
        patch.object(IPv4HostResolver, "async_request") as async_request,
        patch.object(
            IPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[],
        ),
        pytest.raises(OSError, match="MDNS lookup failed"),
    ):
        await resolver.resolve("localhost.local")

    async_request.assert_not_called()


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
    resolver = AsyncMDNSResolver(mdns_timeout=0.1, async_zeroconf=aiozc)
    await resolver.close()
    await aiozc.async_close()
    assert resolver._aiozc is None
    assert resolver._aiozc_owner is False


@pytest.mark.asyncio
async def test_create_destroy_resolver_no_aiozc() -> None:
    """Test the resolver can be created and destroyed."""
    resolver = AsyncMDNSResolver(mdns_timeout=0.1)
    await resolver.close()
    assert resolver._aiozc is None
    assert resolver._aiozc_owner is True


@pytest.mark.asyncio
async def test_async_context_manager_closes_resolver() -> None:
    """Test ``async with`` closes an owned resolver on exit."""
    async with AsyncMDNSResolver(mdns_timeout=0.1) as resolver:
        assert isinstance(resolver, AsyncMDNSResolver)
        assert resolver._aiozc is not None
        assert resolver._aiozc_owner is True
    assert resolver._aiozc is None


@pytest.mark.asyncio
async def test_async_context_manager_closes_dual_resolver() -> None:
    """Test ``async with`` closes an owned dual resolver on exit."""
    async with AsyncDualMDNSResolver(mdns_timeout=0.1) as resolver:
        assert isinstance(resolver, AsyncDualMDNSResolver)
        assert resolver._aiozc is not None
    assert resolver._aiozc is None


@pytest.mark.asyncio
async def test_async_context_manager_returns_self() -> None:
    """Test ``__aenter__`` yields the resolver instance itself."""
    resolver = AsyncMDNSResolver(mdns_timeout=0.1)
    async with resolver as entered:
        assert entered is resolver


@pytest.mark.asyncio
async def test_async_context_manager_closes_on_exception() -> None:
    """Test the resolver is closed even when the body raises."""
    resolver = AsyncMDNSResolver(mdns_timeout=0.1)
    with pytest.raises(ValueError, match="boom"):
        async with resolver:
            raise ValueError("boom")
    assert resolver._aiozc is None


@pytest.mark.asyncio
async def test_async_context_manager_passed_in_zeroconf_not_closed() -> None:
    """Test exiting the context manager does not close a borrowed zeroconf."""
    aiozc = AsyncZeroconf()
    async with AsyncMDNSResolver(mdns_timeout=0.1, async_zeroconf=aiozc) as resolver:
        assert resolver._aiozc_owner is False
    assert resolver._aiozc is None
    # The borrowed instance is the caller's to close; doing so must still work.
    await aiozc.async_close()


@pytest.mark.asyncio
async def test_same_results_async_dual_mdns_resolver(
    dual_resolver: AsyncMDNSResolver,
) -> None:
    """Test AsyncDualMDNSResolver resolves using mDNS and DNS.

    Test when both resolvers return the same result.
    """
    with (
        patch(
            "aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve",
            return_value=[
                ResolveResult(hostname="localhost.local.", host="127.0.0.1", port=0)  # type: ignore[typeddict-item]
            ],
        ),
        patch.object(IPv4HostResolver, "async_request", return_value=True),
        patch.object(
            IPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv4Address("127.0.0.1")],
        ),
    ):
        results = await dual_resolver.resolve("localhost.local.")
    assert results is not None
    assert len(results) == 1
    result = results[0]
    assert result["hostname"] == "localhost.local."
    assert result["host"] == "127.0.0.1"


@pytest.mark.asyncio
async def test_first_result_wins_async_dual_mdns_resolver(
    dual_resolver: AsyncMDNSResolver,
) -> None:
    """Test AsyncDualMDNSResolver resolves using mDNS and DNS.

    Test the first result wins when one resolver takes longer
    """

    async def _take_a_while_to_resolve(*args: Any, **kwargs: Any) -> NoReturn:
        await asyncio.sleep(0.1)
        raise RuntimeError("Should not be called")

    with (
        patch(
            "aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve",
            _take_a_while_to_resolve,
        ),
        patch.object(IPv4HostResolver, "async_request", return_value=True),
        patch.object(
            IPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv4Address("127.0.0.2")],
        ),
    ):
        results = await dual_resolver.resolve("localhost.local.")
    assert results is not None
    assert len(results) == 1
    result = results[0]
    assert result["hostname"] == "localhost.local."
    assert result["host"] == "127.0.0.2"


@pytest.mark.asyncio
async def test_exception_mdns_before_result_async_dual_mdns_resolver(
    dual_resolver: AsyncMDNSResolver,
) -> None:
    """Test AsyncDualMDNSResolver resolves using mDNS and DNS.

    Test that an exception is returned from mDNS resolver the other
    resolver returns a result.
    """

    async def _take_a_while_to_resolve_and_fail(*args: Any, **kwargs: Any) -> NoReturn:
        await asyncio.sleep(0)
        raise OSError(None, "NXDOMAIN")

    async def _take_a_while_to_resolve(
        *args: Any, **kwargs: Any
    ) -> list[ResolveResult]:
        await asyncio.sleep(0.2)
        return [ResolveResult(hostname="localhost.local.", host="127.0.0.1", port=0)]  # type: ignore[typeddict-item]

    with (
        patch(
            "aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve",
            _take_a_while_to_resolve,
        ),
        patch.object(
            IPv4HostResolver, "async_request", _take_a_while_to_resolve_and_fail
        ),
    ):
        results = await dual_resolver.resolve("localhost.local.")
    assert results is not None
    assert len(results) == 1
    result = results[0]
    assert result["hostname"] == "localhost.local."
    assert result["host"] == "127.0.0.1"


@pytest.mark.asyncio
async def test_exception_dns_before_result_async_dual_mdns_resolver(
    dual_resolver: AsyncMDNSResolver,
) -> None:
    """Test AsyncDualMDNSResolver resolves using mDNS and DNS.

    Test that an exception is returned from DNS resolver the other
    mDNS resolver returns a result.
    """

    async def _take_a_while_to_resolve_and_fail(*args: Any, **kwargs: Any) -> NoReturn:
        await asyncio.sleep(0)
        raise OSError(None, "NXDOMAIN")

    async def _take_a_while_to_resolve(*args: Any, **kwargs: Any) -> bool:
        await asyncio.sleep(0.2)
        return True

    with (
        patch(
            "aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve",
            _take_a_while_to_resolve_and_fail,
        ),
        patch.object(IPv4HostResolver, "async_request", _take_a_while_to_resolve),
        patch.object(
            IPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv4Address("127.0.0.2")],
        ),
    ):
        results = await dual_resolver.resolve("localhost.local.")
    assert results is not None
    assert len(results) == 1
    result = results[0]
    assert result["hostname"] == "localhost.local."
    assert result["host"] == "127.0.0.2"


@pytest.mark.asyncio
async def test_async_dual_mdns_resolver_from_cache(
    dual_resolver: AsyncMDNSResolver,
) -> None:
    """Test AsyncDualMDNSResolver can resolve from cache."""
    with (
        patch(
            "aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve",
            side_effect=OSError,
        ),
        patch.object(IPv4HostResolver, "load_from_cache", return_value=True),
        patch.object(
            IPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv4Address("127.0.0.2")],
        ),
    ):
        results = await dual_resolver.resolve("localhost.local.")
    assert results is not None
    assert len(results) == 1
    result = results[0]
    assert result["hostname"] == "localhost.local."
    assert result["host"] == "127.0.0.2"


@pytest.mark.asyncio
async def test_different_results_async_dual_mdns_resolver(
    dual_resolver: AsyncMDNSResolver,
) -> None:
    """Test AsyncDualMDNSResolver resolves using mDNS and DNS.

    Test when both resolvers return different results
    """
    with (
        patch(
            "aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve",
            return_value=[
                ResolveResult(hostname="localhost.local.", host="127.0.0.1", port=0)  # type: ignore[typeddict-item]
            ],
        ),
        patch.object(IPv4HostResolver, "async_request", return_value=True),
        patch.object(
            IPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv4Address("127.0.0.2")],
        ),
    ):
        results = await dual_resolver.resolve("localhost.local.")
    assert results is not None
    assert len(results) == 2
    result = results[0]
    assert result["hostname"] == "localhost.local."
    assert result["host"] == "127.0.0.2"
    result = results[1]
    assert result["hostname"] == "localhost.local."
    assert result["host"] == "127.0.0.1"


@pytest.mark.asyncio
async def test_duplicate_ip_differing_hostname_async_dual_mdns_resolver(
    dual_resolver: AsyncMDNSResolver,
) -> None:
    """Test the dual resolver collapses the same address from mDNS and DNS.

    The mDNS path reports the zeroconf ``info.server`` hostname (with a
    trailing dot) while the DNS path echoes the caller's input host (no
    trailing dot). Both describe the same endpoint, so the combined result
    must not contain the address twice.
    """
    with (
        patch(
            "aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve",
            return_value=[
                ResolveResult(hostname="localhost.local", host="127.0.0.1", port=0)  # type: ignore[typeddict-item]
            ],
        ),
        patch.object(IPv4HostResolver, "async_request", return_value=True),
        patch.object(
            IPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv4Address("127.0.0.1")],
        ),
    ):
        results = await dual_resolver.resolve("localhost.local")
    assert results is not None
    assert len(results) == 1
    result = results[0]
    assert result["hostname"] == "localhost.local."
    assert result["host"] == "127.0.0.1"


@pytest.mark.asyncio
async def test_unspec_combines_ipv4_and_ipv6_async_dual_mdns_resolver(
    dual_resolver: AsyncDualMDNSResolver,
) -> None:
    """Test the dual resolver merges both address families with AF_UNSPEC.

    The concurrent mDNS/DNS combine path was only covered for IPv4. With
    ``AF_UNSPEC`` the unified ``AddressResolver`` returns both an IPv4 and an
    IPv6 address; a DNS result echoing one of them must be de-duplicated while
    the other family is preserved.
    """
    with (
        patch(
            "aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve",
            return_value=[
                ResolveResult(hostname="localhost.local", host="127.0.0.1", port=0)  # type: ignore[typeddict-item]
            ],
        ),
        patch.object(IPv6orIPv4HostResolver, "async_request", return_value=True),
        patch.object(
            IPv6orIPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv4Address("127.0.0.1"), IPv6Address("::1")],
        ),
    ):
        results = await dual_resolver.resolve(
            "localhost.local", family=socket.AF_UNSPEC
        )
    assert results is not None
    # mDNS results come first; the DNS IPv4 echo collapses into the mDNS IPv4.
    assert len(results) == 2
    assert results[0]["host"] == "127.0.0.1"
    assert results[1]["host"] == "::1"


@pytest.mark.asyncio
async def test_inet6_distinct_results_async_dual_mdns_resolver(
    dual_resolver: AsyncDualMDNSResolver,
) -> None:
    """Test the dual resolver merges distinct IPv6 results with AF_INET6.

    Exercises the IPv6-only resolver class through the concurrent combine path,
    which was previously only validated for IPv4.
    """
    with (
        patch(
            "aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve",
            return_value=[
                ResolveResult(hostname="localhost.local.", host="::2", port=0)  # type: ignore[typeddict-item]
            ],
        ),
        patch.object(IPv6HostResolver, "async_request", return_value=True),
        patch.object(
            IPv6HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv6Address("::1")],
        ),
    ):
        results = await dual_resolver.resolve("localhost.local.", family=socket.AF_INET6)
    assert results is not None
    assert len(results) == 2
    # mDNS result is prioritized ahead of the distinct DNS result.
    assert results[0]["host"] == "::1"
    assert results[1]["host"] == "::2"


@pytest.mark.asyncio
async def test_different_results_async_dual_mdns_resolver_zero_timeout(
    dual_resolver: AsyncMDNSResolver,
) -> None:
    """Test AsyncDualMDNSResolver resolves using mDNS and DNS.

    Test when both resolvers return different results with zero timeout
    for mDNS.
    """
    dual_resolver._mdns_timeout = 0
    with (
        patch(
            "aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve",
            return_value=[
                ResolveResult(hostname="localhost.local.", host="127.0.0.1", port=0)  # type: ignore[typeddict-item]
            ],
        ),
        patch.object(IPv4HostResolver, "load_from_cache", return_value=False),
        patch.object(IPv4HostResolver, "async_request", return_value=True),
        patch.object(
            IPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[],
        ),
    ):
        results = await dual_resolver.resolve("localhost.local.")
    assert results is not None
    assert len(results) == 1
    result = results[0]
    assert result["hostname"] == "localhost.local."
    assert result["host"] == "127.0.0.1"


@pytest.mark.asyncio
async def test_failed_mdns_async_dual_mdns_resolver(
    dual_resolver: AsyncMDNSResolver,
) -> None:
    """Test AsyncDualMDNSResolver resolves using mDNS and DNS.

    Test when mDNS fails, but DNS succeeds.
    """
    with (
        patch(
            "aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve",
            return_value=[
                ResolveResult(hostname="localhost.local.", host="127.0.0.1", port=0)  # type: ignore[typeddict-item]
            ],
        ),
        patch.object(IPv4HostResolver, "async_request", return_value=True),
        patch.object(
            IPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[],
        ),
    ):
        results = await dual_resolver.resolve("localhost.local.")
    assert results is not None
    assert len(results) == 1
    result = results[0]
    assert result["hostname"] == "localhost.local."
    assert result["host"] == "127.0.0.1"


@pytest.mark.asyncio
async def test_failed_dns_async_dual_mdns_resolver(
    dual_resolver: AsyncMDNSResolver,
) -> None:
    """Test AsyncDualMDNSResolver resolves using mDNS and DNS.

    Test when DNS fails, but mDNS succeeds.
    """
    with (
        patch(
            "aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve",
            side_effect=OSError(None, "DNS lookup failed"),
        ),
        patch.object(IPv4HostResolver, "async_request", return_value=True),
        patch.object(
            IPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv4Address("127.0.0.2")],
        ),
    ):
        results = await dual_resolver.resolve("localhost.local.")
    assert results is not None
    assert len(results) == 1
    result = results[0]
    assert result["hostname"] == "localhost.local."
    assert result["host"] == "127.0.0.2"


@pytest.mark.asyncio
async def test_all_failed_async_dual_mdns_resolver(
    dual_resolver: AsyncMDNSResolver,
) -> None:
    """Test AsyncDualMDNSResolver resolves using mDNS and DNS.

    Test when DNS fails, and mDNS fails.
    """
    with (
        patch(
            "aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve",
            side_effect=OSError(None, "DNS lookup failed"),
        ),
        patch.object(IPv4HostResolver, "async_request", return_value=True),
        patch.object(
            IPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[],
        ),
        pytest.raises(OSError, match="MDNS lookup failed, DNS lookup failed"),
    ):
        await dual_resolver.resolve("localhost.local.")


@pytest.mark.asyncio
async def test_close_idempotent_owned_zeroconf() -> None:
    """Closing a resolver that owns its AsyncZeroconf twice is a no-op."""
    resolver = AsyncMDNSResolver(mdns_timeout=0.1)
    assert resolver._aiozc_owner is True
    await resolver.close()
    assert resolver._aiozc is None
    # A second close must not raise (e.g. AttributeError on None).
    await resolver.close()
    assert resolver._aiozc is None


@pytest.mark.asyncio
async def test_close_idempotent_custom_zeroconf() -> None:
    """Closing a resolver with a passed-in AsyncZeroconf twice is a no-op."""
    aiozc = AsyncZeroconf()
    resolver = AsyncMDNSResolver(mdns_timeout=0.1, async_zeroconf=aiozc)
    assert resolver._aiozc_owner is False
    await resolver.close()
    await resolver.close()
    assert resolver._aiozc is None
    # The caller still owns the passed-in instance and closes it themselves.
    await aiozc.async_close()


@pytest.mark.asyncio
async def test_no_cancel_swallow_dual_mdns_resolver(
    dual_resolver: AsyncMDNSResolver,
) -> None:
    """Test AsyncDualMDNSResolver does not swallow cancellation errors."""

    async def _take_a_while_to_resolve(*args: Any, **kwargs: Any) -> NoReturn:
        await asyncio.sleep(0.5)
        raise RuntimeError("Should not be called")

    with (
        patch(
            "aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve",
            _take_a_while_to_resolve,
        ),
        patch.object(IPv4HostResolver, "async_request", _take_a_while_to_resolve),
    ):
        resolve_tasks = asyncio.create_task(dual_resolver.resolve("localhost.local."))
        await asyncio.sleep(0.1)
        resolve_tasks.cancel()
        with pytest.raises(asyncio.CancelledError):
            await resolve_tasks


@pytest.mark.asyncio
async def test_cancel_cancels_child_tasks_dual_mdns_resolver(
    dual_resolver: AsyncDualMDNSResolver,
) -> None:
    """Test cancelling resolve() cancels both child tasks instead of orphaning them."""
    cancelled = {"mdns": False, "dns": False}

    async def _mdns_op(*args: Any, **kwargs: Any) -> NoReturn:
        try:
            await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            cancelled["mdns"] = True
            raise
        raise RuntimeError("Should not finish")

    async def _dns_op(*args: Any, **kwargs: Any) -> NoReturn:
        try:
            await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            cancelled["dns"] = True
            raise
        raise RuntimeError("Should not finish")

    with (
        patch("aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve", _dns_op),
        patch.object(IPv4HostResolver, "async_request", _mdns_op),
    ):
        resolve_task = asyncio.create_task(dual_resolver.resolve("localhost.local."))
        await asyncio.sleep(0.1)
        resolve_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await resolve_task

    assert cancelled["mdns"] is True
    assert cancelled["dns"] is True


@pytest.mark.asyncio
async def test_loser_non_cancel_exception_does_not_override_result_dual_mdns_resolver(
    dual_resolver: AsyncDualMDNSResolver,
) -> None:
    """Test loser raising a non-cancel exception during cleanup does not override winner."""

    async def _dns_swallows_cancel_and_raises(*args: Any, **kwargs: Any) -> NoReturn:
        try:
            await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            raise RuntimeError("Loser blew up on cancel") from None
        raise RuntimeError("Should not finish")

    with (
        patch(
            "aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve",
            _dns_swallows_cancel_and_raises,
        ),
        patch.object(IPv4HostResolver, "async_request", return_value=True),
        patch.object(
            IPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv4Address("127.0.0.1")],
        ),
    ):
        results = await dual_resolver.resolve("localhost.local.")

    assert results is not None
    assert len(results) == 1
    assert results[0]["host"] == "127.0.0.1"


@pytest.mark.asyncio
async def test_cancel_during_loser_wait_dual_mdns_resolver(
    dual_resolver: AsyncDualMDNSResolver,
) -> None:
    """Test cancellation while waiting for the loser (after winner failed) propagates."""
    dns_cancelled = False

    async def _mdns_fast_failure(*args: Any, **kwargs: Any) -> NoReturn:
        raise OSError(None, "MDNS lookup failed")

    async def _dns_slow(*args: Any, **kwargs: Any) -> NoReturn:
        nonlocal dns_cancelled
        try:
            await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            dns_cancelled = True
            raise
        raise RuntimeError("Should not finish")

    with (
        patch("aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve", _dns_slow),
        patch.object(IPv4HostResolver, "async_request", _mdns_fast_failure),
    ):
        resolve_task = asyncio.create_task(dual_resolver.resolve("localhost.local."))
        await asyncio.sleep(0.05)
        resolve_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await resolve_task

    assert dns_cancelled is True


@pytest.mark.asyncio
async def test_cancel_after_winner_completes_dual_mdns_resolver(
    dual_resolver: AsyncDualMDNSResolver,
) -> None:
    """Test cancellation arriving while the loser is being drained propagates."""
    dns_cancelled = False

    async def _dns_slow(*args: Any, **kwargs: Any) -> NoReturn:
        nonlocal dns_cancelled
        try:
            await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            dns_cancelled = True
            raise
        raise RuntimeError("Should not finish")

    with (
        patch("aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve", _dns_slow),
        patch.object(IPv4HostResolver, "async_request", return_value=True),
        patch.object(
            IPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv4Address("127.0.0.1")],
        ),
    ):
        resolve_task = asyncio.create_task(dual_resolver.resolve("localhost.local."))
        # Yield enough times for resolve() to advance past asyncio.wait, collect
        # the mDNS result and enter the gather await inside the finally block.
        for _ in range(5):
            await asyncio.sleep(0)
        resolve_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await resolve_task

    assert dns_cancelled is True


@pytest.mark.asyncio
async def test_double_cancel_dual_mdns_resolver(
    dual_resolver: AsyncDualMDNSResolver,
) -> None:
    """Test that double-cancelling resolve() still propagates CancelledError."""
    cancelled = {"mdns": False, "dns": False}

    async def _mdns_op(*args: Any, **kwargs: Any) -> NoReturn:
        try:
            await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            cancelled["mdns"] = True
            raise
        raise RuntimeError("Should not finish")

    async def _dns_op(*args: Any, **kwargs: Any) -> NoReturn:
        try:
            await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            cancelled["dns"] = True
            raise
        raise RuntimeError("Should not finish")

    with (
        patch("aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve", _dns_op),
        patch.object(IPv4HostResolver, "async_request", _mdns_op),
    ):
        resolve_task = asyncio.create_task(dual_resolver.resolve("localhost.local."))
        await asyncio.sleep(0.05)
        resolve_task.cancel()
        resolve_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await resolve_task

    assert cancelled["mdns"] is True
    assert cancelled["dns"] is True
