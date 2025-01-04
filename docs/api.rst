.. _aiohttp_asyncmdnsresolver-api:

=========
Reference
=========

.. module:: aiohttp_asyncmdnsresolver.api

The only public *aiohttp_asyncmdnsresolver.api* class is :class:`AsyncMDNSResolver`:

.. doctest::

   >>> from aiohttp_asyncmdnsresolver.api import AsyncMDNSResolver


.. class:: AsyncMDNSResolver(*args*, *, async_zeroconf, timeout, **kwargs)

   This class functions the same as ``aiohttp.resolver.AsyncResolver``,
   but with the added ability to resolve mDNS queries.

    :param ``AsyncZeroconf`` async_zeroconf: If an ``AsyncZeroconf`` instance is
        passed, it will be used to resolve mDNS queries. If not, a new
        instance will be created.

    :param float timeout: The timeout for the mDNS query in seconds. If not provided
        the default timeout is 5 seconds.

   Example::

       from aiohttp_asyncmdnsresolver.api import AsyncMDNSResolver

       resolver = AsyncMDNSResolver()
       connector = aiohttp.TCPConnector(resolver=resolver)
       async with aiohttp.ClientSession(connector=connector) as session:
           async with session.get("http://KNKSADE41945.local.") as response:
               print(response.status)
