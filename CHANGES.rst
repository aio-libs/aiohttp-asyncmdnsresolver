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
