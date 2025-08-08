Feature: Config API
  Background:
    Given the API server is running with config permissions

  Scenario: Retrieve current configuration
    When I request the config endpoint
    Then the response status should be 200
    And the response body should contain "reasoning_mode"

  Scenario: Update loops via the config endpoint
    When I update loops to 2 via the config endpoint
    Then the response status should be 200
    And the response body should show loops 2

  Scenario: Replace configuration via the config endpoint
    When I replace the configuration via the config endpoint
    Then the response status should be 200
    And the response body should contain "reasoning_mode"

  Scenario: Reload configuration
    When I reload the configuration
    Then the response status should be 200
    And the response body should contain "reasoning_mode"
