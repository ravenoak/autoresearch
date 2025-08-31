# API Rate Limiting

Rate limiting protects the API from abuse and spreads capacity across
clients. The token bucket model grants each client a bucket with a
maximum capacity ``C`` and refill rate ``R`` tokens per second. Each
request removes one token; requests are denied when the bucket is empty.

## Derivations

Let ``L`` be the sustained limit in requests per second. To tolerate
bursts lasting ``T`` seconds the bucket must hold

\[
C = L T
\]

tokens, enough to cover the burst. The refill rate equals the sustained
limit,

\[
R = L,
\]

restoring one token per ``1 / L`` seconds. When the bucket is empty the
worst-case latency for a single request is the wait for one token,

\[
W = 1 / R.
\]

If a burst exceeds capacity by ``\Delta`` requests the final request
waits

\[
W = \Delta / R
\]

seconds before service.

## Complexity

Token checks and refills operate in constant time per request. Memory
usage is linear in the number of tracked clients.

## Edge Cases

- Distributed clocks can drift, causing inconsistent refill times.
- Buckets must expire for idle clients to avoid unbounded memory use.
- Bursty traffic may need jitter or leaky bucket smoothing.

## Verification

Property-based tests
[tests/unit/test_property_api_rate_limit_bounds.py](../../tests/unit/test_property_api_rate_limit_bounds.py)
generate random request patterns to confirm that a client never exceeds its
configured bound.

## Simulation

Automated tests confirm api rate limiting behavior.

- [Spec](../specs/api.md)
- [Tests](../../tests/unit/test_property_api_rate_limit_bounds.py)
