Feature: GUI Query History
  As a user of the Streamlit GUI
  I want to review and rerun previous queries
  So that I can compare results and revisit past work

  Background:
    Given the Streamlit application has a stored query history

  @requires_ui
  Scenario: View and rerun a previous query
    When I view the query history
    Then the previous query should be visible
    When I rerun the query from history
    Then the rerun results should match the stored results
