@behavior @requires_distributed
Feature: Distributed Execution
  As a developer
  I want to run queries across multiple processes
  So that agents can persist claims in parallel

  Background:
    Given mock agents that persist claims

  # Spec: docs/algorithms/distributed_workflows.md - distributed coordination

  Scenario: Run distributed query with Ray executor
    Given a distributed configuration using Ray
    When I run a distributed query
    Then the claims should be persisted for each agent
    And more than one process should execute

  Scenario: Run distributed query with multiprocessing
    Given a distributed configuration using multiprocessing
    When I run a distributed query
    Then the claims should be persisted for each agent
    And more than one process should execute
