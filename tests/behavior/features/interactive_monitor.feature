Feature: Interactive Monitoring
  As a user
  I want to watch each cycle interactively
  So that I can provide feedback and exit cleanly

  Background:
    Given the application is running

  Scenario: Interactive monitoring
    When I start `autoresearch monitor run` and enter "test"
    Then the monitor should exit successfully

  Scenario: Exit immediately
    When I start `autoresearch monitor run` and enter "q"
    Then the monitor should exit successfully

  Scenario: Display metrics
    When I run `autoresearch monitor metrics`
    Then the monitor should exit successfully
    And the monitor output should display system metrics
