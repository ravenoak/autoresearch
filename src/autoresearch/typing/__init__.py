"""Typing helpers shared across the project.

This package exposes reusable Protocol definitions and type aliases that keep
runtime dependencies lightweight while ensuring static analysis remains
precise. Modules should import the most specific type available instead of
depending on vendor-specific classes directly.
"""

from .http import RequestsResponseProtocol, RequestsSessionProtocol

__all__ = [
    "RequestsResponseProtocol",
    "RequestsSessionProtocol",
]
