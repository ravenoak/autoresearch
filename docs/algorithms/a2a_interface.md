# A2A Interface

The A2A interface exposes Autoresearch through a minimal REST protocol. Clients
send JSON messages to the `/message` endpoint or query capabilities via
`/capabilities`.

## Protocol flow
- Client issues `GET /health` to confirm server readiness.
- Client sends `POST /message` with a query payload.
- Server responds with result data and metrics.

## Security assumptions
- Communication occurs over TLS with server certificates trusted by the client.
- API tokens are checked in constant time to reduce timing side channels.
- Requests are authenticated, rate limited, and sanitized before execution.
- Logs never persist secrets or raw user inputs.

See the [A2A and MCP Integration Guide](../a2a_mcp_integration.md) for
implementation details.
