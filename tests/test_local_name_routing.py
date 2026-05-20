"""Routing-boundary tests: which hostnames are treated as mDNS ``.local`` names.

The resolvers must send only genuine ``.local`` names down the mDNS path and
route everything else to unicast DNS. The positive cases (``host.local`` /
``host.local.``, mixed case) are covered in ``test_impl.py``; this module pins
the *negative* boundary so a future change to the suffix check (for example a
substring or dot-less ``endswith`` test) cannot silently misroute near-miss
names such as ``host.local.example.com``.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from aiohttp.resolver import ResolveResult

from aiohttp_asyncmdnsresolver.api import AsyncDualMDNSResolver, AsyncMDNSResolver

# Hostnames that look ``.local``-ish but are NOT in the mDNS ``.local`` domain.
# Each entry guards a specific plausible mis-implementation of the suffix check.
NON_MDNS_HOSTS = [
    "example.com",  # plain unicast name
    "mylocal",  # ends in "local" but has no leading dot
    "notlocal",  # ditto
    "foo.localdomain",  # contains ".local" only as a substring, not a suffix
    "local.example.com",  # starts with "local." but is not a .local name
    "host.local.example.com",  # ".local." appears mid-name, not as the suffix
]


@pytest.mark.parametrize(
    "resolver_cls", [AsyncMDNSResolver, AsyncDualMDNSResolver]
)
@pytest.mark.parametrize("host", NON_MDNS_HOSTS)
@pytest.mark.asyncio
async def test_non_local_names_route_to_unicast_dns(
    resolver_cls: type[AsyncMDNSResolver] | type[AsyncDualMDNSResolver],
    host: str,
) -> None:
    """Near-miss hostnames are resolved via unicast DNS, never over mDNS."""
    resolver = resolver_cls(mdns_timeout=0.1)
    sentinel = [ResolveResult(hostname=host, host="127.0.0.1")]  # type: ignore[typeddict-item]
    try:
        with (
            patch(
                "aiohttp_asyncmdnsresolver._impl.AsyncResolver.resolve",
                return_value=sentinel,
            ) as mock_unicast,
            patch.object(resolver, "_make_resolver") as mock_make_resolver,
        ):
            result = await resolver.resolve(host)

        assert result == sentinel
        mock_unicast.assert_awaited_once()
        # The mDNS resolver is only built once a name is classified as .local;
        # never building it proves the unicast path was taken.
        mock_make_resolver.assert_not_called()
    finally:
        await resolver.close()
