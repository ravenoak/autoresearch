Feature: Tracing
  Scenario: Tracing enabled emits spans
    Given tracing is enabled
    When I perform a traced operation
    Then a span is recorded with name "test-span" and attribute "foo"="bar"

  Scenario: Tracing disabled emits no spans
    Given tracing is disabled
    When I perform a traced operation
    Then no spans are recorded
