@legacy_streamlit
Feature: Streamlit GUI Features
  As a user
  I want a web-based GUI for Autoresearch
  So that I can interact with the system in a more visual way

  Background:
    Given the Streamlit application is running

  @requires_ui
  Scenario: Formatted Answer Display with Markdown Rendering
    When I enter a query that returns Markdown-formatted content
    Then the answer should be displayed with proper Markdown rendering
    And formatting elements like headers, lists, and code blocks should be properly styled
    And math expressions in LaTeX format should be properly rendered

  @requires_ui
  Scenario: Tabbed Interface for Results
    When I run a query in the Streamlit interface
    Then the results should be displayed in a tabbed interface
    And there should be tabs for "Citations", "Reasoning", "Metrics", and "Knowledge Graph"
    And I should be able to switch between tabs without losing information

  @requires_ui
  Scenario: Knowledge Graph Visualization
    When I run a query that generates a knowledge graph
    Then the knowledge graph should be visualized in the "Knowledge Graph" tab
    And the visualization should show relationships between concepts
    And the nodes should be color-coded by type

  @requires_ui
  Scenario: Knowledge graph exports toggle prepares downloads
    When I run a query that generates a knowledge graph with exports enabled
    Then graph export downloads should be prepared

  @requires_ui
  Scenario: Configuration Editor Interface
    When I navigate to the configuration section
    Then I should see a form with configuration options
    And the form should have validation for input fields
    And I should be able to save changes to the configuration
    And I should see feedback when the configuration is saved

  @requires_ui
  Scenario: Configuration Updates Persist
    When I update a configuration value in the GUI
    Then the configuration should be saved with the new value
    And the updated configuration should be used for the next query

  @requires_ui
  Scenario: Agent Interaction Trace Visualization
    When I run a query in the Streamlit interface
    Then an interaction trace should be displayed
    And progress metrics should be visualized

  @requires_ui
  Scenario: User Preferences Configuration
    When I open the configuration editor
    And I change a user preference value
    Then the preference should be saved
    And the sidebar should reflect the updated preference

  @requires_ui
  Scenario: Theme Toggle Switch
    When I toggle dark mode
    Then the page background should change according to the selected mode
    And text color should adjust for readability
