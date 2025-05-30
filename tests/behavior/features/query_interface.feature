Feature: Query Interface
  As a user of Autoresearch,
  I want to submit natural-language queries via different interfaces,
  so that I can receive evidence-driven answers.

  Background:
    Given the Autoresearch application is running

  Scenario: Submit query via CLI
    When I run `autoresearch search "What is Promise Theory?"` in a terminal
    Then I should receive a readable Markdown answer with `answer`, `citations`, `reasoning`, and `metrics` sections

  Scenario: Submit query via HTTP API
    When I send a POST request to `/query` with JSON `{ "query": "What is Promise Theory?" }`
    Then the response should be a valid JSON document with keys `answer`, `citations`, `reasoning`, and `metrics`

  Scenario: Submit query via MCP tool
    When I run `autoresearch.search("What is Promise Theory?")` via the MCP CLI
    Then I should receive a JSON output matching the defined schema for `answer`, `citations`, `reasoning`, and `metrics`
