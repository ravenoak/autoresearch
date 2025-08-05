Feature: Interface test commands
  Scenarios for MCP and A2A interface testing utilities

  Scenario: Run MCP interface tests
    When I run `autoresearch test_mcp --host 127.0.0.1 --port 8080`
    Then the CLI should exit successfully

  Scenario: Fail to connect to MCP server
    When I run `autoresearch test_mcp --port 9`
    Then the CLI should exit with an error

  Scenario: Run A2A interface tests
    When I run `autoresearch test_a2a --host 127.0.0.1 --port 8765`
    Then the CLI should exit successfully

  Scenario: Fail to connect to A2A server
    When I run `autoresearch test_a2a --port 9`
    Then the CLI should exit with an error
