"""Backward compatibility wrapper for ranking utilities.

The core implementation lives in :mod:`ranking_formula`. This module simply
re-exports its public functions so existing imports continue to work.
"""

from .ranking_formula import combine_scores, normalize_scores

__all__ = ["combine_scores", "normalize_scores"]
