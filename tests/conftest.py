"""Test conftest.py."""

from __future__ import annotations

import asyncio
import sys
import warnings

import pytest

if sys.platform == "win32":

    @pytest.fixture(scope="session")
    def event_loop_policy() -> asyncio.AbstractEventLoopPolicy:
        """Force a selector-based event loop on Windows.

        The default ``ProactorEventLoop`` does not support the socket
        ``add_reader``/``add_writer`` operations that zeroconf and aiodns rely
        on, so the suite needs a ``SelectorEventLoop`` on Windows. This is
        provided through pytest-asyncio's ``event_loop_policy`` fixture instead
        of calling ``asyncio.set_event_loop_policy()`` at import time: the event
        loop policy API is deprecated and slated for removal in Python 3.16, and
        because the suite runs with warnings-as-errors that import-time call
        aborts collection on Python 3.14+. Constructing the policy is wrapped in
        a ``DeprecationWarning`` filter for the same reason (the policy classes
        are deprecated on 3.14+); pytest-asyncio already suppresses the warning
        when it sets the returned policy.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            return asyncio.WindowsSelectorEventLoopPolicy()
