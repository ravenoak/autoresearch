# Api

FastAPI app aggregator for Autoresearch. See [API authentication
algorithm](../algorithms/api_authentication.md) and
[error paths](../algorithms/api_auth_error_paths.md) for credential handling
details, and [API rate limiting
model](../algorithms/api_rate_limiting.md) for load control guidance.

## Authentication flow

Clients authenticate with an API key in the `X-API-Key` header or a bearer
token in the `Authorization` header. The `AuthMiddleware` checks these
credentials on every request and assigns a role to the connection. Endpoints
use a `require_permission` dependency to verify that the role has access to a
given resource.

Requests without credentials return **401**. Invalid API keys or bearer
tokens and authenticated clients lacking permission return **403**.

## Configuration

Authentication settings live in `autoresearch.toml` under `[api]` or via
environment variables:

- `AUTORESEARCH_API__API_KEY`
- `AUTORESEARCH_API__API_KEYS`
- `AUTORESEARCH_API__BEARER_TOKEN`
- `AUTORESEARCH_API__ROLE_PERMISSIONS`

When both an API key and bearer token are set, either credential grants
access. Role permissions limit which endpoints a client may call.

## Threat model

API keys and tokens are shared secrets. Use HTTPS to avoid interception and
rotate credentials regularly. Tokens are compared using constant-time checks to
reduce timing attacks. Rate limiting mitigates brute-force attempts, and role
permissions constrain the impact of a leaked credential.

## Traceability

- Modules
  - [src/autoresearch/api/][m1]
  - Tests
    - [tests/unit/test_api.py][t1]
    - [tests/unit/test_api_error_handling.py][t2]
    - [tests/unit/test_api_imports.py][t3]
    - [tests/unit/test_api_auth_middleware.py][t4]
    - [tests/unit/test_api_auth_deps.py][t5]
    - [tests/integration/test_api_auth.py][t6]
    - [tests/integration/test_api_streaming.py][t7]
    - [tests/integration/test_api_docs.py][t8]

[m1]: ../../src/autoresearch/api/
[t1]: ../../tests/unit/test_api.py
[t2]: ../../tests/unit/test_api_error_handling.py
[t3]: ../../tests/unit/test_api_imports.py
[t4]: ../../tests/unit/test_api_auth_middleware.py
[t5]: ../../tests/unit/test_api_auth_deps.py
[t6]: ../../tests/integration/test_api_auth.py
[t7]: ../../tests/integration/test_api_streaming.py
[t8]: ../../tests/integration/test_api_docs.py
