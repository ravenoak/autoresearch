# Documentation: docs/installation.md
Feature: Data analysis utilities
  As a user
  I want to summarize metrics with Polars
  So that I can analyze agent performance

  Scenario: Generate metrics dataframe when Polars enabled
    Given sample metrics
    When I generate metrics dataframe with Polars enabled
    Then a Polars dataframe should be returned

  Scenario: Fail to generate metrics dataframe when Polars disabled
    Given sample metrics
    When I generate metrics dataframe with Polars disabled
    Then the operation should fail with polars disabled error
