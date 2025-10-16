Feature: Logging Separation and Format Control
  As a user or automation tool
  I want log messages separated from application output with appropriate formatting
  So that humans get readable output and machines get structured logs

  Background:
    Given the Autoresearch application is running

  Scenario: Default auto-detection in interactive terminal
    When I run `autoresearch search "test query"` in an interactive terminal
    Then log messages should use console format "[LEVEL] component: message"
    And application results should appear in markdown format without JSON logs

  Scenario: Explicit JSON format override
    When I run `autoresearch search "test query" --log-format json`
    Then all log messages should be in structured JSON format
    And application results should appear normally

  Scenario: Explicit console format override
    When I run `autoresearch search "test query" --log-format console`
    Then all log messages should use console format "[LEVEL] component: message"
    And application results should appear normally

  Scenario: Piped output defaults to JSON logs
    When I run `autoresearch search "test query" | cat`
    Then log messages should be in structured JSON format for machine parsing

  Scenario: Quiet logs suppress diagnostic messages
    When I run `autoresearch search "test query" --quiet-logs`
    Then only error and warning messages should appear
    And informational and debug messages should be suppressed

  Scenario: Environment variable overrides default format
    Given the environment variable "AUTORESEARCH_LOG_FORMAT" is set to "console"
    When I run `autoresearch search "test query"`
    Then log messages should use console format regardless of terminal type

  Scenario: Log separation in error scenarios
    When I run `autoresearch search "invalid query causing error"`
    Then error messages should appear in application output
    And diagnostic logs should follow the configured format (console or JSON)
    And error logs should not be duplicated in application output

  Scenario: Correlation IDs preserved in console format
    When I run `autoresearch search "test query"` with correlation tracking enabled
    Then console-format logs should include correlation IDs in brackets like "[req-12345]"
    And JSON-format logs should include correlation_id field
