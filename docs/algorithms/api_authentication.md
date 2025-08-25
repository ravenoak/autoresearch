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
5. On success the request proceeds. Missing or invalid credentials trigger a
   **401 Unauthorized** response with messages such as ``Missing API key``,
   ``Invalid API key``, ``Missing token``, or ``Invalid token``. Authenticated
   clients lacking required permissions receive **403 Forbidden** with an
   ``Insufficient permissions`` detail.

## Configuration

Credentials are defined in `autoresearch.toml` under `[api]`:

- `api_key` – single shared key.
- `api_keys` – mapping of keys to roles.
- `bearer_token` – value for the `Authorization` header.

Roles gain capabilities via `[api.role_permissions]` with entries such as
`query` or `docs`.

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

naive_range = max(naive_times) - min(naive_times)
secure_range = max(secure_times) - min(secure_times)
print(f"naive range: {naive_range:.6f}")
print(f"secure range: {secure_range:.6f}")
```

Plotting `naive_times` shows longer durations when more prefix characters match,
while `secure_times` remain flat. This supports the correctness of the
constant-time strategy.

The `secure_range` output approaches zero, showing constant-time behavior even
when token prefixes overlap. Integration coverage lives in
[tests/integration/test_api_auth.py](../../tests/integration/test_api_auth.py).

## Error paths

See [API auth error paths](api_auth_error_paths.md) for failure scenarios and
responses.

## Conclusion

By combining explicit handshake steps, a clear threat model, and constant-time
verification, the API guards against token disclosure and timing attacks.
