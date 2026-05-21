"""Lock in the socket-level fields of mDNS ``ResolveResult`` entries.

Each resolved address is converted to an aiohttp ``ResolveResult`` by
``_to_resolve_result``. Beyond ``hostname``/``host``/``port`` (covered in
``test_impl.py``), every result also carries ``family``, ``proto`` and ``flags``
that aiohttp uses to open the right kind of socket without further name
resolution. The most subtle of these is ``family``: it is derived from the
*address version* of the resolved IP, not from the family requested in the
query. An ``AF_UNSPEC`` lookup that returns a mix of IPv4 and IPv6 addresses
must therefore tag each result individually. None of these fields were asserted
anywhere, so a refactor of the conversion (e.g. echoing the query family) would
misroute aiohttp's socket selection while every existing test still passed.
"""

from __future__ import annotations

import socket
from collections.abc import AsyncGenerator, Generator
from ipaddress import IPv4Address, IPv6Address
from unittest.mock import patch

import pytest
import pytest_asyncio

from aiohttp_asyncmdnsresolver._impl import (
    _FAMILY_TO_RESOLVER_CLASS,
    _NUMERIC_SOCKET_FLAGS,
    AddressResolver,
    AddressResolverIPv4,
    AddressResolverIPv6,
)
from aiohttp_asyncmdnsresolver.api import AsyncMDNSResolver


class IPv6orIPv4HostResolver(AddressResolver):
    """Patchable class for testing."""


class IPv4HostResolver(AddressResolverIPv4):
    """Patchable class for testing."""


class IPv6HostResolver(AddressResolverIPv6):
    """Patchable class for testing."""


@pytest.fixture(autouse=True)
def make_resolvers_patchable() -> Generator[None, None, None]:
    """Swap the family->resolver map for patchable subclasses."""
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
    """Return a resolver closed during teardown."""
    resolver = AsyncMDNSResolver(mdns_timeout=0.1)
    yield resolver
    await resolver.close()


@pytest.mark.asyncio
async def test_unspec_result_family_follows_address_version(
    resolver: AsyncMDNSResolver,
) -> None:
    """An AF_UNSPEC lookup tags each result by the *address* family.

    The query family is ``AF_UNSPEC``, yet the IPv4 result must report
    ``AF_INET`` and the IPv6 result ``AF_INET6`` -- aiohttp opens sockets based
    on this per-result ``family``, so it has to follow the address, not the
    query.
    """
    with (
        patch.object(IPv6orIPv4HostResolver, "async_request", return_value=True),
        patch.object(
            IPv6orIPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv4Address("127.0.0.1"), IPv6Address("::1")],
        ),
    ):
        results = await resolver.resolve("localhost.local", family=socket.AF_UNSPEC)

    assert [r["family"] for r in results] == [socket.AF_INET, socket.AF_INET6]


@pytest.mark.asyncio
async def test_ipv4_result_socket_fields(resolver: AsyncMDNSResolver) -> None:
    """An IPv4 mDNS result advertises a numeric, ready-to-connect endpoint."""
    with (
        patch.object(IPv4HostResolver, "async_request", return_value=True),
        patch.object(
            IPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv4Address("127.0.0.1")],
        ),
    ):
        results = await resolver.resolve("localhost.local", family=socket.AF_INET)

    assert len(results) == 1
    result = results[0]
    assert result["family"] == socket.AF_INET
    assert result["proto"] == 0
    assert result["flags"] == _NUMERIC_SOCKET_FLAGS
    assert result["flags"] == socket.AI_NUMERICHOST | socket.AI_NUMERICSERV


@pytest.mark.asyncio
async def test_ipv6_result_socket_fields(resolver: AsyncMDNSResolver) -> None:
    """An IPv6 mDNS result advertises a numeric, ready-to-connect endpoint."""
    with (
        patch.object(IPv6HostResolver, "async_request", return_value=True),
        patch.object(
            IPv6HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv6Address("::1")],
        ),
    ):
        results = await resolver.resolve("localhost.local", family=socket.AF_INET6)

    assert len(results) == 1
    result = results[0]
    assert result["family"] == socket.AF_INET6
    assert result["proto"] == 0
    assert result["flags"] == _NUMERIC_SOCKET_FLAGS
