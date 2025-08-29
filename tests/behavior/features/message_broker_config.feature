# Documentation: docs/message_brokers.md
# Documentation: docs/configuration.md
Feature: Message broker selection
  As a developer
  I want to configure message broker backends
  So that distributed workers coordinate correctly

  Scenario: Use default in-memory message broker
    Given the message broker name "memory"
    When I obtain a message broker instance
    Then an in-memory broker should be returned

  Scenario: Unsupported message broker raises error
    Given the message broker name "unknown"
    When I obtain a message broker instance
    Then a message broker error should be raised

  # Spec: docs/algorithms/distributed_workflows.md - Redis broker detection
  @requires_distributed @redis
  Scenario: Redis broker detection
    Given the message broker name "redis"
    When I obtain a message broker instance
    Then a redis broker should be returned
