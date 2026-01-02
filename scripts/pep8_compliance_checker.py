#!/usr/bin/env python3
"""
Comprehensive PEP 8 Compliance Checker for AWS DRS Orchestration

This script performs complete PEP 8 compliance validation based on our
comprehensive Python coding standards steering document. It checks:
- Code formatting (Black)
- Import sorting (isort) 
- PEP 8 violations (Flake8)
- Naming conventions
- Programming recommendations
- Documentation standards

Usage:
    python scripts/pep8_compliance_checker.py [--fix] [--report]
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class PEP8ComplianceChecker:
    """Comprehensive PEP 8 compliance checker and fixer."""

    def __init__(self):
        """Initialize the compliance checker."""
        self.python_files = self._discover_python_files()
        self.results = {}
        self.timestamp = datetime.now()

    def _discover_python_files(self) -> List[Path]:
        """Discover all Python files in the project."""
        python_files = []
        
        # Core directories to check
        directories = ["lambda", "scripts", "tests"]
        
        for directory in directories:
            dir_path = Path(directory)
            if dir_path.exists():
                python_files.extend(dir_path.rglob("*.py"))
        
        # Root level Python files
        python_files.extend(Path(".").glob("*.py"))
        
        return [f for f in python_files if f.is_file()]

    def check_black_formatting(self) -> Dict:
        """Check Black code formatting compliance."""
        print("🎨 Checking Black formatting compliance...")
        
        try:
            result = subprocess.run(
                [
                    "python", "-m", "black", 
                    "--check", "--diff", "--line-length=79"
                ] + [str(f) for f in self.python_files],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return {
                "tool": "black",
                "compliant": result.returncode == 0,
                "files_checked": len(self.python_files),
                "output": result.stdout,
                "errors": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "tool": "black",
                "compliant": False,
                "error": "Black check timed out"
            }
        except Exception as e:
            return {
                "tool": "black", 
                "compliant": False,
                "error": str(e)
            }

    def check_isort_imports(self) -> Dict:
        """Check isort import sorting compliance."""
        print("📦 Checking import sorting compliance...")
        
        try:
            result = subprocess.run(
                [
                    "python", "-m", "isort",
                    "--check-only", "--diff", 
                    "--profile=black", "--line-length=79"
                ] + [str(f) for f in self.python_files],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return {
                "tool": "isort",
                "compliant": result.returncode == 0,
                "files_checked": len(self.python_files),
                "output": result.stdout,
                "errors": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "tool": "isort",
                "compliant": False,
                "error": "isort check timed out"
            }
        except Exception as e:
            return {
                "tool": "isort",
                "compliant": False,
                "error": str(e)
            }

    def check_flake8_violations(self) -> Dict:
        """Check Flake8 PEP 8 violations."""
        print("🔍 Checking PEP 8 violations with Flake8...")
        
        try:
            result = subprocess.run(
                [
                    "python", "-m", "flake8",
                    "--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s",
                    "--statistics", "--count"
                ] + [str(f) for f in self.python_files],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            violations = []
            violation_counts = {}
            
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if ':' in line and ' ' in line:
                        # Parse violation line
                        parts = line.split(':', 3)
                        if len(parts) >= 4:
                            code_msg = parts[3].strip()
                            if ' ' in code_msg:
                                code = code_msg.split(' ', 1)[0]
                                message = code_msg.split(' ', 1)[1]
                                
                                violations.append({
                                    "file": parts[0],
                                    "line": int(parts[1]) if parts[1].isdigit() else 0,
                                    "column": int(parts[2]) if parts[2].isdigit() else 0,
                                    "code": code,
                                    "message": message,
                                    "severity": self._get_violation_severity(code)
                                })
                                
                                violation_counts[code] = violation_counts.get(code, 0) + 1
            
            return {
                "tool": "flake8",
                "compliant": result.returncode == 0,
                "files_checked": len(self.python_files),
                "total_violations": len(violations),
                "violations": violations,
                "violation_counts": violation_counts,
                "output": result.stdout,
                "errors": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "tool": "flake8",
                "compliant": False,
                "error": "Flake8 check timed out"
            }
        except Exception as e:
            return {
                "tool": "flake8",
                "compliant": False,
                "error": str(e)
            }

    def _get_violation_severity(self, code: str) -> str:
        """Get severity level for violation code."""
        critical_codes = ["F821", "F822", "F823", "F831", "E999", "E902"]
        high_codes = ["F401", "F841", "E722", "E702", "F811", "F812", 
                     "N801", "N802", "N803", "N806"]
        medium_codes = ["C901", "E713", "W504", "E711", "E712", 
                       "N804", "N805", "N815"]
        
        if code in critical_codes:
            return "critical"
        elif code in high_codes:
            return "high"
        elif code in medium_codes:
            return "medium"
        else:
            return "low"

    def fix_formatting_issues(self) -> Dict:
        """Fix formatting issues with Black and isort."""
        print("🔧 Fixing formatting issues...")
        
        results = {}
        
        # Fix with Black
        try:
            black_result = subprocess.run(
                [
                    "python", "-m", "black",
                    "--line-length=79"
                ] + [str(f) for f in self.python_files],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            results["black_fix"] = {
                "success": black_result.returncode == 0,
                "output": black_result.stdout,
                "errors": black_result.stderr
            }
            
        except Exception as e:
            results["black_fix"] = {
                "success": False,
                "error": str(e)
            }
        
        # Fix with isort
        try:
            isort_result = subprocess.run(
                [
                    "python", "-m", "isort",
                    "--profile=black", "--line-length=79"
                ] + [str(f) for f in self.python_files],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            results["isort_fix"] = {
                "success": isort_result.returncode == 0,
                "output": isort_result.stdout,
                "errors": isort_result.stderr
            }
            
        except Exception as e:
            results["isort_fix"] = {
                "success": False,
                "error": str(e)
            }
        
        return results

    def generate_compliance_report(self) -> Dict:
        """Generate comprehensive compliance report."""
        print("📊 Generating compliance report...")
        
        # Run all checks
        self.results["black"] = self.check_black_formatting()
        self.results["isort"] = self.check_isort_imports()
        self.results["flake8"] = self.check_flake8_violations()
        
        # Calculate overall compliance
        tools_compliant = sum(
            1 for result in self.results.values() 
            if result.get("compliant", False)
        )
        total_tools = len(self.results)
        compliance_percentage = (tools_compliant / total_tools * 100) if total_tools > 0 else 0
        
        # Categorize violations by severity
        flake8_result = self.results.get("flake8", {})
        violations = flake8_result.get("violations", [])
        
        severity_counts = {
            "critical": len([v for v in violations if v.get("severity") == "critical"]),
            "high": len([v for v in violations if v.get("severity") == "high"]),
            "medium": len([v for v in violations if v.get("severity") == "medium"]),
            "low": len([v for v in violations if v.get("severity") == "low"])
        }
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        report = {
            "metadata": {
                "timestamp": self.timestamp.isoformat(),
                "files_analyzed": len(self.python_files),
                "tools_run": total_tools,
                "steering_document_version": "v1.2.2+"
            },
            "compliance_summary": {
                "overall_compliant": tools_compliant == total_tools,
                "compliance_percentage": round(compliance_percentage, 2),
                "tools_compliant": tools_compliant,
                "total_tools": total_tools
            },
            "tool_results": self.results,
            "violation_analysis": {
                "total_violations": len(violations),
                "by_severity": severity_counts,
                "violation_counts": flake8_result.get("violation_counts", {})
            },
            "recommendations": recommendations,
            "files_analyzed": [str(f) for f in self.python_files]
        }
        
        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate specific recommendations based on results."""
        recommendations = []
        
        # Black formatting recommendations
        if not self.results.get("black", {}).get("compliant", True):
            recommendations.append(
                "Run 'python -m black --line-length=79 lambda/ scripts/' to fix formatting issues"
            )
        
        # isort recommendations
        if not self.results.get("isort", {}).get("compliant", True):
            recommendations.append(
                "Run 'python -m isort --profile=black --line-length=79 lambda/ scripts/' to fix import sorting"
            )
        
        # Flake8 recommendations
        flake8_result = self.results.get("flake8", {})
        violations = flake8_result.get("violations", [])
        violation_counts = flake8_result.get("violation_counts", {})
        
        if violations:
            # Critical violations
            critical_violations = [v for v in violations if v.get("severity") == "critical"]
            if critical_violations:
                recommendations.append(
                    f"URGENT: Fix {len(critical_violations)} critical violations (undefined names, syntax errors)"
                )
            
            # High-frequency violations
            for code, count in violation_counts.items():
                if count >= 10:
                    if code == "F401":
                        recommendations.append(
                            f"Remove {count} unused imports - consider using autoflake"
                        )
                    elif code in ["E231", "E221", "E222"]:
                        recommendations.append(
                            f"Fix {count} whitespace issues - run Black formatter"
                        )
                    elif code == "C901":
                        recommendations.append(
                            f"Refactor {count} complex functions to reduce complexity"
                        )
        
        # General recommendations
        if not recommendations:
            recommendations.append("✅ Code is PEP 8 compliant! Maintain quality with pre-commit hooks")
        else:
            recommendations.append(
                "Consider setting up pre-commit hooks to prevent future violations"
            )
        
        return recommendations

    def save_report(self, report: Dict, filename: str = None) -> Path:
        """Save compliance report to JSON file."""
        if filename is None:
            filename = f"pep8_compliance_report_{self.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        report_file = reports_dir / filename
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Compliance report saved: {report_file}")
        return report_file

    def print_summary(self, report: Dict) -> None:
        """Print compliance summary to console."""
        print("\n" + "=" * 70)
        print("PEP 8 COMPLIANCE REPORT - AWS DRS ORCHESTRATION")
        print("=" * 70)
        
        summary = report["compliance_summary"]
        violation_analysis = report["violation_analysis"]
        
        # Overall status
        status = "✅ COMPLIANT" if summary["overall_compliant"] else "❌ NON-COMPLIANT"
        print(f"\nOverall Status: {status}")
        print(f"Compliance Percentage: {summary['compliance_percentage']}%")
        print(f"Files Analyzed: {report['metadata']['files_analyzed']}")
        
        # Tool results
        print(f"\nTool Results:")
        for tool_name, result in report["tool_results"].items():
            compliant = result.get("compliant", False)
            status_icon = "✅" if compliant else "❌"
            print(f"  {status_icon} {tool_name.title()}: {'PASS' if compliant else 'FAIL'}")
        
        # Violation breakdown
        if violation_analysis["total_violations"] > 0:
            print(f"\nViolation Breakdown:")
            print(f"  Total Violations: {violation_analysis['total_violations']}")
            
            severity_counts = violation_analysis["by_severity"]
            for severity, count in severity_counts.items():
                if count > 0:
                    print(f"  {severity.title()}: {count}")
            
            # Top violation types
            violation_counts = violation_analysis["violation_counts"]
            if violation_counts:
                print(f"\nTop Violation Types:")
                sorted_violations = sorted(violation_counts.items(), key=lambda x: x[1], reverse=True)
                for code, count in sorted_violations[:5]:
                    print(f"  {code}: {count}")
        
        # Recommendations
        print(f"\nRecommendations:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"  {i}. {rec}")
        
        print("\n" + "=" * 70)


def main():
    """Main entry point for PEP 8 compliance checker."""
    parser = argparse.ArgumentParser(
        description="Comprehensive PEP 8 compliance checker for AWS DRS Orchestration"
    )
    parser.add_argument(
        "--fix", 
        action="store_true",
        help="Automatically fix formatting issues with Black and isort"
    )
    parser.add_argument(
        "--report",
        action="store_true", 
        help="Generate detailed compliance report"
    )
    parser.add_argument(
        "--output",
        help="Output filename for report (default: auto-generated)"
    )
    
    args = parser.parse_args()
    
    try:
        checker = PEP8ComplianceChecker()
        
        if args.fix:
            print("🔧 Fixing formatting issues...")
            fix_results = checker.fix_formatting_issues()
            
            for tool, result in fix_results.items():
                if result.get("success"):
                    print(f"✅ {tool} fixes applied successfully")
                else:
                    print(f"❌ {tool} fixes failed: {result.get('error', 'Unknown error')}")
        
        # Generate compliance report
        report = checker.generate_compliance_report()
        
        # Print summary
        checker.print_summary(report)
        
        # Save detailed report if requested
        if args.report:
            checker.save_report(report, args.output)
        
        # Exit with appropriate code
        if not report["compliance_summary"]["overall_compliant"]:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Compliance check cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during compliance check: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()