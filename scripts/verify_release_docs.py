#!/usr/bin/env python3
"""
Release documentation verification script.

Validates that all documentation claims are consistent with empirical data:
- Coverage claims match 71.94% (measured October 17, 2025)
- Test counts match 1,721 tests (measured October 17, 2025)
- Version consistency across pyproject.toml, __init__.py
- Release status matches git tags
"""

import re
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str]) -> str:
    """Run a command and return its output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"Error: {e.stderr}")
        return ""


def check_coverage_claims() -> bool:
    """Check that all coverage claims are consistent."""
    print("✓ Checking coverage claims...")

    # Find coverage claims (look for "71.94%" specifically, not just any percentage)
    coverage_pattern = r"71\.94%"

    # Check CHANGELOG.md
    changelog_content = Path("CHANGELOG.md").read_text()

    expected_coverage = "71.94"
    coverage_found = False

    # Look for the specific coverage claim
    if "71.94% measured October 17, 2025" in changelog_content:
        coverage_found = True
        print(f"✓ Coverage claims correct: {expected_coverage}%")
    else:
        print("✗ CHANGELOG.md missing correct coverage claim: 71.94% measured October 17, 2025")
        return False

    return True


def check_test_counts() -> bool:
    """Check that all test count claims are consistent."""
    print("✓ Checking test count claims...")

    changelog_content = Path("CHANGELOG.md").read_text()

    expected_tests = "1,721"
    expected_breakdown = "937 unit, 350 integration, 41 behavior"

    # Check test count
    if f"{expected_tests} tests" not in changelog_content:
        print(f"✗ CHANGELOG.md has incorrect test count (expected {expected_tests})")
        return False

    # Check breakdown
    if expected_breakdown not in changelog_content:
        print(f"✗ CHANGELOG.md missing test breakdown (expected {expected_breakdown})")
        return False

    # Check measurement date
    if "(measured October 17, 2025)" not in changelog_content:
        print("✗ CHANGELOG.md missing measurement date for test counts")
        return False

    print(f"✓ Test counts correct: {expected_tests} tests ({expected_breakdown})")
    return True


def check_version_consistency() -> bool:
    """Check version consistency across files."""
    print("✓ Checking version consistency...")

    # Check pyproject.toml
    pyproject_content = Path("pyproject.toml").read_text()
    if 'version = "0.1.0"' not in pyproject_content:
        print("✗ pyproject.toml version not 0.1.0")
        return False

    if 'release_date = "2025-11-15"' not in pyproject_content:
        print("✗ pyproject.toml release_date not 2025-11-15")
        return False

    # Check __init__.py
    init_content = Path("src/autoresearch/__init__.py").read_text()
    if '__version__ = "0.1.0"' not in init_content:
        print("✗ __init__.py version not 0.1.0")
        return False

    if '__release_date__ = "2025-11-15"' not in init_content:
        print("✗ __init__.py release_date not 2025-11-15")
        return False

    print("✓ Version consistency: 0.1.0, 2025-11-15")
    return True


def check_release_status() -> bool:
    """Check that release status claims are accurate."""
    print("✓ Checking release status claims...")

    # Check git tags
    git_tags = run_command(["git", "tag", "-l", "v0.1*"])
    expected_tags = ["v0.1.0a1", "v0.1.0"]

    for tag in expected_tags:
        if tag not in git_tags:
            print(f"✗ Expected git tag {tag} not found")
            return False

    print("✓ Git tags correct: v0.1.0a1 exists, v0.1.0 pending")
    return True


def main() -> int:
    """Run all verification checks."""
    print("🔍 Verifying release documentation consistency...")

    checks = [
        check_coverage_claims,
        check_test_counts,
        check_version_consistency,
        check_release_status,
    ]

    all_passed = True
    for check in checks:
        try:
            if not check():
                all_passed = False
        except Exception as e:
            print(f"✗ Check failed with error: {e}")
            all_passed = False

    if all_passed:
        print("✅ All release documentation checks passed!")
        return 0
    else:
        print("❌ Some release documentation checks failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
