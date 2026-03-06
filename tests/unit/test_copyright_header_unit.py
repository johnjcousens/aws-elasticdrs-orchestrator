# Copyright Amazon.com and Affiliates. All rights reserved.
# This deliverable is considered Developed Content as defined in the AWS Service Terms.

"""Unit tests for the copyright header enforcement script.

Feature: copyright-header-enforcement
Tests LICENSE.txt creation, process_file behavior, and file-type header formatting.
"""
from __future__ import annotations

import os
from pathlib import Path

from scripts.apply_copyright_headers import (
    COPYRIGHT_LINE_1,
    COPYRIGHT_LINE_2,
    Stats,
    build_content_with_header,
    create_license_file,
    process_file,
)


# ---------------------------------------------------------------------------
# LICENSE.txt creation tests (Requirements 1.1, 1.2, 1.3, 1.4)
# ---------------------------------------------------------------------------


class TestLicenseFileCreation:
    """Tests for create_license_file function."""

    def test_license_created_when_missing(self, tmp_path: Path) -> None:
        """Verify LICENSE.txt is created when it does not exist."""
        result = create_license_file(tmp_path)

        license_path = tmp_path / "LICENSE.txt"
        assert result is True
        assert license_path.exists()

    def test_license_contains_aws_copyright(self, tmp_path: Path) -> None:
        """Verify LICENSE.txt starts with the AWS copyright line (Req 1.1)."""
        create_license_file(tmp_path)

        content = (tmp_path / "LICENSE.txt").read_text(encoding="utf-8")
        first_line = content.split("\n")[0]
        assert "\u00a9 2025 Amazon Web Services, Inc. or its affiliates. All Rights Reserved." in first_line

    def test_license_contains_apache_text(self, tmp_path: Path) -> None:
        """Verify LICENSE.txt contains the Apache 2.0 license text (Req 1.2)."""
        create_license_file(tmp_path)

        content = (tmp_path / "LICENSE.txt").read_text(encoding="utf-8")
        assert "Apache License" in content
        assert "Version 2.0" in content
        assert "TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION" in content

    def test_license_at_project_root(self, tmp_path: Path) -> None:
        """Verify LICENSE.txt is created at the given root directory (Req 1.3)."""
        create_license_file(tmp_path)

        assert (tmp_path / "LICENSE.txt").is_file()

    def test_license_skip_when_exists(self, tmp_path: Path) -> None:
        """Verify existing LICENSE.txt is not overwritten (Req 1.4)."""
        license_path = tmp_path / "LICENSE.txt"
        original_content = "Existing license content\n"
        license_path.write_text(original_content, encoding="utf-8")

        result = create_license_file(tmp_path)

        assert result is False
        assert license_path.read_text(encoding="utf-8") == original_content

    def test_license_skip_preserves_content(self, tmp_path: Path) -> None:
        """Verify skip does not alter the existing file content."""
        license_path = tmp_path / "LICENSE.txt"
        original_content = "Custom license\nWith multiple lines\n"
        license_path.write_text(original_content, encoding="utf-8")

        create_license_file(tmp_path)

        assert license_path.read_text(encoding="utf-8") == original_content


# ---------------------------------------------------------------------------
# process_file tests (Requirements 9.8, 12.2, 12.3, 12.4)
# ---------------------------------------------------------------------------


class TestProcessFile:
    """Tests for process_file behavior and error handling."""

    def test_process_unreadable_file_increments_errored(self, tmp_path: Path) -> None:
        """Verify unreadable file increments files_errored and doesn't crash (Req 12.4)."""
        py_file = tmp_path / "unreadable.py"
        py_file.write_text("print('hello')\n", encoding="utf-8")
        os.chmod(py_file, 0o000)

        stats = Stats()
        process_file(py_file, tmp_path, stats)

        assert stats.files_errored == 1
        assert stats.files_processed == 1
        assert stats.files_modified == 0
        assert len(stats.errors) == 1

        # Restore permissions for cleanup
        os.chmod(py_file, 0o644)

    def test_process_empty_file_gets_header(self, tmp_path: Path) -> None:
        """Verify empty .py file gets the copyright header added (Req 9.8)."""
        py_file = tmp_path / "empty.py"
        py_file.write_text("", encoding="utf-8")

        stats = Stats()
        process_file(py_file, tmp_path, stats)

        content = py_file.read_text(encoding="utf-8")
        assert COPYRIGHT_LINE_1 in content
        assert COPYRIGHT_LINE_2 in content
        assert stats.files_modified == 1

    def test_process_whitespace_only_file_gets_header(self, tmp_path: Path) -> None:
        """Verify file with only whitespace gets header added correctly."""
        py_file = tmp_path / "whitespace.py"
        py_file.write_text("   \n\n  \n", encoding="utf-8")

        stats = Stats()
        process_file(py_file, tmp_path, stats)

        content = py_file.read_text(encoding="utf-8")
        assert COPYRIGHT_LINE_1 in content
        assert COPYRIGHT_LINE_2 in content
        assert stats.files_modified == 1

    def test_process_stats_counting_accuracy(self, tmp_path: Path) -> None:
        """Verify all stats counters are correct after processing multiple files (Req 12.2, 12.3)."""
        # File that needs a header
        needs_header = tmp_path / "needs.py"
        needs_header.write_text("x = 1\n", encoding="utf-8")

        # File that already has a header
        has_header = tmp_path / "has.py"
        has_header.write_text(f"# {COPYRIGHT_LINE_1}\n# {COPYRIGHT_LINE_2}\n\nx = 2\n", encoding="utf-8")

        # Another file that needs a header
        also_needs = tmp_path / "also_needs.py"
        also_needs.write_text("y = 3\n", encoding="utf-8")

        stats = Stats()
        process_file(needs_header, tmp_path, stats)
        process_file(has_header, tmp_path, stats)
        process_file(also_needs, tmp_path, stats)

        assert stats.files_processed == 3
        assert stats.files_modified == 2
        assert stats.files_skipped == 1
        assert stats.files_errored == 0

    def test_process_already_headered_file_skipped(self, tmp_path: Path) -> None:
        """Verify file with existing header is skipped and files_skipped incremented (Req 12.3)."""
        py_file = tmp_path / "existing.py"
        original = f"# {COPYRIGHT_LINE_1}\n# {COPYRIGHT_LINE_2}\n\nimport os\n"
        py_file.write_text(original, encoding="utf-8")

        stats = Stats()
        process_file(py_file, tmp_path, stats)

        assert stats.files_skipped == 1
        assert stats.files_modified == 0
        assert stats.files_processed == 1
        # File content unchanged
        assert py_file.read_text(encoding="utf-8") == original


# ---------------------------------------------------------------------------
# File-type header formatting tests (Requirements 2.1, 3.1, 4.1, 5.1, 5.2, 6.1, 7.1, 7.2, 8.1, 9.5)
# ---------------------------------------------------------------------------


class TestFileTypeFormatting:
    """Tests for build_content_with_header across all supported file types."""

    def test_format_python_header(self) -> None:
        """Verify Python files get # comment header (Req 2.1)."""
        content = "import os\n"
        result = build_content_with_header(content, ".py", "example.py")

        assert f"# {COPYRIGHT_LINE_1}" in result
        assert f"# {COPYRIGHT_LINE_2}" in result
        assert result.index(f"# {COPYRIGHT_LINE_1}") < result.index("import os")

    def test_format_typescript_header(self) -> None:
        """Verify TypeScript files get // comment header (Req 3.1)."""
        content = "const x = 1;\n"
        result = build_content_with_header(content, ".ts", "example.ts")

        assert f"// {COPYRIGHT_LINE_1}" in result
        assert f"// {COPYRIGHT_LINE_2}" in result
        assert result.index(f"// {COPYRIGHT_LINE_1}") < result.index("const x = 1;")

    def test_format_yaml_header(self) -> None:
        """Verify YAML files get # comment header (Req 4.1)."""
        content = "key: value\n"
        result = build_content_with_header(content, ".yaml", "example.yaml")

        assert f"# {COPYRIGHT_LINE_1}" in result
        assert f"# {COPYRIGHT_LINE_2}" in result
        assert result.index(f"# {COPYRIGHT_LINE_1}") < result.index("key: value")

    def test_format_shell_header(self) -> None:
        """Verify Shell files get # comment header (Req 5.1)."""
        content = "echo hello\n"
        result = build_content_with_header(content, ".sh", "example.sh")

        assert f"# {COPYRIGHT_LINE_1}" in result
        assert f"# {COPYRIGHT_LINE_2}" in result
        assert result.index(f"# {COPYRIGHT_LINE_1}") < result.index("echo hello")

    def test_format_css_header(self) -> None:
        """Verify CSS files get block comment header (Req 6.1)."""
        content = "body { margin: 0; }\n"
        result = build_content_with_header(content, ".css", "example.css")

        assert f"/* {COPYRIGHT_LINE_1}" in result
        assert f" * {COPYRIGHT_LINE_2} */" in result
        assert result.index(f"/* {COPYRIGHT_LINE_1}") < result.index("body { margin: 0; }")

    def test_format_html_header(self) -> None:
        """Verify HTML files get <!-- --> comment header (Req 7.1)."""
        content = "<html><body>Hello</body></html>\n"
        result = build_content_with_header(content, ".html", "example.html")

        assert f"<!-- {COPYRIGHT_LINE_1}" in result
        assert f"     {COPYRIGHT_LINE_2} -->" in result
        assert result.index(f"<!-- {COPYRIGHT_LINE_1}") < result.index("<html>")

    def test_format_markdown_header(self) -> None:
        """Verify Markdown files get <!-- --> comment header (Req 8.1)."""
        content = "# My Document\n\nSome text.\n"
        result = build_content_with_header(content, ".md", "README.md")

        assert f"<!-- {COPYRIGHT_LINE_1}" in result
        assert f"     {COPYRIGHT_LINE_2} -->" in result
        assert result.index(f"<!-- {COPYRIGHT_LINE_1}") < result.index("# My Document")

    def test_format_shell_shebang_preservation(self) -> None:
        """Verify shebang stays on line 1 in shell scripts (Req 5.2)."""
        content = "#!/bin/bash\necho hello\n"
        result = build_content_with_header(content, ".sh", "deploy.sh")

        lines = result.split("\n")
        assert lines[0] == "#!/bin/bash"
        assert f"# {COPYRIGHT_LINE_1}" in result
        assert result.index("#!/bin/bash") < result.index(f"# {COPYRIGHT_LINE_1}")

    def test_format_yaml_separator_handling(self) -> None:
        """Verify YAML --- separator: header appears BEFORE --- (Req 9.5)."""
        content = "---\nAWSTemplateFormatVersion: '2010-09-09'\n"
        result = build_content_with_header(content, ".yaml", "template.yaml")

        assert "---" in result
        assert f"# {COPYRIGHT_LINE_1}" in result
        assert result.index(f"# {COPYRIGHT_LINE_1}") < result.index("---")

    def test_format_python_shebang_and_coding_declaration(self) -> None:
        """Verify Python shebang + coding declaration both preserved before header (Req 5.2, 9.3)."""
        content = "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\nimport os\n"
        result = build_content_with_header(content, ".py", "script.py")

        lines = result.split("\n")
        assert lines[0] == "#!/usr/bin/env python3"
        assert lines[1] == "# -*- coding: utf-8 -*-"
        assert f"# {COPYRIGHT_LINE_1}" in result
        # Both preserved lines come before the header
        header_idx = result.index(f"# {COPYRIGHT_LINE_1}")
        assert result.index("#!/usr/bin/env python3") < header_idx
        assert result.index("# -*- coding: utf-8 -*-") < header_idx
        # Original content preserved after header
        assert "import os" in result

    def test_format_html_doctype_placement(self) -> None:
        """Verify HTML header appears before DOCTYPE declaration (Req 7.2)."""
        content = "<!DOCTYPE html>\n<html><body>Hello</body></html>\n"
        result = build_content_with_header(content, ".html", "index.html")

        assert f"<!-- {COPYRIGHT_LINE_1}" in result
        assert "<!DOCTYPE html>" in result
        assert result.index(f"<!-- {COPYRIGHT_LINE_1}") < result.index("<!DOCTYPE html>")
