# Api

FastAPI app aggregator for Autoresearch. See these algorithm references:

- [API authentication](../algorithms/api_authentication.md)
- [Error paths](../algorithms/api_auth_error_paths.md)
- [API rate limiting](../algorithms/api_rate_limiting.md)
- [API streaming](../algorithms/api_streaming.md)

## Authentication flow

Clients authenticate with an API key in the `X-API-Key` header or a bearer
token in the `Authorization` header. The `AuthMiddleware` checks these
credentials on every request and assigns a role to the connection. Endpoints
use a `require_permission` dependency to verify that the role has access to a
given resource.

Requests without credentials return **401** with a descriptive message such as
`Missing API key`, `Missing token`, or `Missing API key or token` when both
credentials are configured. Invalid API keys or bearer tokens return **401**
with `Invalid API key` or `Invalid token`. Authenticated clients lacking
permission receive **403** `Insufficient permissions`. Streaming and webhook
requests follow the same rules.

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
    - [tests/integration/test_api_auth_middleware.py][t7]
    - [tests/integration/test_api_streaming.py][t8]
    - [tests/integration/test_api_docs.py][t9]

[m1]: ../../src/autoresearch/api/
[t1]: ../../tests/unit/test_api.py
[t2]: ../../tests/unit/test_api_error_handling.py
[t3]: ../../tests/unit/test_api_imports.py
[t4]: ../../tests/unit/test_api_auth_middleware.py
[t5]: ../../tests/unit/test_api_auth_deps.py
[t6]: ../../tests/integration/test_api_auth.py
[t7]: ../../tests/integration/test_api_auth_middleware.py
[t8]: ../../tests/integration/test_api_streaming.py
[t9]: ../../tests/integration/test_api_docs.py
