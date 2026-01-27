#!/usr/bin/env python3
"""
Code Quality Checker for Development Principles
Validates code against project-specific quality standards
"""

import re
import sys
from pathlib import Path
from typing import List

# Patterns for temporal references in comments
# These indicate comments describing history rather than current state
TEMPORAL_PATTERNS = [
    r"\b(recently|just)\s+(refactored|moved|updated|changed|fixed|added|removed)\b",
    r"\b(was|were|used to|previously)\s+",
    r"\b(old|legacy)\s+(code|implementation|version|approach|method|function)\b",
    r"#.*\bFIXED:",  # Comments with "FIXED:" indicate historical context
    r"#.*\b(moved from|updated to|changed to|refactored to)\b",
]

# Patterns for bad naming conventions
BAD_NAME_PATTERNS = [
    r"\b(New|Old|Legacy|Deprecated|Updated|Improved|Enhanced|Fixed|Temp|Tmp)\w+",
    r"\w+(New|Old|Legacy|Deprecated|Updated|Improved|Enhanced|Fixed|Temp|Tmp)\b",
]

# Exclusions - legitimate names that match patterns but are acceptable
NAME_EXCLUSIONS = {
    "TemporaryDirectory",  # Python stdlib
    "TemporaryPassword",  # AWS Cognito API
    "toFixed",  # JavaScript Number method
    "lastUpdated",  # Standard field name for timestamps
    "totalAfterNew",  # Domain-specific: total count after adding new items
    "statusOld",  # Migration script - temporary field name
}

# Patterns for redundant comments (what instead of why)
REDUNDANT_COMMENT_PATTERNS = [
    r"#\s*(This function|This method|This class)\s+(gets?|sets?|returns?|creates?|deletes?|updates?)",
    r"//\s*(This function|This method|This class)\s+(gets?|sets?|returns?|creates?|deletes?|updates?)",
]

# Pattern for empty docstrings
EMPTY_DOCSTRING_PATTERN = (
    r'^\s*def\s+\w+\([^)]*\)(?:\s*->\s*[^:]+)?:\s*"""[\s]*"""'
)


class CodeQualityIssue:
    def __init__(
        self,
        file_path: str,
        line_num: int,
        issue_type: str,
        message: str,
        line_content: str,
    ):
        self.file_path = file_path
        self.line_num = line_num
        self.issue_type = issue_type
        self.message = message
        self.line_content = line_content

    def __str__(self):
        return f"{self.file_path}:{self.line_num}: [{self.issue_type}] {self.message}\n  {self.line_content.strip()}"


def check_temporal_references(
    file_path: str, content: str
) -> List[CodeQualityIssue]:
    """Check for temporal references in comments"""
    issues = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        # Check if line is a comment
        if "#" in line or "//" in line:
            comment_part = (
                line.split("#")[-1] if "#" in line else line.split("//")[-1]
            )

            for pattern in TEMPORAL_PATTERNS:
                if re.search(pattern, comment_part, re.IGNORECASE):
                    issues.append(
                        CodeQualityIssue(
                            file_path=file_path,
                            line_num=line_num,
                            issue_type="TEMPORAL_REFERENCE",
                            message="Comment contains temporal reference - describe code as it is NOW",
                            line_content=line,
                        )
                    )
                    break

    return issues


def check_bad_naming(file_path: str, content: str) -> List[CodeQualityIssue]:
    """Check for bad naming conventions with historical context"""
    issues = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        # Skip comments
        if line.strip().startswith("#") or line.strip().startswith("//"):
            continue

        for pattern in BAD_NAME_PATTERNS:
            matches = re.finditer(pattern, line)
            for match in matches:
                matched_name = match.group()
                # Skip if in exclusion list
                if matched_name in NAME_EXCLUSIONS:
                    continue

                issues.append(
                    CodeQualityIssue(
                        file_path=file_path,
                        line_num=line_num,
                        issue_type="BAD_NAMING",
                        message=f"Name contains historical context: '{matched_name}' - use domain-focused names",
                        line_content=line,
                    )
                )

    return issues


def check_redundant_comments(
    file_path: str, content: str
) -> List[CodeQualityIssue]:
    """Check for redundant comments that describe WHAT instead of WHY"""
    issues = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        for pattern in REDUNDANT_COMMENT_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append(
                    CodeQualityIssue(
                        file_path=file_path,
                        line_num=line_num,
                        issue_type="REDUNDANT_COMMENT",
                        message="Comment describes WHAT code does instead of WHY - code should be self-explanatory",
                        line_content=line,
                    )
                )
                break

    return issues


def check_empty_docstrings(
    file_path: str, content: str
) -> List[CodeQualityIssue]:
    """Check for empty docstrings in function definitions"""
    issues = []

    # Only check Python files
    if not file_path.endswith(".py"):
        return issues

    # Find all function definitions with empty docstrings
    pattern = EMPTY_DOCSTRING_PATTERN
    for match in re.finditer(pattern, content, re.MULTILINE):
        line_num = content[: match.start()].count("\n") + 1
        func_match = re.search(r"def\s+(\w+)", match.group())
        func_name = func_match.group(1) if func_match else "unknown"

        issues.append(
            CodeQualityIssue(
                file_path=file_path,
                line_num=line_num,
                issue_type="EMPTY_DOCSTRING",
                message=f"Function '{func_name}' has empty docstring - add purpose, parameters, returns",
                line_content=match.group().split("\n")[0],
            )
        )

    return issues


def check_file(file_path: Path) -> List[CodeQualityIssue]:
    """Check a single file for code quality issues"""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
        return []

    issues = []
    file_path_str = str(file_path)

    # Run all checks
    issues.extend(check_temporal_references(file_path_str, content))
    issues.extend(check_bad_naming(file_path_str, content))
    issues.extend(check_redundant_comments(file_path_str, content))
    issues.extend(check_empty_docstrings(file_path_str, content))

    return issues


def main():
    """Main entry point"""
    # Directories to check
    check_dirs = [
        Path("lambda"),
        Path("frontend/src"),
        Path("scripts"),
    ]

    # File extensions to check
    extensions = {".py", ".ts", ".tsx", ".js", ".jsx"}

    # Files/patterns to exclude
    exclude_patterns = [
        "*_backup.*",
        "*.backup",
        "migrate-*.py",  # One-time migration scripts
        "migrate_*.py",
    ]

    # Collect all files to check
    files_to_check = []
    for check_dir in check_dirs:
        if check_dir.exists():
            for ext in extensions:
                for file_path in check_dir.rglob(f"*{ext}"):
                    # Skip excluded files
                    if any(
                        file_path.match(pattern)
                        for pattern in exclude_patterns
                    ):
                        continue
                    files_to_check.append(file_path)

    # Check all files
    all_issues = []
    for file_path in files_to_check:
        issues = check_file(file_path)
        all_issues.extend(issues)

    # Report results
    if all_issues:
        print("=" * 80)
        print("CODE QUALITY ISSUES FOUND")
        print("=" * 80)
        print()
        # Group by issue type
        by_type = {}
        for issue in all_issues:
            if issue.issue_type not in by_type:
                by_type[issue.issue_type] = []
            by_type[issue.issue_type].append(issue)

        for issue_type, issues in by_type.items():
            print(f"\n{issue_type} ({len(issues)} issues):")
            print("-" * 80)
            for issue in issues:
                print(f"\n{issue}")

        print()
        print("=" * 80)
        print(f"Total issues: {len(all_issues)}")
        print("=" * 80)
        print()
        print("Development Principles Reminder:")
        print("  - Comments should describe WHY, not WHAT")
        print("  - No temporal references (recently, moved, updated, etc.)")
        print("  - Use domain-focused names without historical context")
        print("  - Code should be self-explanatory")
        print()

        # Exit with error code
        sys.exit(1)
    else:
        print("✅ All code quality checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
