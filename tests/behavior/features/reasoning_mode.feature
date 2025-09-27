# Feature covers reasoning modes: direct, chain-of-thought, dialectical, unsupported
@behavior @reasoning_modes
Feature: Reasoning Mode Selection
  As a user
  I want to choose how the system reasons
  So that agent execution adapts accordingly

  Background:
    Given loops is set to 2 in configuration

  Scenario: Default reasoning mode is dialectical
    Given loops is set to 1 in configuration
    When I run the orchestrator on query "mode test"
    Then the loops used should be 1
    And the reasoning mode selected should be "dialectical"
    And the agent groups should be "Synthesizer; Contrarian; FactChecker"
    And the agents executed should be "Synthesizer, Contrarian, FactChecker"

  Scenario: Direct mode runs Synthesizer only
    Given reasoning mode is "direct"
    When I run the orchestrator on query "mode test"
    Then the loops used should be 1
    And the reasoning mode selected should be "direct"
    And the agent groups should be "Synthesizer"
    And the agents executed should be "Synthesizer"

  Scenario: Auto mode exits after the scout pass
    Given reasoning mode is "auto"
    And gate policy forces exit
    When I run the orchestrator on query "mode test"
    Then the loops used should be 1
    And the reasoning mode selected should be "auto"
    And the agent groups should be "Synthesizer; Contrarian; FactChecker"
    And the agents executed should be "Synthesizer"

  Scenario: Auto mode escalates to debate
    Given reasoning mode is "auto"
    And gate policy forces debate
    When I run the orchestrator on query "mode test"
    Then the loops used should be 2
    And the reasoning mode selected should be "auto"
    And the agent groups should be "Synthesizer; Contrarian; FactChecker"
    And the agents executed should be "Synthesizer, Contrarian, FactChecker"

  Scenario: Chain-of-thought mode loops Synthesizer
    Given reasoning mode is "chain-of-thought"
    When I run the orchestrator on query "mode test"
    Then the loops used should be 2
    And the reasoning mode selected should be "chain-of-thought"
    And the agent groups should be "Synthesizer; Contrarian; FactChecker"
    And the agents executed should be "Synthesizer, Synthesizer"

  Scenario: Chain-of-thought reasoning with a realistic query
    Given reasoning mode is "chain-of-thought"
    When I run the orchestrator on query "How do airplanes fly?"
    Then the loops used should be 2
    And the reasoning mode selected should be "chain-of-thought"
    And the agent groups should be "Synthesizer; Contrarian; FactChecker"
    And the agents executed should be "Synthesizer, Synthesizer"

  Scenario: Dialectical mode with custom Primus start
    Given loops is set to 1 in configuration
    And reasoning mode is "dialectical"
    And primus start is 1
    When I run the orchestrator on query "mode test"
    Then the loops used should be 1
    And the reasoning mode selected should be "dialectical"
    And the agent groups should be "Synthesizer; Contrarian; FactChecker"
    And the agents executed should be "Contrarian, FactChecker, Synthesizer"

  Scenario: Dialectical reasoning with a realistic query
    Given loops is set to 1 in configuration
    And reasoning mode is "dialectical"
    When I run the orchestrator on query "Why is the sky blue?"
    Then the loops used should be 1
    And the reasoning mode selected should be "dialectical"
    And the agent groups should be "Synthesizer; Contrarian; FactChecker"
    And the agents executed should be "Synthesizer, Contrarian, FactChecker"

  Scenario: Direct reasoning with a realistic query
    Given loops is set to 1 in configuration
    And reasoning mode is "direct"
    When I run the orchestrator on query "Why is the sky blue?"
    Then the loops used should be 1
    And the reasoning mode selected should be "direct"
    And the agent groups should be "Synthesizer"
    And the agents executed should be "Synthesizer"

  Scenario: Direct mode agent failure triggers fallback
    Given reasoning mode is "direct"
    When I run the orchestrator on query "mode test" with a failing agent
    Then the fallback agent should be "Synthesizer"
    And a recovery strategy "fallback_agent" should be recorded
    And recovery should be applied
    And the logs should include "recovery for Synthesizer"
    And the system state should be restored

  Scenario: Chain-of-thought mode agent failure triggers fallback
    Given reasoning mode is "chain-of-thought"
    When I run the orchestrator on query "mode test" with a failing agent
    Then the fallback agent should be "Synthesizer"
    And a recovery strategy "fallback_agent" should be recorded
    And recovery should be applied
    And the logs should include "recovery for Synthesizer"
    And the system state should be restored

  Scenario: Dialectical mode agent failure triggers fallback
    Given loops is set to 1 in configuration
    And reasoning mode is "dialectical"
    When I run the orchestrator on query "mode test" with a failing agent
    Then the fallback agent should be "Synthesizer"
    And a recovery strategy "fallback_agent" should be recorded
    And recovery should be applied
    And the logs should include "recovery for Synthesizer"
    And the system state should be restored

  Scenario: Loop overflow triggers recovery
    Given loops is set to 1 in configuration
    And reasoning mode is "dialectical"
    When I run the orchestrator on query "mode test" exceeding loop limit
    Then the fallback agent should be "Synthesizer"
    And a recovery strategy "fallback_agent" should be recorded
    And recovery should be applied
    And the logs should include "loop overflow"
    And the system state should be restored

  Scenario: Unsupported reasoning mode fails gracefully
    Given loops is set to 1 in configuration
    When I run the orchestrator on query "mode test" with unsupported reasoning mode "quantum"
    Then a reasoning mode error should be raised
    And no agents should execute
    And the system state should be restored
    And the logs should include "unsupported reasoning mode"

  Scenario: Planner research debate validate telemetry
    When I simulate a PRDV planner flow
    Then the planner react log should capture normalization warnings
    And the coordinator trace metadata should include unlock events
