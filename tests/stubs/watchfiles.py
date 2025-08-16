"""Minimal stub for the :mod:`watchfiles` package."""

import sys
import types

if "watchfiles" not in sys.modules:
    watchfiles_stub = types.ModuleType("watchfiles")

    def watch(*_args, **_kwargs):
        if False:
            yield ("", "")

    watchfiles_stub.watch = watch
    sys.modules["watchfiles"] = watchfiles_stub
