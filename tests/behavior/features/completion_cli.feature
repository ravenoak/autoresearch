Feature: Completion CLI
  # See docs/quickstart_guides.md

  Scenario: Generate shell completion script
    When I run `autoresearch completion bash`
    Then the CLI should exit successfully

  Scenario: Unsupported shell argument
    When I run `autoresearch completion invalidshell`
    Then the CLI should report an error
