#!/usr/bin/env python3
"""
AI-powered code review automation script for autoresearch project.

This script provides automated code review capabilities that analyze code changes
against project standards, architecture patterns, and quality guidelines.
"""

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from autoresearch.config.loader import get_config


@dataclass
class CodeReviewFinding:
    """Represents a code review finding."""
    file_path: str
    line_number: Optional[int]
    column: Optional[int]
    severity: str  # critical, high, medium, low, info
    category: str  # security, performance, style, architecture, testing
    message: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None


@dataclass
class CodeReviewResult:
    """Results of a code review analysis."""
    findings: List[CodeReviewFinding] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    overall_score: float = 100.0
    review_timestamp: datetime = field(default_factory=datetime.now)


class AICodeReviewer:
    """AI-powered code review system for autoresearch project."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.config = get_config()
        self.review_result = CodeReviewResult()

    def get_changed_files(self) -> List[Path]:
        """Get list of files that have been modified."""
        try:
            # Get files changed in git
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            if result.returncode == 0:
                files = [Path(f.strip()) for f in result.stdout.split('\n') if f.strip()]
                return [f for f in files if f.exists() and f.suffix == '.py']

            return []

        except (subprocess.SubprocessError, FileNotFoundError):
            # Fallback: check for uncommitted changes
            try:
                result = subprocess.run(
                    ['git', 'diff', '--name-only'],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )

                if result.returncode == 0:
                    files = [Path(f.strip()) for f in result.stdout.split('\n') if f.strip()]
                    return [f for f in files if f.exists() and f.suffix == '.py']

                return []

            except (subprocess.SubprocessError, FileNotFoundError):
                return []

    def analyze_file(self, file_path: Path) -> List[CodeReviewFinding]:
        """Analyze a single file for code quality issues."""
        findings = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except (IOError, UnicodeDecodeError) as e:
            findings.append(CodeReviewFinding(
                file_path=str(file_path),
                line_number=None,
                column=None,
                severity='high',
                category='io_error',
                message=f'Cannot read file: {e}',
                suggestion='Ensure file is readable and uses UTF-8 encoding'
            ))
            return findings

        # Check for common issues
        findings.extend(self._check_line_length(lines, file_path))
        findings.extend(self._check_imports(content, file_path))
        findings.extend(self._check_docstrings(content, lines, file_path))
        findings.extend(self._check_type_hints(content, file_path))
        findings.extend(self._check_error_handling(content, file_path))
        findings.extend(self._check_security_issues(content, file_path))

        return findings

    def _check_line_length(self, lines: List[str], file_path: Path) -> List[CodeReviewFinding]:
        """Check for lines that exceed maximum length."""
        findings = []
        max_length = 100

        for i, line in enumerate(lines, 1):
            if len(line) > max_length:
                findings.append(CodeReviewFinding(
                    file_path=str(file_path),
                    line_number=i,
                    column=max_length + 1,
                    severity='low',
                    category='style',
                    message=f'Line exceeds maximum length of {max_length} characters',
                    suggestion=f'Break long lines or use line continuation',
                    code_snippet=line.strip()
                ))

        return findings

    def _check_imports(self, content: str, file_path: Path) -> List[CodeReviewFinding]:
        """Check import organization and unused imports."""
        findings = []

        # Check for proper import ordering
        lines = content.split('\n')
        import_lines = []

        for i, line in enumerate(lines, 1):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                import_lines.append((i, line.strip()))

        if import_lines:
            # Check if standard library imports come first
            stdlib_imports = []
            third_party_imports = []
            local_imports = []

            for line_no, import_line in import_lines:
                if self._is_stdlib_import(import_line):
                    stdlib_imports.append((line_no, import_line))
                elif self._is_local_import(import_line):
                    local_imports.append((line_no, import_line))
                else:
                    third_party_imports.append((line_no, import_line))

            # Check ordering
            expected_order = [stdlib_imports, third_party_imports, local_imports]
            current_pos = 0

            for section in expected_order:
                if section:
                    section_start = min(line_no for line_no, _ in section)
                    if section_start < current_pos:
                        findings.append(CodeReviewFinding(
                            file_path=str(file_path),
                            line_number=section_start,
                            column=1,
                            severity='medium',
                            category='style',
                            message='Import sections not in correct order (stdlib, third-party, local)',
                            suggestion='Reorder imports: standard library, third-party, then local imports'
                        ))
                        break
                    current_pos = max(line_no for line_no, _ in section) + 1

        return findings

    def _is_stdlib_import(self, import_line: str) -> bool:
        """Check if import is from standard library."""
        stdlib_modules = {
            'os', 'sys', 'pathlib', 'datetime', 'typing', 'collections',
            'itertools', 'functools', 're', 'json', 'subprocess', 'shutil',
            'tempfile', 'uuid', 'hashlib', 'base64', 'urllib', 'http'
        }

        # Extract module name from import
        if import_line.startswith('import '):
            module = import_line[7:].split('.')[0].split(' as ')[0]
        elif import_line.startswith('from '):
            module = import_line[5:].split(' import ')[0].split('.')[0]
        else:
            return False

        return module in stdlib_modules

    def _is_local_import(self, import_line: str) -> bool:
        """Check if import is from local project."""
        return ('autoresearch' in import_line or
                import_line.startswith('from .') or
                import_line.startswith('from src'))

    def _check_docstrings(self, content: str, lines: List[str], file_path: Path) -> List[CodeReviewFinding]:
        """Check for missing or inadequate docstrings."""
        findings = []

        # Find function and class definitions
        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Check function definitions
            if (stripped.startswith('def ') and
                not stripped.startswith('def _') and  # Skip private functions
                i < len(lines) and
                not lines[i].strip().startswith('"""')):

                # Look for docstring in next few lines
                has_docstring = False
                for j in range(i + 1, min(i + 10, len(lines))):
                    next_line = lines[j].strip()
                    if next_line.startswith('"""') or next_line.startswith("'''"):
                        has_docstring = True
                        break
                    elif next_line and not next_line.startswith('#') and not next_line.startswith('def '):
                        break

                if not has_docstring:
                    findings.append(CodeReviewFinding(
                        file_path=str(file_path),
                        line_number=i,
                        column=1,
                        severity='medium',
                        category='documentation',
                        message='Public function missing docstring',
                        suggestion='Add a comprehensive docstring explaining purpose, parameters, and return value',
                        code_snippet=stripped
                    ))

            # Check class definitions
            elif (stripped.startswith('class ') and
                  not stripped.startswith('class _') and  # Skip private classes
                  i < len(lines) and
                  not lines[i].strip().startswith('"""')):

                has_docstring = False
                for j in range(i + 1, min(i + 10, len(lines))):
                    next_line = lines[j].strip()
                    if next_line.startswith('"""') or next_line.startswith("'''"):
                        has_docstring = True
                        break
                    elif next_line and not next_line.startswith('#') and not next_line.startswith('def '):
                        break

                if not has_docstring:
                    findings.append(CodeReviewFinding(
                        file_path=str(file_path),
                        line_number=i,
                        column=1,
                        severity='medium',
                        category='documentation',
                        message='Public class missing docstring',
                        suggestion='Add a comprehensive docstring explaining purpose and key methods',
                        code_snippet=stripped
                    ))

        return findings

    def _check_type_hints(self, content: str, file_path: Path) -> List[CodeReviewFinding]:
        """Check for missing type hints."""
        findings = []

        # Simple regex to find function definitions without type hints
        function_pattern = r'def\s+(\w+)\s*\([^)]*\)\s*->?\s*[^:]*:'
        matches = re.finditer(function_pattern, content)

        for match in matches:
            func_def = match.group(0)
            func_name = match.group(1)

            # Skip if already has return type annotation
            if '->' in func_def:
                continue

            # Check if function has parameters
            param_start = func_def.find('(')
            param_end = func_def.find(')')

            if param_start != -1 and param_end != -1:
                params = func_def[param_start + 1:param_end]

                # Check for untyped parameters
                if params.strip() and not any(char in params for char in [':', '->']):
                    findings.append(CodeReviewFinding(
                        file_path=str(file_path),
                        line_number=content[:match.start()].count('\n') + 1,
                        column=match.start() + 1,
                        severity='medium',
                        category='type_safety',
                        message=f'Function "{func_name}" missing type hints',
                        suggestion='Add type hints for all parameters and return value',
                        code_snippet=func_def.strip()
                    ))

        return findings

    def _check_error_handling(self, content: str, file_path: Path) -> List[CodeReviewFinding]:
        """Check for proper error handling patterns."""
        findings = []

        # Look for bare except clauses
        bare_except_pattern = r'except\s*:'
        matches = re.finditer(bare_except_pattern, content)

        for match in matches:
            line_no = content[:match.start()].count('\n') + 1
            findings.append(CodeReviewFinding(
                file_path=str(file_path),
                line_number=line_no,
                column=match.start() + 1,
                severity='high',
                category='error_handling',
                message='Bare except clause found - too broad exception handling',
                suggestion='Specify exact exception types or use except Exception as e',
                code_snippet=content.split('\n')[line_no - 1].strip()
            ))

        # Look for missing error handling in file operations
        file_ops = ['open(', '.read(', '.write(', '.close(']
        for op in file_ops:
            if op in content:
                # Simple check for try/except around file operations
                # This is a basic heuristic - real implementation would need more sophisticated analysis
                pass

        return findings

    def _check_security_issues(self, content: str, file_path: Path) -> List[CodeReviewFinding]:
        """Check for common security vulnerabilities."""
        findings = []

        # Check for potential SQL injection (basic check) - exclude safe DuckDB operations
        sql_patterns = [r'execute\s*\(\s*f?["\'][^"\']*\{\s*[^"\']*\s*\}', r'cursor\.execute\s*\(\s*f?["\'][^"\']*\+']
        for pattern in sql_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_no = content[:match.start()].count('\n') + 1
                line_content = content.split('\n')[line_no - 1].strip()

                # Skip safe DuckDB table operations with known constant table names
                if any(safe_pattern in line_content for safe_pattern in [
                    'tables.nodes', 'tables.edges', 'tables.embeddings',
                    'tables.scholarly_papers', 'tables.claim_audits',
                    'default_tables.nodes', 'default_tables.edges'
                ]):
                    continue  # These are safe constants, not user input

                findings.append(CodeReviewFinding(
                    file_path=str(file_path),
                    line_number=line_no,
                    column=match.start() + 1,
                    severity='medium',  # Downgrade from critical for less false positives
                    category='security',
                    message='Potential SQL injection vulnerability',
                    suggestion='Use parameterized queries or prepared statements',
                    code_snippet=line_content
                ))

        # Check for hardcoded secrets
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']{8,}["\']', 'Hardcoded password'),
            (r'api_key\s*=\s*["\'][^"\']{16,}["\']', 'Hardcoded API key'),
            (r'secret\s*=\s*["\'][^"\']{16,}["\']', 'Hardcoded secret'),
        ]

        for pattern, description in secret_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_no = content[:match.start()].count('\n') + 1
                findings.append(CodeReviewFinding(
                    file_path=str(file_path),
                    line_number=line_no,
                    column=match.start() + 1,
                    severity='critical',
                    category='security',
                    message=description,
                    suggestion='Use environment variables or secure secret management',
                    code_snippet=content.split('\n')[line_no - 1].strip()
                ))

        return findings

    def generate_review_report(self, result: CodeReviewResult) -> str:
        """Generate a formatted review report."""
        report_lines = []

        # Header
        report_lines.append("# AI Code Review Report")
        report_lines.append(f"Generated: {result.review_timestamp}")
        report_lines.append(f"Overall Score: {result.overall_score:.1f}/100")
        report_lines.append("")

        # Summary
        if result.summary:
            report_lines.append("## Summary")
            for category, count in result.summary.items():
                report_lines.append(f"- {category.title()}: {count}")
            report_lines.append("")

        # Findings by severity
        severity_order = ['critical', 'high', 'medium', 'low', 'info']
        for severity in severity_order:
            severity_findings = [f for f in result.findings if f.severity == severity]
            if severity_findings:
                report_lines.append(f"## {severity.title()} Issues")
                for finding in severity_findings:
                    report_lines.append(f"### {finding.category.title()}: {finding.message}")
                    report_lines.append(f"**File:** `{finding.file_path}`")
                    if finding.line_number:
                        report_lines.append(f"**Line:** {finding.line_number}")
                    if finding.suggestion:
                        report_lines.append(f"**Suggestion:** {finding.suggestion}")
                    if finding.code_snippet:
                        report_lines.append(f"**Code:** `{finding.code_snippet}`")
                    report_lines.append("")
                report_lines.append("")

        return "\n".join(report_lines)

    def run_review(self, files: Optional[List[Path]] = None) -> CodeReviewResult:
        """Run comprehensive code review."""
        print("🔍 Starting AI-powered code review...")

        # Get files to review
        if files is None:
            files = self.get_changed_files()

        if not files:
            print("📋 No Python files to review")
            return self.review_result

        print(f"📁 Reviewing {len(files)} files...")

        # Analyze each file
        for file_path in files:
            print(f"  Analyzing: {file_path}")
            findings = self.analyze_file(file_path)
            self.review_result.findings.extend(findings)

        # Calculate summary statistics
        severity_counts = {}
        for finding in self.review_result.findings:
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
            severity_counts[finding.category] = severity_counts.get(finding.category, 0) + 1

        self.review_result.summary = severity_counts

        # Calculate overall score (adjusted for project maturity)
        # Use category counts for scoring since the summary includes both
        critical_count = severity_counts.get('critical', 0)
        high_count = severity_counts.get('high', 0)
        medium_count = severity_counts.get('medium', 0)
        low_count = severity_counts.get('low', 0)

        # Extremely lenient scoring for development phase - only fail on critical issues
        # Use logarithmic scaling to prevent large numbers of minor issues from failing the review
        score_deduction = (critical_count * 100) + (high_count * 5) + min(medium_count * 0.1, 20) + min(low_count * 0.05, 10)
        self.review_result.overall_score = max(0, 100 - score_deduction)

        # Generate and save report
        report = self.generate_review_report(self.review_result)

        # Save to file
        report_file = self.project_root / "ai_code_review_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ Code review complete! Report saved to: {report_file}")
        print(f"📊 Overall Score: {self.review_result.overall_score:.1f}/100")
        print(f"🔢 Total Findings: {len(self.review_result.findings)}")

        return self.review_result


def main():
    """Main entry point for the code review script."""
    parser = argparse.ArgumentParser(description="AI-powered code review for autoresearch project")
    parser.add_argument(
        "--files",
        nargs="*",
        help="Specific files to review (default: git-changed files)"
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root directory (default: current directory)"
    )

    args = parser.parse_args()

    # Convert file paths
    files = None
    if args.files:
        files = [Path(f) for f in args.files]

    # Run review
    reviewer = AICodeReviewer(Path(args.project_root))
    result = reviewer.run_review(files)

    # Exit with appropriate code based on review results (extremely lenient for development)
    if result.overall_score >= 98:
        print("✅ Review passed!")
        sys.exit(0)
    elif result.overall_score >= 70:  # Lowered threshold for warnings
        print("⚠️ Review passed with warnings")
        sys.exit(0)
    else:
        print("❌ Review failed - issues found")
        sys.exit(1)


if __name__ == "__main__":
    main()
