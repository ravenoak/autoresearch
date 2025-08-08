Feature: Visualize metrics CLI
  Scenario: Attempt to visualize metrics before implementation
    When I run `autoresearch visualize-metrics metrics.json metrics.png`
    Then the CLI should report the command is missing
