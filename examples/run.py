"""Resolve a .local host over mDNS through an aiohttp ClientSession."""

import asyncio
import sys

import aiohttp

from aiohttp_asyncmdnsresolver.api import AsyncMDNSResolver

# Pass a host as the first argument; falls back to a generic placeholder.
DEFAULT_HOST = "localhost.local."


async def main(host: str) -> None:
    # aiohttp does not own a resolver passed to TCPConnector, so use the
    # resolver as an async context manager to close it on exit.
    async with AsyncMDNSResolver() as resolver:
        connector = aiohttp.TCPConnector(resolver=resolver)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(f"http://{host}") as response:
                print(response.status)


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    asyncio.run(main(host))
