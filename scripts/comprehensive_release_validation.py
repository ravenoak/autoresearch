#!/usr/bin/env python3
"""
Comprehensive Release Validation Script

This script executes the full validation pipeline to close gaps and achieve
v0.1.0 stable release readiness. It includes systematic testing, quality
validation, and release engineering steps.

Usage:
    uv run python scripts/comprehensive_release_validation.py
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class ReleaseValidator:
    """Comprehensive release validation pipeline."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.log_file = self.project_root / "release_validation.log"

    def run_command(self, command: str, description: str) -> Tuple[bool, str]:
        """Run a command and return success status and output."""
        print(f"\n{'='*60}")
        print(f"EXECUTING: {description}")
        print(f"COMMAND: {command}")
        print(f"{'='*60}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            success = result.returncode == 0
            output = result.stdout + result.stderr

            # Log the result
            with open(self.log_file, 'a') as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"COMMAND: {command}\n")
                f.write(f"DESCRIPTION: {description}\n")
                f.write(f"SUCCESS: {success}\n")
                f.write(f"OUTPUT:\n{output}\n")
                f.write(f"{'='*60}\n")

            if success:
                print(f"✅ SUCCESS: {description}")
            else:
                print(f"❌ FAILED: {description}")
                print(f"Exit code: {result.returncode}")
                if result.stdout:
                    print(f"STDOUT: {result.stdout}")
                if result.stderr:
                    print(f"STDERR: {result.stderr}")

            return success, output

        except subprocess.TimeoutExpired:
            print(f"⏰ TIMEOUT: {description} (5 minutes)")
            return False, "Command timed out"
        except Exception as e:
            print(f"💥 ERROR: {description} - {e}")
            return False, str(e)

    def validate_environment(self) -> bool:
        """Phase 1: Environment Setup & Dependencies."""
        print(f"\n{'🔧'*20} PHASE 1: ENVIRONMENT SETUP {'🔧'*20}")

        commands = [
            ("uv sync --extra dev-minimal --extra test --extra ui --extra analysis --extra distributed --extra llm --extra parsers",
             "Sync all development dependencies"),
            ("uv add PySide6 pytest-bdd hypothesis freezegun responses pytest-httpx pytest-timeout pytest-benchmark pytest-cov",
             "Install missing testing dependencies"),
            ("uv run python -c 'import PySide6, pytest_bdd, hypothesis; print(\"Dependencies OK\")'",
             "Verify critical dependencies are available"),
        ]

        all_success = True
        for command, description in commands:
            success, _ = self.run_command(command, description)
            all_success = all_success and success

        return all_success

    def run_comprehensive_tests(self) -> bool:
        """Phase 2: Comprehensive Test Execution."""
        print(f"\n{'🧪'*20} PHASE 2: COMPREHENSIVE TESTING {'🧪'*20}")

        test_commands = [
            ("uv run pytest tests/unit/ -p no:pytest-qt --tb=short -q",
             "Run complete unit test suite"),
            ("uv run pytest tests/integration/ -p no:pytest-qt --tb=short -q",
             "Run complete integration test suite"),
            ("uv run pytest tests/behavior/ -p no:pytest-qt --tb=short -q",
             "Run complete behavior test suite"),
        ]

        all_success = True
        for command, description in test_commands:
            success, output = self.run_command(command, description)
            all_success = all_success and success

            # Check test results in output
            if success:
                lines = output.split('\n')
                for line in lines:
                    if 'failed' in line.lower() and '0 failed' not in line:
                        print(f"⚠️  WARNING: Tests show failures in: {line.strip()}")
                    elif 'passed' in line.lower():
                        print(f"✅ Test results summary: {line.strip()}")

        return all_success

    def validate_quality(self) -> bool:
        """Phase 3: Quality Validation."""
        print(f"\n{'🔍'*20} PHASE 3: QUALITY VALIDATION {'🔍'*20}")

        quality_commands = [
            ("uv run flake8 src tests", "Code style validation"),
            ("uv run mypy --strict src", "Type safety validation"),
            ("uv run python scripts/lint_specs.py", "Specification compliance"),
            ("uv run python scripts/check_release_metadata.py", "Release metadata validation"),
            ("task code-review", "AI-powered code review"),
        ]

        all_success = True
        for command, description in quality_commands:
            success, _ = self.run_command(command, description)
            all_success = all_success and success

        return all_success

    def analyze_coverage(self) -> bool:
        """Phase 4: Coverage Analysis."""
        print(f"\n{'📊'*20} PHASE 4: COVERAGE ANALYSIS {'📊'*20}")

        coverage_commands = [
            ("task coverage", "Generate comprehensive coverage report"),
            ("task verify", "Run full verification suite"),
            ("uv run coverage report --fail-under=50", "Validate minimum coverage threshold"),
        ]

        all_success = True
        for command, description in coverage_commands:
            success, output = self.run_command(command, description)
            all_success = all_success and success

            # Extract coverage percentage
            if success and "TOTAL" in output:
                for line in output.split('\n'):
                    if "TOTAL" in line and "%" in line:
                        print(f"📈 Coverage result: {line.strip()}")

        return all_success

    def build_and_validate(self) -> bool:
        """Phase 5: Release Engineering."""
        print(f"\n{'🏗️ '*20} PHASE 5: RELEASE ENGINEERING {'🏗️ '*20}")

        build_commands = [
            ("uv run python -m build", "Build distribution packages"),
            ("uv run twine check dist/*", "Validate package metadata"),
            ("uv run python scripts/publish_dev.py --dry-run", "Test publish process"),
        ]

        all_success = True
        for command, description in build_commands:
            success, _ = self.run_command(command, description)
            all_success = all_success and success

        return all_success

    def final_validation(self) -> bool:
        """Phase 6: Final Release Validation."""
        print(f"\n{'🎯'*20} PHASE 6: FINAL VALIDATION {'🎯'*20}")

        final_commands = [
            ("task release:alpha EXTRAS=\"baseline\"", "Complete alpha release validation"),
            ("git status --porcelain", "Check for any uncommitted changes"),
            ("uv run python -c 'import autoresearch; print(f\"Version: {autoresearch.__version__}\")'",
             "Verify package version"),
        ]

        all_success = True
        for command, description in final_commands:
            success, output = self.run_command(command, description)
            all_success = all_success and success

        return all_success

    def run_complete_validation(self) -> bool:
        """Run the complete validation pipeline."""
        print(f"\n{'🚀'*20} COMPREHENSIVE RELEASE VALIDATION {'🚀'*20}")
        print("Starting systematic validation to achieve v0.1.0 stable release readiness")
        print(f"Log file: {self.log_file}")

        # Clear previous log
        with open(self.log_file, 'w') as f:
            f.write("Release Validation Log - " + str(self.project_root) + "\n")
            f.write("="*60 + "\n")

        phases = [
            ("Environment Setup", self.validate_environment),
            ("Comprehensive Testing", self.run_comprehensive_tests),
            ("Quality Validation", self.validate_quality),
            ("Coverage Analysis", self.analyze_coverage),
            ("Release Engineering", self.build_and_validate),
            ("Final Validation", self.final_validation),
        ]

        all_success = True
        for phase_name, phase_func in phases:
            print(f"\n{'🔄'*10} Starting {phase_name} {'🔄'*10}")
            success = phase_func()
            all_success = all_success and success

            if not success:
                print(f"⚠️  Phase '{phase_name}' had issues - continuing for completeness")

        # Final summary
        print(f"\n{'🏁'*20} VALIDATION COMPLETE {'🏁'*20}")
        if all_success:
            print("✅ ALL PHASES PASSED - Release ready!")
            print("🎉 Ready to tag v0.1.0 stable release")
        else:
            print("⚠️  Some phases had issues - review log for details")
            print(f"📋 Check log file: {self.log_file}")

        return all_success


def main():
    """Main entry point."""
    project_root = Path.cwd()
    validator = ReleaseValidator(project_root)

    success = validator.run_complete_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
