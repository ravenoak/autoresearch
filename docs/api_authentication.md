# API Authentication

The HTTP API supports simple authentication using API keys or bearer tokens.
When either mechanism is configured, unauthenticated or invalid requests
receive a `401` response with a `WWW-Authenticate` header indicating the
required scheme.

## API keys

- Set `api.api_key` in your configuration to require a shared secret.
- Clients must include the value in the `X-API-Key` header.
- Missing or incorrect keys trigger `401` with `WWW-Authenticate: API-Key`.
- Multiple keys with different roles can be defined via `api.api_keys`.
- Each key maps to a role that grants permissions via `api.role_permissions`.
- Keys are validated and roles assigned before request bodies are read.
- If an `X-API-Key` header is present but invalid, the request is rejected
  even when a bearer token is supplied.

### Example

```bash
curl -i -H "X-API-Key: $AUTORESEARCH_API_KEY" \
  http://localhost:8000/metrics
```

A missing header yields:

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: API-Key
{"detail": "Missing API key"}
```

## Bearer tokens

- Set `api.bearer_token` to enable bearer authentication.
- Clients send `Authorization: Bearer <token>` headers.
- Bearer tokens authenticate requests when `api.bearer_token` is set.
- Tokens grant the `user` role.
- When API keys are configured, a valid bearer token can be used instead of an
  `X-API-Key`. Supplying an invalid API key still causes rejection.

## Roles and permissions

- Configure `api.role_permissions` to control which roles may access each
  endpoint.
- The default `anonymous` role has no permissions.
- Bearer tokens resolve to the `user` role unless overridden.
- Requests missing required permissions receive a `403` response.

See [api.md](api.md) for a complete overview of available endpoints.

