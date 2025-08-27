@a2a_mcp @requires_distributed
Feature: A2A MCP integration
  Ensure the A2A interface can communicate with an MCP server and recover from failures.

  Background:
    Given a mock MCP server is available

  Scenario: Successful A2A to MCP query
    When I send an A2A MCP query "hello"
    Then the MCP answer should be "42"

  Scenario: MCP timeout handling
    When the MCP query times out
    Then the A2A interface should report a timeout

  @error_recovery
  Scenario: Error recovery after MCP failure
    When the MCP query fails once and then succeeds
    Then the MCP answer should be "42"
