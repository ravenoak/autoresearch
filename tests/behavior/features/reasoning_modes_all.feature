@behavior @reasoning_modes
Feature: Reasoning modes coverage
  As a user
  I want to select different reasoning modes
  So the orchestrator adapts its execution

  Scenario Outline: selecting reasoning mode
    When I request reasoning mode "<mode>"
    Then bdd_context should record the reasoning mode "<mode>"

    Examples:
      | mode             |
      | direct           |
      | chain-of-thought |
      | dialectical      |
