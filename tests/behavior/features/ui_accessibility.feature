Feature: UI Accessibility
  As a user with accessibility needs
  I want the Autoresearch interfaces to be accessible
  So that I can use the system regardless of my abilities

  Background:
    Given the Autoresearch system is running

  Scenario: CLI Color Alternatives
    When I use the CLI with color output disabled
    Then all information should be conveyed through text and symbols
    And error messages should use symbolic indicators like "✗"
    And success messages should use symbolic indicators like "✓"
    And informational messages should use symbolic indicators like "ℹ"

  Scenario: CLI Screen Reader Compatibility
    When I use the CLI with a screen reader
    Then all progress indicators should have text alternatives
    And all visual elements should have text descriptions
    And command help text should be properly structured for screen readers

  @requires_ui
  Scenario: Streamlit GUI Keyboard Navigation
    Given the Streamlit application is running
    When I navigate the interface using only keyboard
    Then I should be able to access all functionality
    And focus indicators should be clearly visible
    And tab order should be logical and follow page structure

  @requires_ui
  Scenario: Streamlit GUI Screen Reader Compatibility
    Given the Streamlit application is running
    When I use the GUI with a screen reader
    Then all images should have alt text
    And all form controls should have proper labels
    And dynamic content updates should be announced to screen readers

  @requires_ui
  Scenario: High Contrast Mode
    Given the Streamlit application is running
    When I enable high contrast mode
    Then text should have sufficient contrast against backgrounds
    And interactive elements should be clearly distinguishable
    And information should not be conveyed by color alone

  @requires_ui
  Scenario: Responsive Layout on Mobile
    Given the Streamlit application is running on a small screen
    When I view the page
    Then columns should stack vertically
    And controls should remain usable without horizontal scrolling

  @requires_ui
  Scenario: Guided Tour Availability
    Given the Streamlit application is running
    When I open the page for the first time
    Then a guided tour modal should describe the main features
    And I should be able to dismiss the tour
