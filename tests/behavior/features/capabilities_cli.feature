Feature: Capabilities CLI
  # See docs/api_reference/llm.md

  Scenario: List available capabilities
    Given the capabilities command environment is prepared
    When I run the capabilities command
    Then the CLI should exit successfully

  Scenario: Unknown capabilities option
    Given the capabilities command environment is prepared
    When I run `autoresearch capabilities --unknown`
    Then the CLI should report an error
