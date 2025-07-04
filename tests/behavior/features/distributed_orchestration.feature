Feature: Distributed Agent Orchestration
  As a developer
  I want agents to run across multiple processes
  So that heavy tasks can be parallelised

  Scenario: Running agents across processes
    Given a distributed configuration with 2 workers
    When I execute a distributed query with two agents
    Then multiple worker processes should be used
