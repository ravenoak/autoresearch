Feature: Tracing
  # Spec: docs/specs/tracing.md#key-behaviors - Emit spans when tracing is enabled
  Scenario: Tracing enabled emits spans
    Given tracing is enabled
    When I perform a traced operation
    Then a span is recorded with name "test-span" and attribute "foo"="bar"

  # Spec: docs/specs/tracing.md#key-behaviors - Ignore spans when tracing is disabled
  Scenario: Tracing disabled emits no spans
    Given tracing is disabled
    When I perform a traced operation
    Then no spans are recorded
