"""Lock the ``mdns_timeout`` seconds-to-milliseconds conversion.

The public ``mdns_timeout`` constructor argument is documented in seconds, but
``zeroconf``'s ``async_request`` expects a timeout in **milliseconds**. The
resolver bridges the two by multiplying by 1000 before issuing the network
query. None of the existing tests assert the value handed to ``async_request``
(they stub it with ``return_value=True`` regardless of its arguments), so a
refactor dropping the ``* 1000`` would silently turn a 5-second timeout into a
5-millisecond one and the whole suite would still pass. These tests pin that
conversion against the observable call.
"""

import socket
from collections.abc import AsyncGenerator
from ipaddress import IPv4Address
from typing import Any
from unittest.mock import patch

import pytest
import pytest_asyncio

from aiohttp_asyncmdnsresolver._impl import (
    _FAMILY_TO_RESOLVER_CLASS,
    DEFAULT_TIMEOUT,
    AddressResolverIPv4,
)
from aiohttp_asyncmdnsresolver.api import AsyncMDNSResolver


class IPv4HostResolver(AddressResolverIPv4):
    """Patchable subclass so ``async_request`` can be intercepted."""


@pytest.fixture(autouse=True)
def make_resolvers_patchable() -> Any:
    """Route AF_INET lookups through the patchable subclass."""
    with patch.dict(_FAMILY_TO_RESOLVER_CLASS, {socket.AF_INET: IPv4HostResolver}):
        yield


@pytest_asyncio.fixture
async def make_resolver() -> AsyncGenerator[Any]:
    """Build resolvers via the public constructor and close them on teardown."""
    resolvers: list[AsyncMDNSResolver] = []

    def _factory(**kwargs: Any) -> AsyncMDNSResolver:
        resolver = AsyncMDNSResolver(**kwargs)
        resolvers.append(resolver)
        return resolver

    yield _factory
    for resolver in resolvers:
        await resolver.close()


async def _resolve_and_capture_timeout(
    resolver: AsyncMDNSResolver,
) -> tuple[Any, float]:
    """Resolve a cache-miss ``.local`` name and return the ``async_request`` args."""
    with (
        patch.object(IPv4HostResolver, "load_from_cache", return_value=False),
        patch.object(
            IPv4HostResolver, "async_request", return_value=True
        ) as async_request,
        patch.object(
            IPv4HostResolver,
            "ip_addresses_by_version",
            return_value=[IPv4Address("127.0.0.1")],
        ),
    ):
        result = await resolver.resolve("printer.local", family=socket.AF_INET)

    assert result[0]["host"] == "127.0.0.1"
    async_request.assert_called_once()
    zeroconf_arg, timeout_arg = async_request.call_args.args
    return zeroconf_arg, timeout_arg


@pytest.mark.asyncio
async def test_mdns_timeout_seconds_converted_to_milliseconds(
    make_resolver: Any,
) -> None:
    """A non-default ``mdns_timeout`` in seconds reaches zeroconf in ms."""
    resolver = make_resolver(mdns_timeout=2.5)

    zeroconf_arg, timeout_arg = await _resolve_and_capture_timeout(resolver)

    assert timeout_arg == 2500.0
    # The query is issued through the resolver's own zeroconf instance.
    assert zeroconf_arg is resolver._aiozc.zeroconf


@pytest.mark.asyncio
async def test_default_mdns_timeout_passed_in_milliseconds(
    make_resolver: Any,
) -> None:
    """The default ``mdns_timeout`` (seconds) is forwarded as milliseconds."""
    resolver = make_resolver()

    _, timeout_arg = await _resolve_and_capture_timeout(resolver)

    assert timeout_arg == DEFAULT_TIMEOUT * 1000
    assert timeout_arg == 5000.0
