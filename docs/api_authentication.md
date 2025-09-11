# API Authentication

The HTTP API supports simple authentication using API keys or bearer tokens.
When either mechanism is configured, unauthenticated requests receive a
`401` response with a `WWW-Authenticate` header indicating the required
scheme.

## API keys

- Set `api.api_key` in your configuration to require a shared secret.
- Clients must include the value in the `X-API-Key` header.
- Multiple keys with different roles can be defined via `api.api_keys`.

## Bearer tokens

- Set `api.bearer_token` to enable bearer authentication.
- Clients send `Authorization: Bearer <token>` headers.

See [api.md](api.md) for a complete overview of available endpoints.

