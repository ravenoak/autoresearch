# Restore API parse and FastMCP handshake behaviour

## Context
`uv run --extra test pytest` shows API and MCP failures:
`tests/unit/test_api.py` complains that `autoresearch.api` no longer exposes a
`parse` helper, and `tests/unit/test_a2a_mcp_handshake.py` errors because
`FastMCP` cannot be constructed with the expected arguments.
【7be155†L170-L227】

## Dependencies
- [prepare-first-alpha-release](prepare-first-alpha-release.md)

## Acceptance Criteria
- `autoresearch.api.parse` or a replacement entry point is exported and covered
  by unit tests.
- FastMCP handshake helpers accept the arguments used in the tests and production
  code paths.
- API and MCP handshake tests pass without local patches.
- Documentation or release notes summarise the API and handshake changes.

## Status
Closed

## Resolution
- Restored the `autoresearch.api` surface by re-exporting rate-limit helpers,
  middleware, and the `parse` utility for compatibility with existing
  integrations.
- Updated FastMCP adapters to emit and accept `QueryRequestV1` and
  `QueryResponseV1` payloads, including structured error telemetry for Socratic
  recovery prompts.
- Added unit tests that assert success and failure flows for both the REST API
  and FastMCP handshake while exercising Socratic diagnostics.
- Documented the consolidated Python exports in `docs/api.md` so downstream
  clients can rely on the public surface without spelunking submodules.
