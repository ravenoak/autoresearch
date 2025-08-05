Feature: First run experience
  Ensures the CLI greets users only on first launch when no configuration exists.

  Scenario: No config present shows welcome and prompt
    When I run the CLI without a config file
    Then the welcome banner and initialization prompt are shown

  Scenario: Config exists suppresses welcome
    When I run the CLI with an existing config file
    Then the welcome banner is suppressed
