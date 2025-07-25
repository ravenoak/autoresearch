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

  Scenario: Display graph
    When I run `autoresearch monitor graph`
    Then the monitor should exit successfully
    And the monitor output should display graph data

  Scenario: Display TUI graph
    When I run `autoresearch monitor graph --tui`
    Then the monitor should exit successfully
    And the monitor output should display graph data

  Scenario: Visualize search results
    When I run `autoresearch search "Test graph" --visualize`
    Then the search command should exit successfully
    And the search output should display graph data

  Scenario: Record resource usage
    When I run `autoresearch monitor resources --duration 1`
    Then the monitor should exit successfully
    And the monitor output should display resource usage

  Scenario: Start monitoring service
    When I run `autoresearch monitor start --interval 0.1`
    Then the monitor should exit successfully
    And the monitor output should indicate it started
