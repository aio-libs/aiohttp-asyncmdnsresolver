=========
Changelog
=========

..
    You should *NOT* be adding new change log entries to this file, this
    file is managed by towncrier. You *may* edit previous change logs to
    fix problems like typo corrections or such.
    To add a new change log entry, please see
    https://pip.pypa.io/en/latest/development/#adding-a-news-entry
    we named the news folder "changes".

    WARNING: Don't drop the next directive!

.. towncrier release notes start

v0.2.0
======

*(2026-05-20)*


Bug fixes
---------

- Matched the ``.local`` mDNS suffix case-insensitively so hostnames such as ``MyHost.LOCAL`` are routed through mDNS as required by :rfc:`6762` -- by :user:`aiolibsbot`.

  *Related issues and pull requests on GitHub:*
  :issue:`65`.

- Cancelled the in-flight mDNS and DNS lookup tasks when ``AsyncDualMDNSResolver.resolve()`` is itself cancelled, so a cancelled lookup no longer orphans tasks that keep running against the shared ``zeroconf`` instance -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`69`.

- Made resolver ``close()`` idempotent -- a second call on a resolver that owns
  its :class:`~zeroconf.asyncio.AsyncZeroconf` no longer raises
  :exc:`AttributeError` -- by :user:`aiolibsbot`.

  *Related issues and pull requests on GitHub:*
  :issue:`74`.

- Stopped :class:`~aiohttp_asyncmdnsresolver.api.AsyncDualMDNSResolver` from returning the same address twice when the mDNS and DNS resolvers agree on a ``.local`` name -- by :user:`aiolibsbot`.

  *Related issues and pull requests on GitHub:*
  :issue:`87`.


Features
--------

- Added async context manager support to :class:`~aiohttp_asyncmdnsresolver.api.AsyncMDNSResolver` and :class:`~aiohttp_asyncmdnsresolver.api.AsyncDualMDNSResolver`, so ``async with`` closes the resolver automatically -- by :user:`aiolibsbot`.

  *Related issues and pull requests on GitHub:*
  :issue:`90`.


Removals and backward incompatible breaking changes
---------------------------------------------------

- Dropped Python 3.9 support; the minimum supported Python version is now 3.10 -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`62`.


Improved documentation
----------------------

- Corrected the public API module docstring (it described an unrelated project), fixed a grammar error in the package docstring, and normalized the indentation of the class directives in the API reference so the parameter lists render correctly, and added an intersphinx mapping to ``python-zeroconf`` so the ``async_zeroconf`` parameter cross-references resolve under the nitpicky docs build -- by :user:`aiolibsbot`.

  *Related issues and pull requests on GitHub:*
  :issue:`67`.

- Fixed the README quick-start example leaking the resolver: a resolver passed to ``aiohttp.TCPConnector`` is owned by the caller, so it is now closed in a ``finally`` block -- by :user:`aiolibsbot`.

  *Related issues and pull requests on GitHub:*
  :issue:`80`.

- Completed the documentation landing page: filled the empty Introduction section, added an installation snippet, and added a runnable usage example that closes the resolver in a ``finally`` block. Also fixed the same resolver leak in the ``AsyncMDNSResolver`` reference example -- by :user:`aiolibsbot`.

  *Related issues and pull requests on GitHub:*
  :issue:`84`.

- Documented the :meth:`~aiohttp_asyncmdnsresolver.api.AsyncMDNSResolver.resolve` and :meth:`~aiohttp_asyncmdnsresolver.api.AsyncMDNSResolver.close` methods of :class:`~aiohttp_asyncmdnsresolver.api.AsyncMDNSResolver` and :class:`~aiohttp_asyncmdnsresolver.api.AsyncDualMDNSResolver` in the API reference, including the ``.local`` routing behaviour and the :class:`~zeroconf.asyncio.AsyncZeroconf` ownership semantics of :meth:`~aiohttp_asyncmdnsresolver.api.AsyncMDNSResolver.close` -- by :user:`aiolibsbot`.

  *Related issues and pull requests on GitHub:*
  :issue:`85`.

- Added a usage example for :class:`~aiohttp_asyncmdnsresolver.api.AsyncDualMDNSResolver` in the API reference and documented the ``family`` parameter of :meth:`~aiohttp_asyncmdnsresolver.api.AsyncMDNSResolver.resolve` (``socket.AF_INET``, ``socket.AF_INET6`` and ``socket.AF_UNSPEC``). Also clarified that ``mdns_timeout=None`` is cache-only, the same as ``0`` -- by :user:`aiolibsbot`.

  *Related issues and pull requests on GitHub:*
  :issue:`86`.

- Documented :class:`~aiohttp_asyncmdnsresolver.api.AsyncDualMDNSResolver` in the README quick start so the landing page covers the full public API, not just :class:`~aiohttp_asyncmdnsresolver.api.AsyncMDNSResolver` -- by :user:`aiolibsbot`.

  *Related issues and pull requests on GitHub:*
  :issue:`89`.


Packaging updates and notes for downstreams
-------------------------------------------

- The packaging metadata switched to including an SPDX license identifier introduced in :pep:`639` -- by :user:`cdce8p`.

  As a side effect, the minimum required version of ``setuptools`` increased to v77.

  *Related issues and pull requests on GitHub:*
  :issue:`36`.

- Fixed ``MANIFEST.in`` to graft the ``src/`` tree and dropped references to the non-existent ``packaging/`` directory and ``NOTICE`` file, removing spurious build warnings. The ``py.typed`` marker is now shipped explicitly via ``package-data``, and the distribution advertises the Python 3.10--3.13, CPython, PyPy, and ``Typing :: Typed`` classifiers -- by :user:`aiolibsbot`.

  *Related issues and pull requests on GitHub:*
  :issue:`68`.

- Added support for Python 3.14: the test matrix now runs against 3.14 and the distribution advertises the ``Programming Language :: Python :: 3.14`` classifier -- by :user:`aiolibsbot`.

  *Related issues and pull requests on GitHub:*
  :issue:`81`.


Contributor-facing changes
--------------------------

- Expanded the public-API regression test to cover ``AsyncDualMDNSResolver``,
  ``api.__all__``, and the ``aiohttp.resolver.AsyncResolver`` drop-in subclass
  guarantee for both resolvers.

  *Related issues and pull requests on GitHub:*
  :issue:`71`.

- Hardened the CI workflow: the default ``GITHUB_TOKEN`` is now restricted to
  ``contents: read``, and a concurrency group cancels superseded in-progress
  pull request runs to conserve CI resources -- by :user:`aiolibsbot`.

  *Related issues and pull requests on GitHub:*
  :issue:`72`.

- Enabled the mypy ``disallow_untyped_defs``, ``disallow_incomplete_defs``, and
  ``check_untyped_defs`` checks so that newly added functions in ``src/`` and
  ``tests/`` must carry complete type annotations -- by :user:`aiolibsbot`.

  *Related issues and pull requests on GitHub:*
  :issue:`73`.

- Migrated CI runners from ``actions/setup-python`` to ``astral-sh/setup-uv``
  so dependencies and Python interpreters are provisioned via ``uv`` instead
  of system ``pip`` -- by :user:`aiolibsbot`.

  *Related issues and pull requests on GitHub:*
  :issue:`76`.

- Replaced the ``pyupgrade`` pre-commit hook with Ruff's ``UP`` rule set so a
  single linter handles syntax modernization, targeting Python 3.10+
  -- by :user:`aiolibsbot`.

  *Related issues and pull requests on GitHub:*
  :issue:`78`.


----


v0.1.1
======

*(2025-02-14)*


Miscellaneous internal changes
------------------------------

- Improved MDNS resolver performance when the name is already in the cache -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`27`.


----


v0.1.0
======

*(2025-02-05)*


Features
--------

- Created the :class:`aiohttp_asyncmdnsresolver.api.AsyncDualMDNSResolver` class to resolve ``.local`` names using both mDNS and DNS -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`23`.


----


v0.0.3
======

*(2025-01-31)*


Bug fixes
---------

- Fixed imports not being properly sorted -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`21`.


----


v0.0.2
======

*(2025-01-30)*


Miscellaneous internal changes
------------------------------

- Migrated to using zeroconf's built-in resolver classes -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`19`.


----


v0.0.1
======

*(2025-01-05)*


Initial release


----
