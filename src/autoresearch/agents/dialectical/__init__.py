"""Dialectical agents for multi-perspective reasoning."""

from .synthesizer import SynthesizerAgent
from .contrarian import ContrarianAgent
from .fact_checker import FactChecker

__all__ = ["SynthesizerAgent", "ContrarianAgent", "FactChecker"]
