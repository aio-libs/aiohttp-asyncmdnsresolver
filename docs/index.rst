.. aiohttp_asyncmdnsresolver documentation master file, created by
   sphinx-quickstart on Mon Aug 29 19:55:36 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

aiohttp-asyncmdnsresolver
=========================

This module provides an ``aiohttp`` resolver that supports mDNS, which uses the ``zeroconf`` library
to resolve mDNS queries.

Introduction
------------

Usage
-----

The API provides a single ``AsyncMDNSResolver`` class that can be
used to resolve mDNS queries and fallback to ``AsyncResolver`` for
non-MDNS hosts.

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
