# Search Module Specification

This specification outlines expected behaviors for the
`autoresearch.search` module.

## Query Generation
- `Search.generate_queries` normalizes raw user text and returns a list of
  variants for external lookup.
- When `return_embeddings=True` it yields deterministic numeric embeddings of
  the cleaned query.

## Backend Selection
- `Search.external_lookup` uses `config.search.backends` to determine which
  registered backends to call.
- Results from each backend are cached via `SearchCache` using the query and
  backend name.
- Cached results must be reused on subsequent lookups without invoking the
  backend again.

## DomainAuthorityScore Ranking
- Credibility ranking relies on `DomainAuthorityScore` entries that map
  domains to scores in `[0,1]`. See
  [source credibility heuristics](algorithms/source_credibility.md).
- `Search.assess_source_credibility` assigns the configured score for known
  domains and a default of `0.5` otherwise.
- Final result ordering uses weighted combination of
  [BM25](algorithms/bm25.md),
  [semantic similarity](algorithms/semantic_similarity.md), and
  [domain authority scores](algorithms/source_credibility.md). The formula
  is detailed in [search ranking](algorithms/search_ranking.md).

## Tests
Property-based tests in `tests/unit/test_relevance_ranking.py` verify:
- Results are returned in non-increasing order of `relevance_score`.
- Cached lookups avoid redundant backend calls while preserving ranking.
- Raising any component score increases the final `relevance_score`.
- Changing relevance weights alters ordering to reflect their emphasis.
