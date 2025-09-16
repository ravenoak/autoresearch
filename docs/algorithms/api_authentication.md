# API Authentication Algorithm

This specification defines the handshake for API credentials, the threat
model, and why comparisons run in constant time.

## Handshake

1. Clients obtain credentials: API keys mapped to roles or a bearer token.
2. Each HTTP request sends credential headers:
   - `X-API-Key` carries an API key.
   - `Authorization: Bearer <token>` carries a bearer token.
   Clients may send both headers.
3. `AuthMiddleware` reloads the latest configuration via
   `ConfigLoader.load_config()` so hot-reloaded values apply before checks run.
4. If `[api].api_keys` is populated the middleware compares the provided key
   against each entry with `secrets.compare_digest`. Otherwise it checks a
   single `[api].api_key`. Missing or mismatched keys return **401** with an
   `API-Key` challenge.
5. When `[api].bearer_token` is set the middleware extracts the bearer token
   and verifies it with `verify_bearer_token`. Invalid tokens return **401**
   even if a valid API key was supplied. When authentication is configured but
   no credential succeeds the response includes the appropriate
   `WWW-Authenticate` scheme.
6. Successful validation assigns a role, populates
   `request.scope["state"].permissions` from `[api].role_permissions`, and
   stores the active challenge scheme. Downstream calls to
   `enforce_permission` return **401** for missing credentials and **403** for
   insufficient permissions.

When no credentials are configured the middleware leaves the role as
`anonymous` with an empty permission set, so unauthenticated deployments stay
accessible.

## Configuration

Credentials are defined in `autoresearch.toml` under `[api]`:

- `api_keys` – mapping of keys to roles. When present it takes precedence over
  `api_key`.
- `api_key` – single shared key used when `api_keys` is empty.
- `bearer_token` – value for the `Authorization` header.

Roles gain capabilities via `[api.role_permissions]` (for example `query` or
`docs`). Entries for `anonymous` and `user` control defaults for unauthenticated
and single-key clients.

## Permission coverage

Each route declares a required permission with `require_permission`:

- `query`: `POST /query`, `POST /query/stream`, `POST /query/batch`,
  `POST /query/async`, `GET /query/{query_id}`, and
  `DELETE /query/{query_id}`.
- `health`: `GET /health`.
- `capabilities`: `GET /capabilities`.
- `config`: `GET/PUT/POST/DELETE /config`.
- `metrics`: `GET /metrics` (available only when monitoring is enabled).
- `docs`: `GET /docs` and `GET /openapi.json`.

Roles missing the relevant permission reach `enforce_permission`, which raises
**403 Forbidden** even when authentication succeeds.

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
