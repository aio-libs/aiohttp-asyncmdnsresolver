"""Public API of the aiohttp-asyncmdnsresolver library."""

from ._impl import AsyncDualMDNSResolver, AsyncMDNSResolver

__all__ = ("AsyncMDNSResolver", "AsyncDualMDNSResolver")
