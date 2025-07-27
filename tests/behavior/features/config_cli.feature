Feature: Configuration CLI
  Scenarios covering configuration commands

  Scenario: Initialize configuration files
    Given a temporary work directory
    When I run `autoresearch config init --force` in a temporary directory
    Then the files "autoresearch.toml" and ".env" should be created

  Scenario: Validate configuration files
    Given a temporary work directory
    And I run `autoresearch config init --force` in a temporary directory
    When I run `autoresearch config validate`
    Then the CLI should exit successfully
