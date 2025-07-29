Feature: CLI search options
  Scenarios covering new search flags

  Scenario: Set loops and token budget via CLI
    When I run `autoresearch search "Budget" --loops 3 --token-budget 100 --no-ontology-reasoning`
    Then the search config should have loops 3 and token budget 100

  Scenario: Choose specific agents via CLI
    When I run `autoresearch search "Agents" --agents Synthesizer,Contrarian`
    Then the search config should list agents "Synthesizer,Contrarian"

  Scenario: Run agent groups in parallel via CLI
    When I run `autoresearch search --parallel --agent-groups "Synthesizer,Contrarian" "FactChecker" "Parallel"`
    Then the parallel query should use groups "Synthesizer,Contrarian" and "FactChecker"

  Scenario: Override reasoning mode via CLI
    When I run `autoresearch search "ModeCLI" --reasoning-mode chain-of-thought`
    Then the search config should use reasoning mode "chain-of-thought"

  Scenario: Override primus start via CLI
    When I run `autoresearch search "PrimusCLI" --primus-start 2`
    Then the search config should have primus start 2
