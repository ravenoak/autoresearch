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

## Query expansion convergence

A simple simulation iteratively expands queries using stored entities.
After an initial enrichment step, further expansions return the same
string, indicating the process converges.

## HTTP session behavior

All network requests share a pooled `requests.Session`. The session
mounts an `HTTPAdapter` configured for connection reuse and up to three
retries on common server errors. `close_http_session` releases resources
when search work completes.
