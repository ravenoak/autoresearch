Feature: Reasoning parameter overrides
  Scenarios demonstrating CLI flags for circuit breaker and adaptive budgeting

  Scenario: Override circuit breaker settings via CLI
    When I run `autoresearch search "breaker" --circuit-breaker-threshold 5 --circuit-breaker-cooldown 60 --no-ontology-reasoning`
    Then the search config should set circuit breaker threshold 5 and cooldown 60

  Scenario: Tune adaptive token budgeting via CLI
    When I run `autoresearch search "adapt" --adaptive-max-factor 25 --adaptive-min-buffer 20 --no-ontology-reasoning`
    Then the search config should have adaptive factor 25 and buffer 20
