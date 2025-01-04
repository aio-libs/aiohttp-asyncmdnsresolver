aiohttp-asyncmdnsresolver
=========================

The module provides a fast implementation of cached properties for Python 3.9+.

.. image:: https://github.com/aio-libs/aiohttp_asyncmdnsresolver/actions/workflows/ci-cd.yml/badge.svg
  :target: https://github.com/aio-libs/aiohttp_asyncmdnsresolver/actions?query=workflow%3ACI
  :align: right

.. image:: https://codecov.io/gh/aio-libs/aiohttp_asyncmdnsresolver/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/aio-libs/aiohttp_asyncmdnsresolver

.. image:: https://badge.fury.io/py/aiohttp_asyncmdnsresolver.svg
    :target: https://badge.fury.io/py/aiohttp_asyncmdnsresolver


.. image:: https://readthedocs.org/projects/aiohttp_asyncmdnsresolver/badge/?version=latest
    :target: https://aiohttp_asyncmdnsresolver.readthedocs.io


.. image:: https://img.shields.io/pypi/pyversions/aiohttp_asyncmdnsresolver.svg
    :target: https://pypi.python.org/pypi/aiohttp_asyncmdnsresolver

.. image:: https://img.shields.io/matrix/aio-libs:matrix.org?label=Discuss%20on%20Matrix%20at%20%23aio-libs%3Amatrix.org&logo=matrix&server_fqdn=matrix.org&style=flat
   :target: https://matrix.to/#/%23aio-libs:matrix.org
   :alt: Matrix Room — #aio-libs:matrix.org

.. image:: https://img.shields.io/matrix/aio-libs-space:matrix.org?label=Discuss%20on%20Matrix%20at%20%23aio-libs-space%3Amatrix.org&logo=matrix&server_fqdn=matrix.org&style=flat
   :target: https://matrix.to/#/%23aio-libs-space:matrix.org
   :alt: Matrix Space — #aio-libs-space:matrix.org

Introduction
------------

This module provides an ``aiohttp`` resolver that supports mDNS, which uses the ``zeroconf`` library
to resolve mDNS queries.

For full documentation please read https://aiohttp_asyncmdnsresolver.readthedocs.io.

Installation
------------

::

   $ pip install aiohttp_asyncmdnsresolver


Quick start
-----------

::

   import asyncio
   import aiohttp
   from aiohttp_asyncmdnsresolver.api import AsyncMDNSResolver

   async def main():
       resolver = AsyncMDNSResolver()
       connector = aiohttp.TCPConnector(resolver=resolver)
       async with aiohttp.ClientSession(connector=connector) as session:
           async with session.get('http://example.com') as response:
               print(response.status)
           async with session.get('http://xxx.local.') as response:
               print(response.status)

   asyncio.run(main())


API documentation
-----------------

The documentation is located at https://aiohttp_asyncmdnsresolver.readthedocs.io.

Source code
-----------

The project is hosted on GitHub_

Please file an issue on the `bug tracker
<https://github.com/aio-libs/aiohttp_asyncmdnsresolver/issues>`_ if you have found a bug
or have some suggestion in order to improve the library.


Authors and License
-------------------

It's *Apache 2* licensed and freely available.


.. _GitHub: https://github.com/aio-libs/aiohttp_asyncmdnsresolver
