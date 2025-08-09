Feature: MCP interface
  Tests interactions with the MCP client and server.

  Background:
    Given a mock MCP server is available

  Scenario: Successful query exchange
    When I send a MCP query "hello"
    Then I should receive a MCP response with answer "42"

  Scenario: Malformed request handling
    When I send a malformed MCP request
    Then the MCP client should receive an error response

  Scenario: Connection failure recovery
    When a connection interruption occurs and the client retries
    Then the client should eventually receive a MCP response with answer "42"
