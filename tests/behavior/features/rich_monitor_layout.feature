@requires_ui @user_workflows
Feature: Rich layout coherence with bare-mode fallbacks
  Monitor and metrics commands share Rich renderables yet preserve deterministic
  plain-text output when accessibility constraints apply.

  Background:
    Given the CLI accessibility mode is disabled
    And telemetry capture is enabled

  Scenario: Render Rich panels during monitor sessions
    When I run "autoresearch monitor run" inside a TTY session
    Then the CLI displays Rich panels for CPU, memory, and token metrics
    And telemetry records a "cli.render.rich" event for "monitor.run"

  Scenario: Emit plain-text output when bare mode is active
    Given bare mode is enabled
    When I run "autoresearch monitor run" without a TTY
    Then the CLI prints ASCII metrics identical to the baseline snapshot
    And telemetry records a "cli.render.plain" event for "monitor.run"
