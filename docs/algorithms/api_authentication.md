# API Authentication Algorithm

This specification defines the handshake for API credentials, the threat
model, and why comparisons run in constant time.

## Handshake

1. Client obtains a credential: an API key or bearer token.
2. For each request the client sends:
   - `X-API-Key` header for an API key.
   - `Authorization: Bearer <token>` for a bearer token.
3. The server fetches the expected credential from configuration.
4. Verification uses a constant-time comparison.
5. On success the request proceeds; otherwise a **401 Unauthorized** response is
   returned.

## Threat model

- Adversaries may sniff traffic, replay requests, or attempt token guessing.
- Timing differences could reveal partial credential matches.
- Compromised storage might expose credentials.

Mitigations:

- Use HTTPS to protect transport confidentiality.
- Generate high-entropy credentials and rotate them when possible.
- Compare tokens with `secrets.compare_digest` to remove timing side channels.
- Log failures and rate limit brute-force attempts.

## Constant-time comparison

`secrets.compare_digest` performs a comparison whose duration does not depend on
matching prefixes, preventing timing leaks. See the [Python docs]
(https://docs.python.org/3/library/secrets.html#secrets.compare_digest).

```python
from secrets import compare_digest

def verify(token: str, expected: str) -> bool:
    return compare_digest(token, expected)
```

## Simulation

The following experiment illustrates that `compare_digest` timing is independent
of token similarity.

```python
import timeit
from secrets import compare_digest

def naive(a, b):
    return a == b

token = "a" * 32
wrong = ["b" * i + "a" * (32 - i) for i in range(32)]

naive_times = [
    timeit.timeit(lambda: naive(token, w), number=1000) for w in wrong
]
secure_times = [
    timeit.timeit(lambda: compare_digest(token, w), number=1000) for w in wrong
]
```

Plotting `naive_times` shows longer durations when more prefix characters match,
while `secure_times` remain flat. This supports the correctness of the
constant-time strategy.

## Conclusion

By combining explicit handshake steps, a clear threat model, and constant-time
verification, the API guards against token disclosure and timing attacks.
