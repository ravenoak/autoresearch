"""Knowledge graph utilities and session pipelines.

This package exposes high-level helpers used by the context-aware search
runtime to derive lightweight knowledge graphs from retrieval snippets. The
modules follow the Google style guide for docstrings and are safe to import
from application entry points.
"""

from .graph import (
    GraphContradiction,
    GraphEntity,
    GraphExtractionSummary,
    GraphRelation,
    SessionGraphPipeline,
)

__all__ = [
    "GraphContradiction",
    "GraphEntity",
    "GraphExtractionSummary",
    "GraphRelation",
    "SessionGraphPipeline",
]
