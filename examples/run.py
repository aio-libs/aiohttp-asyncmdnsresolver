"""Resolve a .local host over mDNS through an aiohttp ClientSession."""

import asyncio

import aiohttp

from aiohttp_asyncmdnsresolver.api import AsyncMDNSResolver


async def main() -> None:
    resolver = AsyncMDNSResolver()
    # aiohttp does not own a resolver passed to TCPConnector, so close it here.
    try:
        connector = aiohttp.TCPConnector(resolver=resolver)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get("http://KNKSADE41945.local.") as response:
                print(response.status)
    finally:
        await resolver.close()


asyncio.run(main())
