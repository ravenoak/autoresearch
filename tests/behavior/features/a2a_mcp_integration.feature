@a2a_mcp @requires_distributed
Feature: A2A MCP integration
  Ensure the A2A interface can communicate with an MCP server and recover from failures.

  Background:
    Given a mock MCP server is available

  Scenario: Successful A2A MCP handshake
    When I perform an A2A MCP handshake
    Then the handshake result should be "42"

  Scenario: MCP handshake timeout handling
    When the A2A MCP handshake times out
    Then the A2A interface should report a timeout

  @error_recovery
  Scenario: Error recovery after handshake failure
    When the A2A MCP handshake fails once and then succeeds
    Then the handshake result should be "42"
