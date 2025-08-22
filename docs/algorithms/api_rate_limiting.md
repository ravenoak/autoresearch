# API Rate Limiting

Rate limiting protects the API from abuse and spreads capacity across
clients. The token bucket model grants each client a bucket with a
maximum capacity ``C`` and refill rate ``R`` tokens per second. Each
request removes one token; requests are denied when the bucket is empty.

## Complexity

Token checks and refills operate in constant time per request. Memory
usage is linear in the number of tracked clients.

## Edge Cases

- Distributed clocks can drift, causing inconsistent refill times.
- Buckets must expire for idle clients to avoid unbounded memory use.
- Bursty traffic may need jitter or leaky bucket smoothing.
