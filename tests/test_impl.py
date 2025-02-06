import asyncio
import socket
from collections.abc import AsyncGenerator, Generator
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
