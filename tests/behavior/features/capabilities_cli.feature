Feature: Capabilities CLI
  Scenario: List available capabilities
    When I run `autoresearch capabilities`
    Then the CLI should exit successfully
