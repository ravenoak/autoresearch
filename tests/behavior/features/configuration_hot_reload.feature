Feature: Configuration & Hot Reload
  As a user or administrator
  I want the system to load settings from a central config file and reload them when changed
  So that agent roster, iteration loops, and storage options can be updated at runtime

  Background:
    Given the application is running with default configuration

  Scenario: Load configuration on startup
    When I start the application
    Then it should load settings from "autoresearch.toml"
    And the active agents should match the config file

  Scenario: Hot-reload on config change
    Given the application is running
    When I modify "autoresearch.toml" to enable a new agent
    Then the orchestrator should reload the configuration automatically
    And the new agent should be visible in the next iteration cycle
