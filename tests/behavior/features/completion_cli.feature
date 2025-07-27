Feature: Completion CLI
  Scenario: Generate shell completion script
    When I run `autoresearch completion bash`
    Then the CLI should exit successfully
