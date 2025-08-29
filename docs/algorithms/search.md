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

### Proof of monotonic relevance

Let the score for document *d* be
$S_d = w_b B_d + w_s S_d + w_c C_d$ where each weight $w_*$ is
non\-negative and $w_b + w_s + w_c = 1$.
For any component, e.g. $B_d$, the partial derivative
$\partial S_d/\partial B_d = w_b \ge 0$.
Thus increasing $B_d$ strictly increases $S_d$ when $w_b > 0$.
The same argument applies to $S_d$ and $C_d$, establishing monotonicity.

## Ranking convergence

The
[ranking_convergence.py](../../scripts/ranking_convergence.py)
simulation ranks sample documents repeatedly. The ordering stabilizes
after the first pass, demonstrating convergence of the weighted
relevance formula.

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

### Proof of session recovery

The global session is stored in `_http_session`. When
`close_http_session` runs, it sets this variable to `None`. A subsequent
call to `get_http_session` detects the `None` value, constructs a fresh
session, and registers a cleanup hook. Therefore the system recovers
from session closure or transient failures without leaking resources.
