Feature: Server commands
  Scenario: Display help for serve
    When I run `autoresearch serve --help`
    Then the CLI should exit successfully

  Scenario: Display help for serve-a2a
    When I run `autoresearch serve-a2a --help`
    Then the CLI should exit successfully
