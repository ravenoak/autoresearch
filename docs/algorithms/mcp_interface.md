# MCP Interface

The MCP interface uses the `fastmcp` library to exchange structured messages
between agents.

## Protocol flow
- Client establishes a connection to the MCP server.
- Client calls the `research` tool with the desired query.
- Server returns a JSON object containing the answer and metadata.

## Security assumptions
- The transport layer is authenticated and encrypted.
- Tool invocation is authorized through configuration loaded at startup.
- Timeouts guard against dead peers, and failures surface to callers.
- Returned data is validated before forwarding to downstream agents.

For more details see the [A2A and MCP Integration Guide](../a2a_mcp_integration.md).
