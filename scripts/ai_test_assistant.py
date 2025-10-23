#!/usr/bin/env python3
"""
AI-assisted testing framework for autoresearch project.

This script provides AI-powered assistance for testing, including test generation,
test analysis, and testing best practices guidance.
"""

import argparse
import ast
import os
import re
import sys
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@dataclass
class TestAnalysis:
    """Analysis results for test files."""
    file_path: str
    test_count: int
    coverage_percentage: float
    test_quality_score: float
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class TestGenerationRequest:
    """Request for AI-generated tests."""
    function_name: str
    file_path: str
    test_type: str  # unit, integration, performance, security
    existing_tests: List[str] = field(default_factory=list)
    requirements: Dict[str, str] = field(default_factory=dict)


class AITestAssistant:
    """AI-powered testing assistant for autoresearch project."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.test_dirs = [
            self.project_root / "tests",
            self.project_root / "src"  # For inline tests
        ]

    def analyze_test_file(self, file_path: Path) -> TestAnalysis:
        """Analyze a test file for quality and coverage."""
        analysis = TestAnalysis(
            file_path=str(file_path),
            test_count=0,
            coverage_percentage=0.0,
            test_quality_score=0.0
        )

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except (IOError, UnicodeDecodeError):
            analysis.issues.append(f"Cannot read test file: {file_path}")
            return analysis

        # Count test functions
        test_functions = re.findall(r'def (test_\w+)', content)
        analysis.test_count = len(test_functions)

        # Analyze test quality indicators
        quality_score = self._analyze_test_quality(content, lines)
        analysis.test_quality_score = quality_score

        # Check for common test issues
        analysis.issues.extend(self._identify_test_issues(content, file_path))
        analysis.recommendations.extend(self._generate_test_recommendations(content, file_path))

        return analysis

    def _analyze_test_quality(self, content: str, lines: List[str]) -> float:
        """Analyze overall test quality on a scale of 0-100."""
        score = 100.0

        # Check for test structure patterns
        if not re.search(r'def test_\w+', content):
            score -= 20  # No tests found

        # Check for proper imports
        if not re.search(r'import pytest', content) and not re.search(r'from pytest', content):
            score -= 10  # Missing pytest

        # Check for fixtures and setup
        if not re.search(r'@pytest\.fixture', content) and not re.search(r'def setup_', content):
            score -= 5  # Missing test setup

        # Check for assertions
        assertion_count = len(re.findall(r'assert ', content))
        if assertion_count == 0:
            score -= 15  # No assertions
        elif assertion_count < analysis.test_count:
            score -= 5  # Insufficient assertions

        # Check for mocking
        if re.search(r'from unittest.mock import', content) or re.search(r'import mock', content):
            score += 5  # Good mocking practices

        # Check for parametrized tests
        if re.search(r'@pytest\.mark\.parametrize', content):
            score += 10  # Good test parametrization

        # Check for proper test organization
        if re.search(r'class Test\w+', content):
            score += 5  # Good test organization

        return max(0, min(100, score))

    def _identify_test_issues(self, content: str, file_path: Path) -> List[str]:
        """Identify common test issues."""
        issues = []

        # Check for hardcoded values
        if re.search(r'assert.*==\s*[\'"]\d+[\'"]', content):
            issues.append("Hardcoded numeric values in assertions")

        # Check for missing edge case tests
        if not re.search(r'test.*edge|test.*boundary|test.*corner', content, re.IGNORECASE):
            issues.append("Missing edge case or boundary condition tests")

        # Check for long test functions
        long_tests = re.findall(r'def (test_\w+)\([^)]*\):\s*\n\s*(.|\n){50,}', content)
        if long_tests:
            issues.append(f"Long test functions found: {[name for name, _ in long_tests]}")

        # Check for missing docstrings on test functions
        test_functions = re.findall(r'def (test_\w+)\([^)]*\):', content)
        for test_func in test_functions:
            # Look for docstring in next few lines
            func_match = re.search(rf'def {re.escape(test_func)}\([^)]*\):(.*?)(?=\n\s*def|\n\s*@|\nclass|\Z)', content, re.DOTALL)
            if func_match:
                func_body = func_match.group(1)
                if not re.search(r'""".*"""', func_body[:200]):  # Check first 200 chars
                    issues.append(f"Test function '{test_func}' missing docstring")

        return issues

    def _generate_test_recommendations(self, content: str, file_path: Path) -> List[str]:
        """Generate recommendations for improving tests."""
        recommendations = []

        # Recommend BDD-style tests for complex workflows
        if 'integration' in str(file_path).lower() or 'behavior' in str(file_path).lower():
            recommendations.append("Consider adding BDD-style feature tests for user workflows")

        # Recommend performance tests for critical functions
        if 'search' in str(file_path).lower() or 'orchestration' in str(file_path).lower():
            recommendations.append("Add performance benchmarks for critical operations")

        # Recommend security tests for API endpoints
        if 'api' in str(file_path).lower() or 'auth' in str(file_path).lower():
            recommendations.append("Add security-focused tests for authentication and authorization")

        # Recommend error handling tests
        if not re.search(r'pytest\.raises|with pytest\.raises', content):
            recommendations.append("Add tests for error conditions and exception handling")

        return recommendations

    def generate_test_suggestions(self, source_file: Path) -> List[str]:
        """Generate test suggestions for a source file."""
        suggestions = []

        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except (IOError, UnicodeDecodeError):
            return ["Cannot analyze source file for test suggestions"]

        # Parse AST to find functions and classes
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return ["Cannot parse source file - syntax errors present"]

        # Find public functions and classes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                suggestions.append(f"Add unit tests for function: {node.name}")
                if not node.name.startswith('test'):
                    # Suggest specific test scenarios
                    suggestions.extend([
                        f"  - Test normal operation with valid inputs",
                        f"  - Test error handling with invalid inputs",
                        f"  - Test edge cases and boundary conditions",
                        f"  - Test integration with other components"
                    ])

            elif isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
                suggestions.append(f"Add tests for class: {node.name}")
                suggestions.extend([
                    f"  - Test class initialization and setup",
                    f"  - Test all public methods",
                    f"  - Test error conditions and edge cases",
                    f"  - Test interaction between methods"
                ])

        return suggestions

    def run_test_analysis(self) -> Dict[str, TestAnalysis]:
        """Run comprehensive test analysis across the project."""
        print("🔍 Analyzing test suite quality...")

        analyses = {}

        # Find all test files
        test_files = []
        for test_dir in self.test_dirs:
            if test_dir.exists():
                for pattern in ["**/test_*.py", "**/*_test.py"]:
                    test_files.extend(test_dir.glob(pattern))

        print(f"📁 Found {len(test_files)} test files")

        for test_file in test_files:
            analysis = self.analyze_test_file(test_file)
            analyses[str(test_file)] = analysis

        # Generate summary
        total_tests = sum(analysis.test_count for analysis in analyses.values())
        avg_quality = sum(analysis.test_quality_score for analysis in analyses.values()) / len(analyses) if analyses else 0

        print("✅ Test analysis complete!"        print(f"📊 Total Tests: {total_tests}")
        print(f"📈 Average Quality Score: {avg_quality".1f"}/100")

        # Show files needing attention
        low_quality_files = [
            (file_path, analysis.test_quality_score)
            for file_path, analysis in analyses.items()
            if analysis.test_quality_score < 70
        ]

        if low_quality_files:
            print("
⚠️ Files needing improvement:"            for file_path, score in low_quality_files:
                print(f"  {file_path}: {score".1f"}/100")

        return analyses

    def generate_test_report(self, analyses: Dict[str, TestAnalysis]) -> str:
        """Generate a comprehensive test report."""
        report_lines = []

        # Header
        report_lines.append("# AI Test Analysis Report")
        report_lines.append(f"Generated: {__import__('datetime').datetime.now().isoformat()}")
        report_lines.append("")

        # Summary
        total_tests = sum(analysis.test_count for analysis in analyses.values())
        avg_quality = sum(analysis.test_quality_score for analysis in analyses.values()) / len(analyses) if analyses else 0

        report_lines.append("## Summary")
        report_lines.append(f"- **Total Test Files**: {len(analyses)}")
        report_lines.append(f"- **Total Tests**: {total_tests}")
        report_lines.append(f"- **Average Quality Score**: {avg_quality".1f"}/100")
        report_lines.append("")

        # Quality breakdown
        quality_ranges = {
            "Excellent (90-100)": 0,
            "Good (80-89)": 0,
            "Fair (70-79)": 0,
            "Poor (60-69)": 0,
            "Critical (<60)": 0
        }

        for analysis in analyses.values():
            if analysis.test_quality_score >= 90:
                quality_ranges["Excellent (90-100)"] += 1
            elif analysis.test_quality_score >= 80:
                quality_ranges["Good (80-89)"] += 1
            elif analysis.test_quality_score >= 70:
                quality_ranges["Fair (70-79)"] += 1
            elif analysis.test_quality_score >= 60:
                quality_ranges["Poor (60-69)"] += 1
            else:
                quality_ranges["Critical (<60)"] += 1

        report_lines.append("## Quality Distribution")
        for range_name, count in quality_ranges.items():
            percentage = (count / len(analyses) * 100) if analyses else 0
            report_lines.append(f"- **{range_name}**: {count} files ({percentage".1f"}%)")
        report_lines.append("")

        # Detailed findings
        report_lines.append("## Detailed Analysis")
        for file_path, analysis in analyses.items():
            if analysis.issues or analysis.recommendations:
                report_lines.append(f"### {file_path}")
                report_lines.append(f"- **Tests**: {analysis.test_count}")
                report_lines.append(f"- **Quality Score**: {analysis.test_quality_score".1f"}/100")

                if analysis.issues:
                    report_lines.append("  **Issues**:")
                    for issue in analysis.issues:
                        report_lines.append(f"  - {issue}")

                if analysis.recommendations:
                    report_lines.append("  **Recommendations**:")
                    for rec in analysis.recommendations:
                        report_lines.append(f"  - {rec}")

                report_lines.append("")

        return "\n".join(report_lines)


def main():
    """Main entry point for AI test assistant."""
    parser = argparse.ArgumentParser(description="AI-powered testing assistance for autoresearch project")
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze existing test files for quality and coverage"
    )
    parser.add_argument(
        "--suggest",
        metavar="SOURCE_FILE",
        help="Generate test suggestions for a source file"
    )
    parser.add_argument(
        "--report",
        metavar="OUTPUT_FILE",
        help="Generate comprehensive test analysis report"
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root directory (default: current directory)"
    )

    args = parser.parse_args()

    assistant = AITestAssistant(Path(args.project_root))

    if args.analyze:
        # Run comprehensive test analysis
        analyses = assistant.run_test_analysis()

        if args.report:
            # Save report to file
            report_content = assistant.generate_test_report(analyses)
            with open(args.report, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"✅ Test analysis report saved to: {args.report}")
        else:
            # Print summary to console
            print("\n📋 Test Analysis Summary:")
            print("=" * 50)
            for file_path, analysis in analyses.items():
                print(f"\n📄 {file_path}")
                print(f"   Tests: {analysis.test_count}")
                print(f"   Quality: {analysis.test_quality_score".1f"}/100")
                if analysis.issues:
                    print(f"   Issues: {len(analysis.issues)}")
                if analysis.recommendations:
                    print(f"   Recommendations: {len(analysis.recommendations)}")

    elif args.suggest:
        # Generate test suggestions for a source file
        source_file = Path(args.suggest)
        if not source_file.exists():
            print(f"❌ Source file not found: {source_file}")
            sys.exit(1)

        print(f"🔧 Generating test suggestions for: {source_file}")
        suggestions = assistant.generate_test_suggestions(source_file)

        if suggestions:
            print("\n📋 Test Suggestions:")
            print("=" * 50)
            for suggestion in suggestions:
                print(f"• {suggestion}")
        else:
            print("No test suggestions generated")

    else:
        parser.print_help()
        print("\n❌ No action specified. Use --analyze or --suggest.")
        sys.exit(1)


if __name__ == "__main__":
    main()
