# Search

Autoresearch combines multiple signals to rank documents and manages
HTTP sessions for external lookups.

## Ranking proofs

Search results use a weighted sum of [BM25](bm25.md) keyword matching,
[semantic similarity](semantic_similarity.md), and
[source credibility](source_credibility.md). The combined score is
proven monotonic: increasing any component increases the final
relevance. Weight normalization ensures convergence as detailed in
[relevance_ranking.md](relevance_ranking.md).

## Ranking convergence

The
[ranking_convergence.py](../../src/autoresearch/search/ranking_convergence.py)
simulation ranks sample documents multiple times. The ordering stabilizes
after the first pass, demonstrating convergence of the weighted relevance
formula.

## Query expansion convergence

A simple simulation iteratively expands queries using stored entities.
After an initial enrichment step, further expansions return the same
string, indicating the process converges.

## Retry algorithm

`get_http_session` configures a pooled session with a
[Retry](https://urllib3.readthedocs.io/en/stable/reference/urllib3.util.html#urllib3.util.retry.Retry)
strategy using three attempts and exponential backoff. The
[simulate_rate_limit.py](../../src/autoresearch/search/simulate_rate_limit.py)
tool models backoff delays of 0.2, 0.4, and 0.8 seconds for successive
retries, illustrating graceful handling of transient server errors.

## HTTP session behavior

All network requests share a pooled `requests.Session`. The session
mounts an `HTTPAdapter` configured for connection reuse and up to three
retries on common server errors. `close_http_session` releases resources
when search work completes.
