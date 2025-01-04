import asyncio
import aiohttp
from aiohttp_asyncmdnsresolver.api import AsyncMDNSResolver


async def main():
    resolver = AsyncMDNSResolver()
    connector = aiohttp.TCPConnector(resolver=resolver)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get("http://KNKSADE41945.local.") as response:
            print(response.status)


asyncio.run(main())
