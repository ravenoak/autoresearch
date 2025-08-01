"""Stub for the :mod:`fastmcp` package."""

import sys
import types

if "fastmcp" not in sys.modules:
    fastmcp_stub = types.ModuleType("fastmcp")

    class _FastMCP:
        def __init__(self, *_, **__):
            self.tools: dict[str, callable] = {}

        def tool(self, func):
            self.tools[func.__name__] = func
            return func

        async def call_tool(self, name, params):
            return await self.tools[name](**params)

    class _Client:
        def __init__(self, target):
            self.target = target

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def call_tool(self, name, params):
            if hasattr(self.target, "call_tool"):
                return await self.target.call_tool(name, params)
            return {}

    fastmcp_stub.FastMCP = _FastMCP
    fastmcp_stub.Client = _Client
    sys.modules["fastmcp"] = fastmcp_stub
