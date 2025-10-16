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
  Scenario: Modular UI Component Keyboard Navigation
    Given the modular UI components are running
    When I navigate the interface using only keyboard
    Then I should be able to access all functionality
    And focus indicators should be clearly visible
    And tab order should be logical and follow page structure

  @requires_ui
  Scenario: Modular UI Component Screen Reader Compatibility
    Given the modular UI components are running
    When I use the GUI with a screen reader
    Then all images should have alt text
    And all form controls should have proper labels
    And dynamic content updates should be announced to screen readers
    And ARIA landmarks should be properly structured

  @requires_ui
  Scenario: Enhanced Accessibility Features
    Given the modular UI components are running
    When I use the accessibility-enhanced interface
    Then color contrast validation should pass WCAG AA standards
    And semantic HTML structure should be valid
    And keyboard navigation should be comprehensive

  @requires_ui
  Scenario: High Contrast Mode
    Given the modular UI components are running
    When I enable high contrast mode
    Then text should have sufficient contrast against backgrounds
    And interactive elements should be clearly distinguishable
    And information should not be conveyed by color alone

  @requires_ui
  Scenario: Responsive Layout on Mobile
    Given the modular UI components are running on a small screen
    When I view the page
    Then columns should stack vertically
    And controls should remain usable without horizontal scrolling

  @requires_ui
  Scenario: Guided Tour Availability
    Given the modular UI components are running
    When I open the page for the first time
    Then a guided tour modal should describe the main features
    And I should be able to dismiss the tour

  @requires_ui
  Scenario: Skip to content link
    Given the modular UI components are running
    When I load the Streamlit page
    Then a skip to main content link should be present

  @requires_ui
  Scenario: Progressive Disclosure Controls
    Given the modular UI components are running
    When I use the results display with progressive disclosure
    Then I should see TL;DR summary first
    And I should be able to expand to see key findings
    And I should be able to further expand to see detailed reasoning
    And I should be able to access full trace information

  @requires_ui
  Scenario: Component-Based Configuration Editor
    Given the modular UI components are running
    When I use the configuration editor component
    Then I should be able to select from configuration presets
    And I should be able to edit core settings
    And I should be able to configure storage settings
    And I should be able to set user preferences
    And validation should prevent invalid configurations
