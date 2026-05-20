.. _aiohttp_asyncmdnsresolver-api:

=========
Reference
=========

.. module:: aiohttp_asyncmdnsresolver.api

The only public *aiohttp_asyncmdnsresolver.api* classes are :class:`AsyncMDNSResolver`
and :class:`AsyncDualMDNSResolver`:

.. doctest::

   >>> from aiohttp_asyncmdnsresolver.api import AsyncMDNSResolver


.. class:: AsyncMDNSResolver(*args, *, async_zeroconf=None, mdns_timeout=5.0, **kwargs)

   This class functions the same as ``aiohttp.resolver.AsyncResolver``,
   but with the added ability to resolve mDNS queries.

   :param async_zeroconf: If an :class:`~zeroconf.asyncio.AsyncZeroconf` instance is
      passed, it will be used to resolve mDNS queries. If not, a new
      instance will be created.
   :type async_zeroconf: ~zeroconf.asyncio.AsyncZeroconf

   :param float mdns_timeout: The timeout for the mDNS query in seconds. If not provided
      the default timeout is 5 seconds. If the mdns_timeout is set to ``0`` or
      ``None``, the query will only use the cache and will not perform a new
      query on the network.

   Example::

       import aiohttp
       from aiohttp_asyncmdnsresolver.api import AsyncMDNSResolver

       resolver = AsyncMDNSResolver()
       try:
           connector = aiohttp.TCPConnector(resolver=resolver)
           async with aiohttp.ClientSession(connector=connector) as session:
               async with session.get("http://KNKSADE41945.local.") as response:
                   print(response.status)
       finally:
           await resolver.close()

   The resolver also supports the async context manager protocol, which closes
   it automatically on exit -- ``aiohttp.TCPConnector`` does not take ownership
   of a resolver passed to it, so this is the recommended way to avoid leaking
   an internally created :class:`~zeroconf.asyncio.AsyncZeroconf` instance. If
   ``async_zeroconf`` was supplied by the caller, that instance is not closed
   by the resolver and remains the caller's responsibility to manage, even when
   using ``async with`` on the resolver::

       import aiohttp
       from aiohttp_asyncmdnsresolver.api import AsyncMDNSResolver

       async with AsyncMDNSResolver() as resolver:
           connector = aiohttp.TCPConnector(resolver=resolver)
           async with aiohttp.ClientSession(connector=connector) as session:
               async with session.get("http://KNKSADE41945.local.") as response:
                   response.raise_for_status()

   .. method:: resolve(host, port=0, family=socket.AF_INET)
      :async:

      Resolve *host* and return a list of ``aiohttp.abc.ResolveResult`` mappings.

      Names in the ``.local`` domain (matched case-insensitively, per
      :rfc:`6762`) are resolved over mDNS using ``zeroconf``; every other name
      is delegated to ``aiohttp.resolver.AsyncResolver``. mDNS lookups consult
      the ``zeroconf`` cache first and only send a query on the network when the
      cache misses. Raises ``OSError`` when the name cannot be resolved.

      *family* selects the address family to resolve. The supported values are
      ``socket.AF_INET`` (the default, IPv4 only), ``socket.AF_INET6`` (IPv6
      only) and ``socket.AF_UNSPEC`` (both IPv4 and IPv6).

   .. method:: close()
      :async:

      Close the resolver and release its resources. When the
      :class:`~zeroconf.asyncio.AsyncZeroconf` instance was created internally
      (no ``async_zeroconf`` was supplied to the constructor) it is closed as
      well; an externally supplied instance is left open for the caller to
      manage.


.. class:: AsyncDualMDNSResolver(*args, *, async_zeroconf=None, mdns_timeout=5.0, **kwargs)

   This resolver is a variant of :class:`AsyncMDNSResolver` that resolves ``.local``
   names with both mDNS and regular DNS. It takes the same arguments as
   :class:`AsyncMDNSResolver`, and is used in the same way.

   - The first successful result from either resolver is returned.
   - If both resolvers fail, an exception is raised.
   - If both resolvers return results at the same time, the results are
     combined and duplicates are removed.

   Example::

       import aiohttp
       from aiohttp_asyncmdnsresolver.api import AsyncDualMDNSResolver

       resolver = AsyncDualMDNSResolver()
       try:
           connector = aiohttp.TCPConnector(resolver=resolver)
           async with aiohttp.ClientSession(connector=connector) as session:
               async with session.get("http://printer.local.") as response:
                   print(response.status)
       finally:
           await resolver.close()

   .. method:: resolve(host, port=0, family=socket.AF_INET)
      :async:

      Behaves like :meth:`AsyncMDNSResolver.resolve`, except that ``.local``
      names are resolved over mDNS and unicast DNS concurrently following the
      rules above. Non-``.local`` names are delegated to
      ``aiohttp.resolver.AsyncResolver``. Raises ``OSError`` when neither
      resolver can resolve the name.

   .. method:: close()
      :async:

      Close the resolver and release its resources, with the same ownership
      semantics as :meth:`AsyncMDNSResolver.close`.
