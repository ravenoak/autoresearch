Feature: Installer optional dependencies
  The installer script should handle extras groups correctly

  Scenario: Minimal installation
    When I run the installer with "--minimal"
    Then only the minimal extra should be installed

  Scenario: Automatic dependency resolution
    When I run the installer without arguments
    Then all extras except minimal should be installed

  Scenario: Upgrade from minimal to full installation
    Given the installer was run with "--minimal" previously
    When I run the installer without arguments
    Then all extras except minimal should be installed
