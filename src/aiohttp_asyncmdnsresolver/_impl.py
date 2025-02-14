"""Asynchronous DNS resolver using mDNS for `aiohttp`."""

from __future__ import annotations

import asyncio
import socket
import sys
from ipaddress import IPv4Address, IPv6Address
from typing import TYPE_CHECKING, Any, Union

from aiohttp.resolver import AsyncResolver, ResolveResult
from zeroconf import (
    AddressResolver,
    AddressResolverIPv4,
    AddressResolverIPv6,
    IPVersion,
)
from zeroconf.asyncio import AsyncZeroconf

DEFAULT_TIMEOUT = 5.0

ResolverType = Union[AddressResolver, AddressResolverIPv4, AddressResolverIPv6]

_FAMILY_TO_RESOLVER_CLASS: dict[
    socket.AddressFamily,
    type[AddressResolver] | type[AddressResolverIPv4] | type[AddressResolverIPv6],
] = {
    socket.AF_INET: AddressResolverIPv4,
    socket.AF_INET6: AddressResolverIPv6,
    socket.AF_UNSPEC: AddressResolver,
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


class _AsyncMDNSResolverBase(AsyncResolver):
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

    def _make_resolver(self, host: str, family: socket.AddressFamily) -> ResolverType:
        """Create an mDNS resolver."""
        resolver_class = _FAMILY_TO_RESOLVER_CLASS[family]
        if host[-1] != ".":
            host += "."
        return resolver_class(host)

    def _addresses_from_info_or_raise(
        self, info: ResolverType, family: socket.AddressFamily
    ) -> list[ResolveResult]:
        """Get addresses from info or raise OSError."""
        ip_version = _FAMILY_TO_IP_VERSION[family]
        if addresses := info.ip_addresses_by_version(ip_version):
            if TYPE_CHECKING:
                assert info.server is not None
                assert info.port is not None
            return [
                _to_resolve_result(info.server, info.port, address)
                for address in addresses
            ]
        raise OSError(None, "MDNS lookup failed")

    async def _resolve_mdns_by_request(self, info: ResolverType) -> bool:
        """Resolve a host name to an IP address using mDNS."""
        if not self._mdns_timeout:
            return False
        return await info.async_request(self._aiozc.zeroconf, self._mdns_timeout * 1000)

    async def _resolve_mdns(
        self, info: ResolverType, family: socket.AddressFamily
    ) -> list[ResolveResult]:
        """Resolve a host name to an IP address using mDNS."""
        await self._resolve_mdns_by_request(info)
        return self._addresses_from_info_or_raise(info, family)

    async def close(self) -> None:
        """Close the resolver."""
        if self._aiozc_owner:
            await self._aiozc.async_close()
        await super().close()
        self._aiozc = None  # type: ignore[assignment] # break ref cycles early


class AsyncMDNSResolver(_AsyncMDNSResolverBase):
    """Use the `aiodns`/`zeroconf` packages to make asynchronous DNS lookups."""

    async def resolve(
        self, host: str, port: int = 0, family: socket.AddressFamily = socket.AF_INET
    ) -> list[ResolveResult]:
        """Resolve a host name to an IP address."""
        if not host.endswith(".local") and not host.endswith(".local."):
            return await super().resolve(host, port, family)
        info = self._make_resolver(host, family)
        if info.load_from_cache(self._aiozc.zeroconf):
            return self._addresses_from_info_or_raise(info, family)
        return await self._resolve_mdns(info, family)


class AsyncDualMDNSResolver(_AsyncMDNSResolverBase):
    """Use the `aiodns`/`zeroconf` packages to make asynchronous DNS lookups.

    This resolver is a variant of `AsyncMDNSResolver` that resolves .local
    names with both mDNS and regular DNS.

    - The first successful result from either resolver is returned.
    - If both resolvers fail, an exception is raised.
    - If both resolvers return results at the same time, the results are
    combined and duplicates are removed.
    """

    async def resolve(
        self, host: str, port: int = 0, family: socket.AddressFamily = socket.AF_INET
    ) -> list[ResolveResult]:
        """Resolve a host name to an IP address."""
        if not host.endswith(".local") and not host.endswith(".local."):
            return await super().resolve(host, port, family)
        info = self._make_resolver(host, family)
        if info.load_from_cache(self._aiozc.zeroconf):
            return self._addresses_from_info_or_raise(info, family)
        resolve_via_mdns = self._resolve_mdns(info, family)
        resolve_via_dns = super().resolve(host, port, family)
        loop = asyncio.get_running_loop()
        if sys.version_info >= (3, 12):
            mdns_task = asyncio.Task(resolve_via_mdns, loop=loop, eager_start=True)
            dns_task = asyncio.Task(resolve_via_dns, loop=loop, eager_start=True)
        else:
            mdns_task = loop.create_task(resolve_via_mdns)
            dns_task = loop.create_task(resolve_via_dns)
        await asyncio.wait((mdns_task, dns_task), return_when=asyncio.FIRST_COMPLETED)
        if mdns_task.done() and mdns_task.exception():
            await asyncio.wait((dns_task,), return_when=asyncio.ALL_COMPLETED)
        elif dns_task.done() and dns_task.exception():
            await asyncio.wait((mdns_task,), return_when=asyncio.ALL_COMPLETED)
        resolve_results: list[ResolveResult] = []
        exceptions: list[BaseException] = []
        seen_results: set[tuple[str, int, str]] = set()
        for task in (mdns_task, dns_task):
            if task.done():
                if exc := task.exception():
                    exceptions.append(exc)
                else:
                    # If we have multiple results, we need to remove duplicates
                    # and combine the results. We put the mDNS results first
                    # to prioritize them.
                    for result in task.result():
                        result_key = (
                            result["hostname"],
                            result["port"],
                            result["host"],
                        )
                        if result_key not in seen_results:
                            seen_results.add(result_key)
                            resolve_results.append(result)
            else:
                task.cancel()
                try:
                    await task  # clear log traceback
                except asyncio.CancelledError:
                    if (
                        sys.version_info >= (3, 11)
                        and (current_task := asyncio.current_task())
                        and current_task.cancelling()
                    ):
                        raise

        if resolve_results:
            return resolve_results

        exception_strings = ", ".join(
            exc.strerror or str(exc) if isinstance(exc, OSError) else str(exc)
            for exc in exceptions
        )
        raise OSError(None, exception_strings)
