"""Asynchronous DNS resolver using mDNS for `aiohttp`."""

from __future__ import annotations

import socket
from typing import Any
from zeroconf import IPVersion
from zeroconf.asyncio import AsyncZeroconf, AsyncServiceInfo
from aiohttp.resolver import AsyncResolver, ResolveResult
from ipaddress import IPv4Address, IPv6Address


class IPv6orIPv4HostResolver(AsyncServiceInfo):
    """Resolve a host name to an IP address."""

    @property
    def _is_complete(self) -> bool:
        """The ServiceInfo has all expected properties."""
        return bool(self._ipv4_addresses) or bool(self._ipv6_addresses)


class IPv6HostResolver(AsyncServiceInfo):
    """Resolve a host name to an IP address."""

    @property
    def _is_complete(self) -> bool:
        """The ServiceInfo has all expected properties."""
        return bool(self._ipv6_addresses)


class IPv4HostResolver(AsyncServiceInfo):
    """Resolve a host name to an IP address."""

    @property
    def _is_complete(self) -> bool:
        """The ServiceInfo has all expected properties."""
        return bool(self._ipv4_addresses)


DEFAULT_TIMEOUT = 5.0

_FAMILY_TO_RESOLVER_CLASS = {
    socket.AF_INET: IPv4HostResolver,
    socket.AF_INET6: IPv6HostResolver,
    socket.AF_UNSPEC: IPv6orIPv4HostResolver,
}
_FAMILY_TO_IP_VERSION = {
    socket.AF_INET: IPVersion.V4Only,
    socket.AF_INET6: IPVersion.V6Only,
    socket.AF_UNSPEC: IPVersion.All,
}
_IP_VERSION_TO_FAMILY = {
    4: socket.AF_INET,
    6: socket.AF_INET6,
}
_NUMERIC_SOCKET_FLAGS = socket.AI_NUMERICHOST | socket.AI_NUMERICSERV


def _to_resolve_result(
    hostname: str, port: int, ipaddress: IPv4Address | IPv6Address
) -> ResolveResult:
    """Convert an IP address to a ResolveResult."""
    return ResolveResult(
        hostname=hostname,
        host=ipaddress.compressed,
        port=port,
        family=_IP_VERSION_TO_FAMILY[ipaddress.version],
        proto=0,
        flags=_NUMERIC_SOCKET_FLAGS,
    )


class AsyncMDNSResolver(AsyncResolver):
    """Use the `aiodns`/`zeroconf` packages to make asynchronous DNS lookups."""

    def __init__(
        self,
        *args: Any,
        async_zeroconf: AsyncZeroconf | None = None,
        mdns_timeout: float | None = DEFAULT_TIMEOUT,
        **kwargs: Any,
    ) -> None:
        """Initialize the resolver."""
        super().__init__(*args, **kwargs)
        self._mdns_timeout = mdns_timeout
        self._aiozc_owner = async_zeroconf is None
        self._aiozc = async_zeroconf or AsyncZeroconf()

    async def resolve(
        self, host: str, port: int = 0, family: socket.AddressFamily = socket.AF_INET
    ) -> list[ResolveResult]:
        """Resolve a host name to an IP address."""
        if host.endswith(".local") or host.endswith(".local."):
            return await self._resolve_mdns(host, port, family)
        return await super().resolve(host, port, family)

    async def _resolve_mdns(
        self, host: str, port: int, family: socket.AddressFamily
    ) -> list[ResolveResult]:
        """Resolve a host name to an IP address using mDNS."""
        resolver_class: type[AsyncServiceInfo] = _FAMILY_TO_RESOLVER_CLASS[family]
        ip_version: IPVersion = _FAMILY_TO_IP_VERSION[family]
        if host[-1] != ".":
            host += "."
        info = resolver_class(".local.", host, server=host)
        if (
            info.load_from_cache(self._aiozc.zeroconf)
            or (
                self._mdns_timeout
                and await info.async_request(
                    self._aiozc.zeroconf, self._mdns_timeout * 1000
                )
            )
        ) and (addresses := info.ip_addresses_by_version(ip_version)):
            return [_to_resolve_result(host, port, address) for address in addresses]
        raise OSError(None, "MDNS lookup failed")

    async def close(self) -> None:
        """Close the resolver."""
        if self._aiozc_owner:
            await self._aiozc.async_close()
        await super().close()
        self._aiozc = None  # type: ignore[assignment] # break ref cycles early
