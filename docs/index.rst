.. aiohttp_asyncmdnsresolver documentation master file, created by
   sphinx-quickstart on Mon Aug 29 19:55:36 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

aiohttp-asyncmdnsresolver
=========================

Introduction
------------

This module provides an ``aiohttp`` resolver that supports mDNS, using the
``zeroconf`` library to resolve ``.local`` host names. Any host name that is not
in the ``.local`` domain is delegated to ``aiohttp``'s standard ``AsyncResolver``,
so either resolver is a drop-in replacement for it.

Two resolver classes are provided:

:class:`~aiohttp_asyncmdnsresolver.api.AsyncMDNSResolver`
    Resolves ``.local`` names with mDNS only, and every other name with regular
    DNS.

:class:`~aiohttp_asyncmdnsresolver.api.AsyncDualMDNSResolver`
    Resolves ``.local`` names with **both** mDNS and regular DNS concurrently and
    returns the first successful result. Use this when ``.local`` names may also
    be served by a unicast DNS server.

Installation
------------

.. code-block:: console

   $ pip install aiohttp-asyncmdnsresolver

Usage
-----

Pass a resolver to an ``aiohttp.TCPConnector``. ``aiohttp`` does not take
ownership of a resolver supplied this way, so close it yourself when you are
done with it:

.. code-block:: python

   import asyncio

   import aiohttp
   from aiohttp_asyncmdnsresolver.api import AsyncMDNSResolver


   async def main() -> None:
       resolver = AsyncMDNSResolver()
       try:
           connector = aiohttp.TCPConnector(resolver=resolver)
           async with aiohttp.ClientSession(connector=connector) as session:
               async with session.get("http://example.com") as response:
                   print(response.status)
               async with session.get("http://xxx.local.") as response:
                   print(response.status)
       finally:
           await resolver.close()


   asyncio.run(main())

Swap :class:`~aiohttp_asyncmdnsresolver.api.AsyncMDNSResolver` for
:class:`~aiohttp_asyncmdnsresolver.api.AsyncDualMDNSResolver` to resolve ``.local``
names with both mDNS and unicast DNS at once.

API documentation
-----------------

Open :ref:`aiohttp_asyncmdnsresolver-api` for reading full list of available methods.

Source code
-----------

The project is hosted on GitHub_

Please file an issue on the `bug tracker
<https://github.com/aio-libs/aiohttp-asyncmdnsresolver/issues>`_ if you have found a bug
or have some suggestion in order to improve the library.

Authors and License
-------------------

It's *Apache 2* licensed and freely available.



Contents:

.. toctree::
   :maxdepth: 2

   api

.. toctree::
   :caption: What's new

   changes

.. toctree::
   :caption: Contributing

   contributing/guidelines

.. toctree::
   :caption: Maintenance

   contributing/release_guide


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _GitHub: https://github.com/aio-libs/aiohttp-asyncmdnsresolver
