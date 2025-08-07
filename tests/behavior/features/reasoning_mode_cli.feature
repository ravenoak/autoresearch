@behavior
# Feature covers reasoning modes: direct, chain-of-thought, dialectical, unsupported
Feature: Reasoning mode via CLI
  As a user
  I want to override reasoning mode on the command line
  So that agent execution adapts accordingly

  Scenario: Direct mode via CLI
    Given loops is set to 2 in configuration
    When I run `autoresearch search "mode test" --mode direct`
    Then the CLI should exit successfully
    And the loops used should be 1
    And the reasoning mode selected should be "direct"
    And the agent groups should be "Synthesizer"
    And the agents executed should be "Synthesizer"
    And the reasoning steps should be "Synthesizer-1"
    And the metrics should record 1 cycles
    And the metrics should list agents "Synthesizer"

  Scenario: Chain-of-thought mode via CLI
    Given loops is set to 2 in configuration
    When I run `autoresearch search "mode test" --mode chain-of-thought`
    Then the CLI should exit successfully
    And the loops used should be 2
    And the reasoning mode selected should be "chain-of-thought"
    And the agent groups should be "Synthesizer; Contrarian; FactChecker"
    And the agents executed should be "Synthesizer, Synthesizer"
    And the reasoning steps should be "Synthesizer-1; Synthesizer-2"
    And the metrics should record 2 cycles
    And the metrics should list agents "Synthesizer"

  Scenario: Dialectical mode via CLI
    Given loops is set to 1 in configuration
    When I run `autoresearch search "mode test" --mode dialectical`
    Then the CLI should exit successfully
    And the loops used should be 1
    And the reasoning mode selected should be "dialectical"
    And the agent groups should be "Synthesizer; Contrarian; FactChecker"
    And the agents executed should be "Synthesizer, Contrarian, FactChecker"
    And the reasoning steps should be "Synthesizer-1; Contrarian-2; FactChecker-3"
    And the metrics should record 1 cycles
    And the metrics should list agents "Synthesizer, Contrarian, FactChecker"

  Scenario: Mode switching within a session via CLI
    Given loops is set to 2 in configuration
    When I run `autoresearch search "mode test" --mode direct`
    And I run `autoresearch search "mode test" --mode chain-of-thought`
    Then the CLI should exit successfully
    And the loops used should be 2
    And the reasoning mode selected should be "chain-of-thought"
    And the agent groups should be "Synthesizer; Contrarian; FactChecker"
    And the agents executed should be "Synthesizer, Synthesizer"
    And the reasoning steps should be "Synthesizer-1; Synthesizer-2"
    And the metrics should record 2 cycles
    And the metrics should list agents "Synthesizer"

  Scenario: Invalid reasoning mode via CLI
    Given loops is set to 2 in configuration
    When I run `autoresearch search "mode test" --mode invalid`
    Then the CLI should exit with an error
    And no agents should execute
    And the system state should be restored
    And the logs should include "unsupported reasoning mode"
