#!/usr/bin/env python3
"""
Quality Reporting System for AWS DRS Orchestration Project

This script generates comprehensive code quality reports by aggregating results
from Black, Flake8, and isort tools. It provides both JSON and HTML outputs
with compliance metrics and trend analysis.

Usage:
    python scripts/generate_quality_report.py [--output-dir reports] [--format json,html]
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class QualityReporter:
    """Generate comprehensive code quality reports."""

    def __init__(self, output_dir: str = "reports"):
        """Initialize the quality reporter.

        Args:
            output_dir: Directory to store generated reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now()

        # Define Python files to analyze
        self.python_files = self._discover_python_files()

    def _discover_python_files(self) -> List[Path]:
        """Discover all Python files in the project."""
        python_files = []

        # Lambda functions
        lambda_dir = Path("lambda")
        if lambda_dir.exists():
            python_files.extend(lambda_dir.glob("*.py"))

        # Scripts
        scripts_dir = Path("scripts")
        if scripts_dir.exists():
            python_files.extend(scripts_dir.glob("*.py"))

        # Tests
        tests_dir = Path("tests")
        if tests_dir.exists():
            python_files.extend(tests_dir.rglob("*.py"))

        # Root level Python files
        python_files.extend(Path(".").glob("*.py"))

        return [f for f in python_files if f.is_file()]

    def run_black_check(self) -> Dict[str, Any]:
        """Run Black formatter in check mode."""
        print("Running Black formatter check...")

        try:
            # Run Black in check mode
            result = subprocess.run(
                ["python", "-m", "black", "--check", "--diff"]
                + [str(f) for f in self.python_files],
                capture_output=True,
                text=True,
                timeout=60,
            )

            return {
                "tool": "black",
                "status": "passed" if result.returncode == 0 else "failed",
                "files_checked": len(self.python_files),
                "files_needing_format": (
                    0 if result.returncode == 0 else "unknown"
                ),
                "output": result.stdout,
                "errors": result.stderr,
                "return_code": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "tool": "black",
                "status": "timeout",
                "error": "Black check timed out after 60 seconds",
            }
        except Exception as e:
            return {"tool": "black", "status": "error", "error": str(e)}

    def run_flake8_check(self) -> Dict[str, Any]:
        """Run Flake8 linter."""
        print("Running Flake8 linter...")

        try:
            # Run Flake8 with JSON-like output
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "flake8",
                    "--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s",
                ]
                + [str(f) for f in self.python_files],
                capture_output=True,
                text=True,
                timeout=60,
            )

            violations = []
            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if ":" in line:
                        parts = line.split(":", 3)
                        if len(parts) >= 4:
                            violations.append(
                                {
                                    "file": parts[0],
                                    "line": (
                                        int(parts[1])
                                        if parts[1].isdigit()
                                        else 0
                                    ),
                                    "column": (
                                        int(parts[2])
                                        if parts[2].isdigit()
                                        else 0
                                    ),
                                    "message": parts[3].strip(),
                                }
                            )

            return {
                "tool": "flake8",
                "status": "passed" if result.returncode == 0 else "failed",
                "files_checked": len(self.python_files),
                "total_violations": len(violations),
                "violations": violations,
                "output": result.stdout,
                "errors": result.stderr,
                "return_code": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "tool": "flake8",
                "status": "timeout",
                "error": "Flake8 check timed out after 60 seconds",
            }
        except Exception as e:
            return {"tool": "flake8", "status": "error", "error": str(e)}

    def run_isort_check(self) -> Dict[str, Any]:
        """Run isort import sorter in check mode."""
        print("Running isort import check...")

        try:
            # Run isort in check mode
            result = subprocess.run(
                ["python", "-m", "isort", "--check-only", "--diff"]
                + [str(f) for f in self.python_files],
                capture_output=True,
                text=True,
                timeout=60,
            )

            return {
                "tool": "isort",
                "status": "passed" if result.returncode == 0 else "failed",
                "files_checked": len(self.python_files),
                "files_needing_sort": (
                    0 if result.returncode == 0 else "unknown"
                ),
                "output": result.stdout,
                "errors": result.stderr,
                "return_code": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "tool": "isort",
                "status": "timeout",
                "error": "isort check timed out after 60 seconds",
            }
        except Exception as e:
            return {"tool": "isort", "status": "error", "error": str(e)}

    def calculate_compliance_metrics(
        self, results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall compliance metrics with baseline support."""
        total_files = len(self.python_files)

        # Check if we have a baseline violations file
        baseline_file = "baseline_violations_report.txt"
        baseline_count = 0
        if os.path.exists(baseline_file):
            try:
                with open(baseline_file, "r") as f:
                    content = f.read()
                    # Extract baseline count from the file
                    for line in content.split("\n"):
                        if "violations documented as baseline" in line:
                            import re

                            match = re.search(
                                r"(\d+) violations documented", line
                            )
                            if match:
                                baseline_count = int(match.group(1))
                                break
            except Exception:
                baseline_count = 0

        # Get Flake8 violations for detailed metrics
        flake8_violations = results.get("flake8", {}).get(
            "total_violations", 0
        )

        # Calculate compliance with baseline approach
        if baseline_count > 0 and flake8_violations <= baseline_count:
            # If violations are at or below baseline, consider flake8 as passing
            tools_passed = sum(
                [
                    results.get("black", {}).get("status") == "passed",
                    results.get("isort", {}).get("status") == "passed",
                    True,  # flake8 considered passing if at/below baseline
                ]
            )
            flake8_status = "baseline_compliant"
        else:
            # Standard compliance calculation
            tools_passed = sum(
                1
                for result in results.values()
                if result.get("status") == "passed"
            )
            flake8_status = results.get("flake8", {}).get("status", "failed")

        total_tools = len(results)

        # Calculate compliance percentage
        tool_compliance = (
            (tools_passed / total_tools * 100) if total_tools > 0 else 0
        )

        return {
            "total_files_analyzed": total_files,
            "tools_run": total_tools,
            "tools_passed": tools_passed,
            "tool_compliance_percentage": round(tool_compliance, 2),
            "flake8_violations": flake8_violations,
            "baseline_violations": baseline_count,
            "flake8_status": flake8_status,
            "overall_status": (
                "PASSED" if tools_passed == total_tools else "FAILED"
            ),
            "timestamp": self.timestamp.isoformat(),
            "files_analyzed": [str(f) for f in self.python_files],
        }

    def generate_json_report(
        self, results: Dict[str, Any], metrics: Dict[str, Any]
    ) -> Path:
        """Generate JSON format report."""
        report_data = {
            "metadata": {
                "generated_at": self.timestamp.isoformat(),
                "generator": "AWS DRS Orchestration Quality Reporter",
                "version": "1.0.0",
            },
            "summary": metrics,
            "tool_results": results,
        }

        json_file = (
            self.output_dir
            / f"quality_report_{self.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(json_file, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"JSON report generated: {json_file}")
        return json_file

    def generate_html_report(
        self, results: Dict[str, Any], metrics: Dict[str, Any]
    ) -> Path:
        """Generate HTML format report."""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Quality Report - AWS DRS Orchestration</title>
    <style>
        body {{font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5;}}
        .container {{max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);}}
        .header {{border-bottom: 2px solid #e1e5e9; padding-bottom: 20px; margin-bottom: 30px;}}
        .header h1 {{color: #232f3e; margin: 0; font-size: 28px;}}
        .header .subtitle {{color: #666; margin-top: 5px;}}
        .metrics {{display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px;}}
        .metric-card {{background: #f8f9fa; padding: 20px; border-radius: 6px; border-left: 4px solid #007dbc;}}
        .metric-value {{font-size: 24px; font-weight: bold; color: #232f3e;}}
        .metric-label {{color: #666; font-size: 14px; margin-top: 5px;}}
        .status-passed {{color: #16a34a;}}
        .status-failed {{color: #dc2626;}}
        .tool-section {{margin-bottom: 30px;}}
        .tool-header {{background: #232f3e; color: white; padding: 15px; border-radius: 6px 6px 0 0; margin: 0;}}
        .tool-content {{border: 1px solid #e1e5e9; border-top: none; padding: 20px; border-radius: 0 0 6px 6px;}}
        .violation {{background: #fef2f2; border: 1px solid #fecaca; padding: 10px; margin: 5px 0; border-radius: 4px;}}
        .violation-file {{font-weight: bold; color: #991b1b;}}
        .violation-message {{color: #7f1d1d; margin-top: 5px;}}
        .no-violations {{color: #16a34a; font-weight: bold;}}
        pre {{background: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto;}}
        .files-list {{background: #f8f9fa; padding: 15px; border-radius: 4px;}}
        .files-list ul {{margin: 0; padding-left: 20px;}}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Code Quality Report</h1>
            <div class="subtitle">AWS DRS Orchestration Project - Generated on {timestamp}</div>
        </div>

        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value {status_class}">{overall_status}</div>
                <div class="metric-label">Overall Status</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{compliance_percentage}%</div>
                <div class="metric-label">Tool Compliance</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{total_files}</div>
                <div class="metric-label">Files Analyzed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{flake8_violations}</div>
                <div class="metric-label">Flake8 Violations</div>
            </div>
        </div>

        {tool_sections}

        <div class="tool-section">
            <h3 class="tool-header">Files Analyzed</h3>
            <div class="tool-content">
                <div class="files-list">
                    <ul>
                        {files_list}
                    </ul>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
        """

        # Generate tool sections
        tool_sections = []
        for tool_name, result in results.items():
            status_class = (
                "status-passed"
                if result.get("status") == "passed"
                else "status-failed"
            )
            status_text = result.get("status", "unknown").upper()

            content = '<div class="tool-content">'
            content += f'<p><strong>Status:</strong> <span class="{status_class}">{status_text}</span></p>'  # noqa: E231

            if tool_name == "flake8" and result.get("violations"):
                violations_list = result.get("violations", [])
                violations_count = len(violations_list)
                content += f"<p><strong>Total Violations:</strong> {violations_count}</p>"  # noqa: E231
                content += '<div class="violations">'
                for violation in violations_list[
                    :10
                ]:  # Show first 10 violations
                    file_path = violation.get("file", "")
                    line_num = violation.get("line", 0)
                    col_num = violation.get("column", 0)
                    message = violation.get("message", "")
                    content += (
                        f'<div class="violation">'
                        f'<div class="violation-file">{file_path}: {line_num}: {col_num}</div>'
                        f'<div class="violation-message">{message}</div>'
                        f"</div>"
                    )
                if len(violations_list) > 10:
                    remaining_count = len(violations_list) - 10
                    content += f"<p><em>... and {remaining_count} more violations</em></p>"
                content += "</div>"
            elif result.get("status") == "passed":
                content += (
                    '<div class="no-violations">✓ No violations found</div>'
                )

            if result.get("output") and result.get("status") != "passed":
                output_text = result.get("output", "")[:1000]
                content += (
                    f"<h4>Output:</h4><pre>{output_text}</pre>"  # noqa: E231
                )

            content += "</div>"

            tool_title = tool_name.title()
            tool_sections.append(
                f'<div class="tool-section">'
                f'<h3 class="tool-header">{tool_title} Results</h3>'
                f"{content}"
                f"</div>"
            )

        # Generate files list
        files_list = "\n".join(
            f"<li>{f}</li>" for f in metrics["files_analyzed"]
        )

        # Fill template
        html_content = html_template.format(
            timestamp=self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            overall_status=metrics["overall_status"],
            status_class=(
                "status-passed"
                if metrics["overall_status"] == "PASSED"
                else "status-failed"
            ),
            compliance_percentage=metrics["tool_compliance_percentage"],
            total_files=metrics["total_files_analyzed"],
            flake8_violations=metrics["flake8_violations"],
            tool_sections="".join(tool_sections),
            files_list=files_list,
        )

        html_file = (
            self.output_dir
            / f"quality_report_{self.timestamp.strftime('%Y%m%d_%H%M%S')}.html"
        )

        with open(html_file, "w") as f:
            f.write(html_content)

        print(f"HTML report generated: {html_file}")
        return html_file

    def store_historical_data(self, metrics: Dict[str, Any]) -> None:
        """Store historical compliance data for trend analysis."""
        history_file = self.output_dir / "compliance_history.json"

        # Load existing history
        history = []
        if history_file.exists():
            try:
                with open(history_file, "r") as f:
                    history = json.load(f)
            except (json.JSONDecodeError, IOError):
                history = []

        # Add current metrics
        history_entry = {
            "timestamp": metrics["timestamp"],
            "compliance_percentage": metrics["tool_compliance_percentage"],
            "total_files": metrics["total_files_analyzed"],
            "flake8_violations": metrics["flake8_violations"],
            "overall_status": metrics["overall_status"],
        }

        history.append(history_entry)

        # Keep only last 100 entries
        history = history[-100:]

        # Save updated history
        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)

        print(f"Historical data updated: {history_file}")

    def generate_reports(self, formats: List[str] = None) -> Dict[str, Path]:
        """Generate quality reports in specified formats."""
        if formats is None:
            formats = ["json", "html"]

        print(f"Analyzing {len(self.python_files)} Python files...")

        # Run all quality checks
        results = {}

        if self.python_files:
            results["black"] = self.run_black_check()
            results["flake8"] = self.run_flake8_check()
            results["isort"] = self.run_isort_check()
        else:
            print("No Python files found to analyze.")
            return {}

        # Calculate metrics
        metrics = self.calculate_compliance_metrics(results)

        # Store historical data
        self.store_historical_data(metrics)

        # Generate reports
        generated_files = {}

        if "json" in formats:
            generated_files["json"] = self.generate_json_report(
                results, metrics
            )

        if "html" in formats:
            generated_files["html"] = self.generate_html_report(
                results, metrics
            )

        # Print summary
        print("\n=== Quality Report Summary ===")
        print(f"Overall Status: {metrics['overall_status']}")
        print(f"Tool Compliance: {metrics['tool_compliance_percentage']}%")
        print(f"Files Analyzed: {metrics['total_files_analyzed']}")
        print(f"Flake8 Violations: {metrics['flake8_violations']}")

        return generated_files


def main():
    """Main entry point for the quality reporter."""
    parser = argparse.ArgumentParser(
        description="Generate code quality reports for AWS DRS Orchestration project"
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Directory to store generated reports (default: reports)",
    )
    parser.add_argument(
        "--format",
        default="json,html",
        help="Report formats to generate: json, html, or both (default: json,html)",
    )

    args = parser.parse_args()

    # Parse formats
    formats = [f.strip().lower() for f in args.format.split(",")]
    valid_formats = ["json", "html"]
    formats = [f for f in formats if f in valid_formats]

    if not formats:
        print(
            "Error: No valid formats specified. Use 'json', 'html', or 'json,html'"
        )
        sys.exit(1)

    # Generate reports
    try:
        reporter = QualityReporter(args.output_dir)
        generated_files = reporter.generate_reports(formats)

        if generated_files:
            print("\n=== Generated Reports ===")
            for format_type, file_path in generated_files.items():
                print(f"{format_type.upper()}: {file_path}")
        else:
            print("No reports generated.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nReport generation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error generating reports: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
