Feature: Interactive Monitoring
  As a user
  I want to watch each cycle interactively
  So that I can provide feedback and exit cleanly

  Background:
    Given the application is running

  Scenario: Interactive monitoring
    When I start `autoresearch monitor` and enter "test"
    Then the monitor should exit successfully

  Scenario: Exit immediately
    When I start `autoresearch monitor` and enter "q"
    Then the monitor should exit successfully
