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
  [domain authority scores](algorithms/source_credibility.md). Results from
  different backends are first scored individually and then merged and
  re-ranked with the same weights to ensure consistent ordering across
  sources. Each component score is normalized to the `0`–`1` range before
  weighting. Semantic similarities from transformers and DuckDB vectors are
  averaged after normalization so hybrid and pure semantic searches operate
  on the same scale. Combined scores are normalized again and sorted in
  descending order. The math is detailed in
  [search ranking](specs/search_ranking.md).
  Simulation trials in
  [`ranking_convergence.py`](algorithms/relevance_ranking.md#simulation)
  report a mean convergence step of `1`, confirming the idempotent ranking.

## Vector extension fallback

- The DuckDB VSS extension is optional. `VSSExtensionLoader` installs it from
  the network and falls back to a stub at `extensions/vss/vss.duckdb_extension`
  when downloads fail. The stub disables vector search features but allows
  storage initialization to continue. See
  [duckdb_vss_fallback.md](duckdb_vss_fallback.md) for details.

## Tests
Property-based tests in `tests/unit/test_relevance_ranking.py` verify:
- Results are returned in non-increasing order of `relevance_score`.
- Cached lookups avoid redundant backend calls while preserving ranking.
- Raising any component score increases the final `relevance_score`.
- Changing relevance weights alters ordering to reflect their emphasis.
