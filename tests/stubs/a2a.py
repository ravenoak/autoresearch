"""Stub for the optional :mod:`a2a` dependency."""

import sys
import types

if "a2a" not in sys.modules:
    a2a_stub = types.ModuleType("a2a")
    sys.modules["a2a"] = a2a_stub

    client_stub = types.ModuleType("a2a.client")

    def _missing(*_a, **_k):
        raise ImportError("A2A SDK not installed")

    client_stub.__getattr__ = lambda _n: _missing()
    sys.modules["a2a.client"] = client_stub

    utils_stub = types.ModuleType("a2a.utils")
    message_stub = types.ModuleType("a2a.utils.message")

    def new_agent_text_message(content=""):
        msg = types.SimpleNamespace(content=content, metadata={})
        return msg

    message_stub.new_agent_text_message = new_agent_text_message
    sys.modules["a2a.utils"] = utils_stub
    sys.modules["a2a.utils.message"] = message_stub
    sys.modules["a2a.types"] = types.ModuleType("a2a.types")
