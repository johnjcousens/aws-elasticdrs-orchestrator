# Copyright Amazon.com and Affiliates. All rights reserved.
# This deliverable is considered Developed Content as defined in the AWS Service Terms.

"""Property-based tests for the copyright header enforcement script.

Feature: copyright-header-enforcement
Uses hypothesis to verify correctness properties across randomized inputs.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

from scripts.apply_copyright_headers import (
    COMMENT_SYNTAX,
    COPYRIGHT_LINE_1,
    COPYRIGHT_LINE_2,
    EXCLUDED_DIRS,
    EXCLUDED_EXTENSIONS,
    EXCLUDED_FILENAMES,
    build_content_with_header,
    has_copyright_header,
    is_excluded,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
ROOT = Path("/fake/project")

# Strategies for non-excluded components — safe directory names, supported
# extensions, and filenames that do NOT collide with any exclusion list.
_safe_dir_chars = st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789_")
safe_dir_name = st.text(alphabet=_safe_dir_chars, min_size=1, max_size=12).filter(
    lambda d: d not in EXCLUDED_DIRS
)
safe_extension = st.sampled_from([".py", ".ts", ".tsx", ".js", ".jsx", ".yaml", ".yml", ".sh", ".css", ".html", ".md"])
safe_filename_stem = st.text(alphabet=_safe_dir_chars, min_size=1, max_size=12)


def _build_safe_filename(stem: str, ext: str) -> str:
    """Build a filename that is guaranteed not to be in EXCLUDED_FILENAMES."""
    name = f"{stem}{ext}"
    while name in EXCLUDED_FILENAMES:
        name = f"x{name}"
    return name


# ---------------------------------------------------------------------------
# Property 4: Exclusion correctness
# Feature: copyright-header-enforcement, Property 4: Exclusion correctness
# Validates: Requirements 2.5, 3.5, 4.5, 6.5, 7.6, 8.5, 10.2, 10.3,
#            11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7
# ---------------------------------------------------------------------------


class TestExclusionCorrectness:
    """Property 4 — files matching any exclusion rule are excluded; files matching none are not."""

    @given(
        excluded_dir=st.sampled_from(sorted(EXCLUDED_DIRS)),
        filename=st.text(alphabet=_safe_dir_chars, min_size=1, max_size=10),
    )
    @settings(max_examples=100)
    def test_exclusion_by_directory(self, excluded_dir: str, filename: str) -> None:
        """Files inside an excluded directory must be excluded.

        **Validates: Requirements 2.5, 3.5, 4.5, 6.5, 7.6, 8.5, 10.2, 10.3, 11.1**
        """
        filepath = ROOT / excluded_dir / f"{filename}.py"
        assert is_excluded(filepath, ROOT) is True

    @given(excluded_ext=st.sampled_from(sorted(EXCLUDED_EXTENSIONS)))
    @settings(max_examples=100)
    def test_exclusion_by_extension(self, excluded_ext: str) -> None:
        """Files with an excluded extension must be excluded.

        **Validates: Requirements 11.2, 11.5**
        """
        filepath = ROOT / "src" / f"somefile{excluded_ext}"
        assert is_excluded(filepath, ROOT) is True

    @given(excluded_name=st.sampled_from(sorted(EXCLUDED_FILENAMES)))
    @settings(max_examples=100)
    def test_exclusion_by_filename(self, excluded_name: str) -> None:
        """Files whose name matches an excluded filename must be excluded.

        **Validates: Requirements 11.3, 11.4, 11.6, 11.7**
        """
        filepath = ROOT / excluded_name
        assert is_excluded(filepath, ROOT) is True

    @given(
        dir_name=safe_dir_name,
        stem=safe_filename_stem,
        ext=safe_extension,
    )
    @settings(max_examples=100)
    def test_non_excluded_files_are_not_excluded(self, dir_name: str, stem: str, ext: str) -> None:
        """Files with no excluded trait must NOT be excluded.

        **Validates: Requirements 2.5, 3.5, 4.5, 6.5, 7.6, 8.5, 10.2, 10.3**
        """
        filename = _build_safe_filename(stem, ext)
        filepath = ROOT / dir_name / filename
        assert is_excluded(filepath, ROOT) is False


# ---------------------------------------------------------------------------
# Property 1: Correct comment syntax per file extension
# Feature: copyright-header-enforcement, Property 1: Correct comment syntax per file extension
# Validates: Requirements 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1
# ---------------------------------------------------------------------------

# Group extensions by expected comment style for parametrize
_HASH_EXTENSIONS = [".py", ".sh", ".yaml", ".yml"]
_SLASH_EXTENSIONS = [".ts", ".tsx", ".js", ".jsx"]
_CSS_EXTENSIONS = [".css"]
_HTML_EXTENSIONS = [".html", ".md"]


class TestCommentSyntaxCorrectness:
    """Property 1 — each supported extension produces a header with the correct comment delimiters."""

    @pytest.mark.parametrize("ext", _HASH_EXTENSIONS)
    def test_comment_syntax_hash_extensions(self, ext: str) -> None:
        """Hash-commented extensions (.py, .sh, .yaml, .yml) use ``# `` prefix.

        **Validates: Requirements 2.1, 4.1, 5.1**
        """
        header = COMMENT_SYNTAX[ext]()
        lines = header.splitlines()
        assert len(lines) == 2, f"Expected 2 header lines for {ext}, got {len(lines)}"
        for line in lines:
            assert line.startswith("# "), f"Line for {ext} must start with '# ', got: {line!r}"
        assert COPYRIGHT_LINE_1 in header, f"Header for {ext} must contain COPYRIGHT_LINE_1"
        assert COPYRIGHT_LINE_2 in header, f"Header for {ext} must contain COPYRIGHT_LINE_2"

    @pytest.mark.parametrize("ext", _SLASH_EXTENSIONS)
    def test_comment_syntax_slash_extensions(self, ext: str) -> None:
        """Slash-commented extensions (.ts, .tsx, .js, .jsx) use ``// `` prefix.

        **Validates: Requirements 3.1, 6.1**
        """
        header = COMMENT_SYNTAX[ext]()
        lines = header.splitlines()
        assert len(lines) == 2, f"Expected 2 header lines for {ext}, got {len(lines)}"
        for line in lines:
            assert line.startswith("// "), f"Line for {ext} must start with '// ', got: {line!r}"
        assert COPYRIGHT_LINE_1 in header, f"Header for {ext} must contain COPYRIGHT_LINE_1"
        assert COPYRIGHT_LINE_2 in header, f"Header for {ext} must contain COPYRIGHT_LINE_2"

    @pytest.mark.parametrize("ext", _CSS_EXTENSIONS)
    def test_comment_syntax_css_extensions(self, ext: str) -> None:
        """CSS extension (.css) uses ``/* ... */`` block comment syntax.

        **Validates: Requirements 6.1**
        """
        header = COMMENT_SYNTAX[ext]()
        assert header.startswith("/* "), f"CSS header must start with '/* ', got: {header[:10]!r}"
        assert header.endswith(" */"), f"CSS header must end with ' */', got: {header[-10:]!r}"
        assert COPYRIGHT_LINE_1 in header, f"CSS header must contain COPYRIGHT_LINE_1"
        assert COPYRIGHT_LINE_2 in header, f"CSS header must contain COPYRIGHT_LINE_2"

    @pytest.mark.parametrize("ext", _HTML_EXTENSIONS)
    def test_comment_syntax_html_extensions(self, ext: str) -> None:
        """HTML/Markdown extensions (.html, .md) use ``<!-- ... -->`` comment syntax.

        **Validates: Requirements 7.1, 8.1**
        """
        header = COMMENT_SYNTAX[ext]()
        assert header.startswith("<!-- "), f"HTML header must start with '<!-- ', got: {header[:10]!r}"
        assert header.endswith(" -->"), f"HTML header must end with ' -->', got: {header[-10:]!r}"
        assert COPYRIGHT_LINE_1 in header, f"HTML header must contain COPYRIGHT_LINE_1"
        assert COPYRIGHT_LINE_2 in header, f"HTML header must contain COPYRIGHT_LINE_2"

    @pytest.mark.parametrize("ext", sorted(COMMENT_SYNTAX.keys()))
    def test_comment_syntax_all_extensions_contain_copyright(self, ext: str) -> None:
        """Every supported extension produces a header containing both copyright lines.

        **Validates: Requirements 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1**
        """
        header = COMMENT_SYNTAX[ext]()
        assert COPYRIGHT_LINE_1 in header, f"Header for {ext} missing COPYRIGHT_LINE_1"
        assert COPYRIGHT_LINE_2 in header, f"Header for {ext} missing COPYRIGHT_LINE_2"


# ---------------------------------------------------------------------------
# Property 11: Header detection consistency
# Feature: copyright-header-enforcement, Property 11: Header detection consistency
# Validates: Requirements 2.3, 13.1, 13.3
# ---------------------------------------------------------------------------

# Supported extensions for random selection in detection tests
_SUPPORTED_EXTENSIONS = sorted(COMMENT_SYNTAX.keys())


class TestHeaderDetectionConsistency:
    """Property 11 — has_copyright_header returns True iff content contains COPYRIGHT_LINE_1."""

    @given(content=st.text(), ext=st.sampled_from(_SUPPORTED_EXTENSIONS))
    @settings(max_examples=100)
    def test_header_detection_with_injected_copyright(self, content: str, ext: str) -> None:
        """Content with COPYRIGHT_LINE_1 injected must be detected as having a header.

        Generates random content, injects COPYRIGHT_LINE_1 at a random position,
        and verifies ``has_copyright_header`` returns True.

        **Validates: Requirements 2.3, 13.1, 13.3**
        """
        injected = content + COPYRIGHT_LINE_1
        assert has_copyright_header(injected, ext) is True

    @given(content=st.text(), ext=st.sampled_from(_SUPPORTED_EXTENSIONS))
    @settings(max_examples=100)
    def test_header_detection_without_copyright(self, content: str, ext: str) -> None:
        """Content without COPYRIGHT_LINE_1 must not be detected as having a header.

        Generates random content, filters out any that accidentally contain the
        copyright line, and verifies ``has_copyright_header`` returns False.

        **Validates: Requirements 2.3, 13.1, 13.3**
        """
        clean_content = content.replace(COPYRIGHT_LINE_1, "")
        assert has_copyright_header(clean_content, ext) is False


# ---------------------------------------------------------------------------
# Property 2: Blank line separation
# Feature: copyright-header-enforcement, Property 2: Blank line separation
# Validates: Requirements 2.2, 3.2, 4.2, 5.4, 6.2, 7.3, 8.2
# ---------------------------------------------------------------------------


class TestBlankLineSeparation:
    """Property 2 — after header insertion, a blank line separates the header from original content."""

    @given(
        content=st.text(min_size=1).filter(lambda s: s.strip()),
        ext=st.sampled_from(_SUPPORTED_EXTENSIONS),
    )
    @settings(max_examples=100)
    def test_blank_line_between_header_and_content(self, content: str, ext: str) -> None:
        """For any non-empty content and supported extension, a blank line separates header from content.

        Generates random non-empty content strings and extensions, applies
        ``build_content_with_header``, then verifies that at least one blank
        line exists between the last line of the header block and the first
        line of the original file content.

        **Validates: Requirements 2.2, 3.2, 4.2, 5.4, 6.2, 7.3, 8.2**
        """
        filepath = f"/fake/project/testfile{ext}"
        result = build_content_with_header(content, ext, filepath)

        # The header text must be present in the result
        header = COMMENT_SYNTAX[ext]()
        assert COPYRIGHT_LINE_1 in result, "Header was not inserted into the result"

        # Find the last line of the header block in the output
        header_lines = header.splitlines()
        last_header_line = header_lines[-1]

        result_lines = result.splitlines()

        # Find the index of the last header line in the result
        last_header_idx = None
        for i, line in enumerate(result_lines):
            if line == last_header_line:
                last_header_idx = i
                break

        assert last_header_idx is not None, (
            f"Could not find last header line {last_header_line!r} in result"
        )

        # There must be at least one more line after the header
        assert last_header_idx + 1 < len(result_lines), (
            "No lines after the header block"
        )

        # The line immediately after the last header line must be blank
        separator_line = result_lines[last_header_idx + 1]
        assert separator_line.strip() == "", (
            f"Expected blank line after header at index {last_header_idx + 1}, "
            f"got: {separator_line!r}"
        )


# ---------------------------------------------------------------------------
# Property 3: Idempotency
# Feature: copyright-header-enforcement, Property 3: Idempotency
# Validates: Requirements 2.3, 3.3, 4.3, 5.5, 6.3, 7.4, 8.3, 13.1, 13.2, 13.3
# ---------------------------------------------------------------------------


class TestIdempotency:
    """Property 3 — applying the header twice produces the same result as applying it once."""

    @given(
        content=st.text(),
        ext=st.sampled_from(_SUPPORTED_EXTENSIONS),
    )
    @settings(max_examples=100)
    def test_idempotency(self, content: str, ext: str) -> None:
        """For any content and extension, build(build(content)) == build(content).

        Applies ``build_content_with_header`` once to get result1, then applies
        it again to result1 to get result2, and asserts they are identical.

        **Validates: Requirements 2.3, 3.3, 4.3, 5.5, 6.3, 7.4, 8.3, 13.1, 13.2, 13.3**
        """
        filepath = f"/fake/project/testfile{ext}"
        result1 = build_content_with_header(content, ext, filepath)
        result2 = build_content_with_header(result1, ext, filepath)
        assert result2 == result1, (
            f"Idempotency violated for ext={ext!r}:\n"
            f"  first application length:  {len(result1)}\n"
            f"  second application length: {len(result2)}"
        )


    # ---------------------------------------------------------------------------
    # Property 5: Shebang preservation
    # Feature: copyright-header-enforcement, Property 5: Shebang preservation
    # Validates: Requirements 5.2, 5.3, 9.2, 10.5, 10.6
    # ---------------------------------------------------------------------------


    class TestShebangPreservation:
        """Property 5 — for .sh and .py files with a shebang, the first line of output is the original shebang."""

        @given(
            shebang=st.sampled_from([
                "#!/usr/bin/env python3",
                "#!/usr/bin/python3",
                "#!/bin/bash",
                "#!/bin/sh",
                "#!/usr/bin/env bash",
            ]),
            body=st.text(min_size=1).filter(lambda s: s.strip()),
            ext=st.sampled_from([".py", ".sh"]),
        )
        @settings(max_examples=100)
        def test_shebang_preserved_as_first_line(self, shebang: str, body: str, ext: str) -> None:
            """For .sh and .py files starting with a shebang, the shebang remains on line 1 after header insertion.

            Generates random shebang lines, random body content, and either .py or .sh
            extension. Constructs content as shebang + newline + body, applies
            ``build_content_with_header``, and asserts the first line of the result
            is the original shebang line.

            **Validates: Requirements 5.2, 5.3, 9.2, 10.5, 10.6**
            """
            content = shebang + "\n" + body
            filepath = f"/fake/project/testfile{ext}"
            result = build_content_with_header(content, ext, filepath)
            assert result.splitlines()[0] == shebang, (
                f"Shebang not preserved as first line for ext={ext!r}:\n"
                f"  expected: {shebang!r}\n"
                f"  got:      {result.splitlines()[0]!r}"
            )



# ---------------------------------------------------------------------------
# Property 6: DOCTYPE placement
# Feature: copyright-header-enforcement, Property 6: DOCTYPE placement
# Validates: Requirements 7.2, 9.6
# ---------------------------------------------------------------------------


class TestDoctypePlacement:
    """Property 6 — for .html files with DOCTYPE, the copyright header appears before the DOCTYPE declaration."""

    @given(
        doctype=st.sampled_from(["<!DOCTYPE html>", "<!doctype html>", "<!DOCTYPE HTML>"]),
        body=st.text(min_size=1).filter(lambda s: s.strip() and "Copyright Amazon.com" not in s),
    )
    @settings(max_examples=100)
    def test_doctype_header_appears_before_doctype(self, doctype: str, body: str) -> None:
        """For .html files starting with a DOCTYPE, the copyright header appears before the DOCTYPE.

        Generates DOCTYPE variations and random body content, constructs content
        as doctype + newline + body, applies ``build_content_with_header``, and
        verifies that:
        1. The copyright header is present in the result.
        2. The DOCTYPE line is still present in the result.
        3. The copyright header appears BEFORE the DOCTYPE line.

        **Validates: Requirements 7.2, 9.6**
        """
        content = doctype + "\n" + body
        filepath = "/fake/project/index.html"
        result = build_content_with_header(content, ".html", filepath)

        # 1. Copyright header must be present
        assert COPYRIGHT_LINE_1 in result, "Copyright header was not inserted into the result"

        # 2. DOCTYPE line must still be present
        assert doctype in result, f"DOCTYPE declaration {doctype!r} was lost from the result"

        # 3. Header appears BEFORE the DOCTYPE — first line is the header, not the DOCTYPE
        result_lines = result.splitlines()
        header = COMMENT_SYNTAX[".html"]()
        first_header_line = header.splitlines()[0]

        assert result_lines[0] == first_header_line, (
            f"First line of output must be the copyright header, not the DOCTYPE.\n"
            f"  expected: {first_header_line!r}\n"
            f"  got:      {result_lines[0]!r}"
        )

        # Find positions to confirm header comes before DOCTYPE
        header_pos = result.index(COPYRIGHT_LINE_1)
        doctype_pos = result.index(doctype)
        assert header_pos < doctype_pos, (
            f"Copyright header (pos {header_pos}) must appear before DOCTYPE (pos {doctype_pos})"
        )


    # ---------------------------------------------------------------------------
    # Property 7: Python coding declaration preservation
    # Feature: copyright-header-enforcement, Property 7: Coding declaration preservation
    # Validates: Requirements 9.3
    # ---------------------------------------------------------------------------


    class TestCodingDeclarationPreservation:
        """Property 7 — for .py files with a coding declaration, the declaration appears before the copyright header."""

        @given(
            coding_decl=st.sampled_from(["# -*- coding: utf-8 -*-", "# coding=utf-8", "# coding: utf-8"]),
            body=st.text(min_size=1).filter(lambda s: s.strip() and "Copyright Amazon.com" not in s),
        )
        @settings(max_examples=100)
        def test_coding_declaration_preserved_before_header(self, coding_decl: str, body: str) -> None:
            """For .py files with a coding declaration, the declaration appears before the copyright header.

            Generates coding declaration variations and random body content, constructs
            content as coding_decl + newline + body, applies ``build_content_with_header``,
            and verifies that:
            1. The coding declaration is present in the result.
            2. The copyright header is present in the result.
            3. The coding declaration line appears BEFORE the copyright header line.

            **Validates: Requirements 9.3**
            """
            content = coding_decl + "\n" + body
            filepath = "/fake/project/module.py"
            result = build_content_with_header(content, ".py", filepath)

            result_lines = result.splitlines()

            # 1. Coding declaration must be present
            assert coding_decl in result, f"Coding declaration {coding_decl!r} was lost from the result"

            # 2. Copyright header must be present
            assert COPYRIGHT_LINE_1 in result, "Copyright header was not inserted into the result"

            # 3. Coding declaration line index must be lower than copyright header line index
            decl_index = next(i for i, line in enumerate(result_lines) if coding_decl in line)
            header_index = next(i for i, line in enumerate(result_lines) if COPYRIGHT_LINE_1 in line)
            assert decl_index < header_index, (
                f"Coding declaration (line {decl_index}) must appear before "
                f"copyright header (line {header_index})"
            )


        # ---------------------------------------------------------------------------
        # Property 8: Trailing newline preservation
        # Feature: copyright-header-enforcement, Property 8: Trailing newline preservation
        # Validates: Requirements 9.9
        # ---------------------------------------------------------------------------

        _SUPPORTED_EXTENSIONS = list(COMMENT_SYNTAX.keys())


        class TestTrailingNewlinePreservation:
            """Property 8 — trailing newline behavior is preserved after header insertion."""

            @given(
                content=st.text(min_size=1).filter(lambda s: s.strip() and "Copyright Amazon.com" not in s),
                ext=st.sampled_from(_SUPPORTED_EXTENSIONS),
            )
            @settings(max_examples=100)
            def test_trailing_newline_preserved_when_present(self, content: str, ext: str) -> None:
                """If the original content ends with a newline, the output also ends with a newline.

                Generates random non-empty content, appends a trailing newline, applies
                ``build_content_with_header``, and verifies the result ends with ``\\n``.

                **Validates: Requirements 9.9**
                """
                content_with_newline = content.rstrip("\n") + "\n"
                filepath = f"/fake/project/file{ext}"
                result = build_content_with_header(content_with_newline, ext, filepath)

                assert result.endswith("\n"), (
                    f"Result should end with newline when original content ends with newline. "
                    f"ext={ext!r}, content tail={content_with_newline[-20:]!r}, result tail={result[-20:]!r}"
                )

            @given(
                content=st.text(min_size=1).filter(lambda s: s.strip() and "Copyright Amazon.com" not in s),
                ext=st.sampled_from(_SUPPORTED_EXTENSIONS),
            )
            @settings(max_examples=100)
            def test_trailing_newline_absent_when_not_present(self, content: str, ext: str) -> None:
                """If the original content does not end with a newline, the output also does not.

                Generates random non-empty content, strips any trailing newlines, applies
                ``build_content_with_header``, and verifies the result does NOT end with ``\\n``.

                **Validates: Requirements 9.9**
                """
                content_no_newline = content.rstrip("\n")
                # Skip if stripping newlines left us with empty/whitespace-only content
                if not content_no_newline.strip():
                    return
                filepath = f"/fake/project/file{ext}"
                result = build_content_with_header(content_no_newline, ext, filepath)

                assert not result.endswith("\n"), (
                    f"Result should NOT end with newline when original content does not end with newline. "
                    f"ext={ext!r}, content tail={content_no_newline[-20:]!r}, result tail={result[-20:]!r}"
                )



# ---------------------------------------------------------------------------
# Property 9: YAML document separator handling
# Validates: Requirements 9.5
# ---------------------------------------------------------------------------


class TestYamlSeparatorHandling:
    """Property 9 — for YAML files starting with ``---``, the header appears BEFORE the separator."""

    @given(
        body=st.text(min_size=1).filter(lambda s: s.strip() and "Copyright Amazon.com" not in s),
        ext=st.sampled_from([".yaml", ".yml"]),
    )
    @settings(max_examples=100)
    def test_yaml_separator_header_before_separator(self, body: str, ext: str) -> None:
        """The copyright header appears before the ``---`` separator in the output.

        Generates random YAML body content prefixed with ``---\\n``, applies
        ``build_content_with_header``, and verifies:

        1. The copyright header is present in the result.
        2. The ``---`` separator is still present in the result.
        3. The header appears before the ``---`` separator (header line index < separator line index).

        **Validates: Requirements 9.5**
        """
        content = "---\n" + body
        filepath = f"/fake/project/file{ext}"
        result = build_content_with_header(content, ext, filepath)

        result_lines = result.split("\n")

        # 1. Copyright header is present
        assert COPYRIGHT_LINE_1 in result, (
            f"Copyright header should be present in result. ext={ext!r}"
        )

        # 2. The --- separator is still present
        separator_indices = [i for i, line in enumerate(result_lines) if line.strip() == "---"]
        assert separator_indices, (
            f"YAML --- separator should still be present in result. ext={ext!r}"
        )

        # 3. Header appears BEFORE the --- separator
        header_indices = [i for i, line in enumerate(result_lines) if COPYRIGHT_LINE_1 in line]
        assert header_indices, (
            f"Copyright header line should be found in result lines. ext={ext!r}"
        )

        first_header_line = header_indices[0]
        first_separator_line = separator_indices[0]
        assert first_header_line < first_separator_line, (
            f"Header (line {first_header_line}) should appear before --- separator "
            f"(line {first_separator_line}). ext={ext!r}"
        )

# ---------------------------------------------------------------------------
# Property 10: Original content preservation
# Feature: copyright-header-enforcement, Property 10: Original content preservation
# Validates: Requirements 9.1, 9.4, 9.7, 10.5
# ---------------------------------------------------------------------------


class TestOriginalContentPreservation:
    """Property 10 — after header insertion, all original non-empty lines are present in the output."""

    @given(
        content=st.text(min_size=1).filter(lambda s: s.strip() and "Copyright Amazon.com" not in s),
        ext=st.sampled_from(_SUPPORTED_EXTENSIONS),
    )
    @settings(max_examples=100)
    def test_content_preservation(self, content: str, ext: str) -> None:
        """All original non-empty lines survive header insertion (the script only adds, never removes).

        Generates random multi-line content, applies ``build_content_with_header``,
        and verifies that every non-empty line from the original content appears
        in the result lines.

        **Validates: Requirements 9.1, 9.4, 9.7, 10.5**
        """
        filepath = f"/fake/project/file{ext}"
        result = build_content_with_header(content, ext, filepath)

        result_lines = result.splitlines()
        original_non_empty_lines = [line for line in content.splitlines() if line.strip()]

        for original_line in original_non_empty_lines:
            assert original_line in result_lines, (
                f"Original non-empty line {original_line!r} should be present in result. ext={ext!r}"
            )
