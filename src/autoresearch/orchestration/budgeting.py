from __future__ import annotations

from ..config.models import ConfigModel


def _apply_adaptive_token_budget(config: ConfigModel, query: str) -> None:
    """Adjust ``config.token_budget`` based on query complexity and loops."""
    budget = getattr(config, "token_budget", None)
    if budget is None:
        return

    loops = getattr(config, "loops", 1)
    if loops > 1:
        budget = max(1, budget // loops)

    query_tokens = len(query.split())
    factor = getattr(config, "adaptive_max_factor", 20)
    buffer = getattr(config, "adaptive_min_buffer", 10)
    max_budget = query_tokens * factor
    if budget > max_budget:
        config.token_budget = max_budget
    elif budget < query_tokens:
        config.token_budget = query_tokens + buffer
    else:
        config.token_budget = budget
