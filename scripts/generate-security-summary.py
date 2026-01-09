#!/usr/bin/env python3
"""
Generate security scan summary from tool outputs
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

def load_json_report(filepath):
    """Load JSON report if it exists"""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return None
    return None

def count_bandit_issues(bandit_report):
    """Count Bandit issues by severity"""
    if not bandit_report or 'results' not in bandit_report:
        return {'high': 0, 'medium': 0, 'low': 0, 'total': 0}
    
    counts = {'high': 0, 'medium': 0, 'low': 0}
    
    for result in bandit_report['results']:
        severity = result.get('issue_severity', '').lower()
        if severity in counts:
            counts[severity] += 1
    
    counts['total'] = sum(counts.values())
    return counts

def count_semgrep_issues(semgrep_report):
    """Count Semgrep issues by severity"""
    if not semgrep_report or 'results' not in semgrep_report:
        return {'error': 0, 'warning': 0, 'info': 0, 'total': 0}
    
    counts = {'error': 0, 'warning': 0, 'info': 0}
    
    for result in semgrep_report['results']:
        severity = result.get('extra', {}).get('severity', '').lower()
        if severity in counts:
            counts[severity] += 1
    
    counts['total'] = sum(counts.values())
    return counts

def count_safety_issues(safety_report):
    """Count Safety dependency vulnerabilities"""
    if not safety_report:
        return 0
    
    if isinstance(safety_report, list):
        return len(safety_report)
    elif isinstance(safety_report, dict) and 'vulnerabilities' in safety_report:
        return len(safety_report['vulnerabilities'])
    
    return 0

def count_npm_vulnerabilities(npm_audit):
    """Count NPM audit vulnerabilities"""
    if not npm_audit:
        return {'critical': 0, 'high': 0, 'moderate': 0, 'low': 0, 'total': 0}
    
    if 'auditReportVersion' in npm_audit and 'vulnerabilities' in npm_audit:
        # npm audit v2 format
        vulns = npm_audit.get('vulnerabilities', {})
        counts = {'critical': 0, 'high': 0, 'moderate': 0, 'low': 0}
        
        for vuln_name, vuln_data in vulns.items():
            severity = vuln_data.get('severity', '').lower()
            if severity in counts:
                counts[severity] += 1
        
        counts['total'] = sum(counts.values())
        return counts
    
    # npm audit v1 format or metadata format
    metadata = npm_audit.get('metadata', {})
    if 'vulnerabilities' in metadata:
        vulns = metadata['vulnerabilities']
        return {
            'critical': vulns.get('critical', 0),
            'high': vulns.get('high', 0),
            'moderate': vulns.get('moderate', 0),
            'low': vulns.get('low', 0),
            'total': vulns.get('total', 0)
        }
    
    return {'critical': 0, 'high': 0, 'moderate': 0, 'low': 0, 'total': 0}

def generate_summary():
    """Generate security summary from all scan results"""
    reports_dir = Path("reports/security/raw")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Load all reports
    bandit_report = load_json_report(reports_dir / "bandit-report.json")
    semgrep_python = load_json_report(reports_dir / "semgrep-python.json")
    semgrep_cfn = load_json_report(reports_dir / "semgrep-cfn.json")
    safety_report = load_json_report(reports_dir / "safety-report.json")
    npm_audit = load_json_report(reports_dir / "npm-audit.json")
    cfn_lint = load_json_report(reports_dir / "cfn-lint.json")
    
    # Count issues
    bandit_counts = count_bandit_issues(bandit_report)
    semgrep_python_counts = count_semgrep_issues(semgrep_python)
    semgrep_cfn_counts = count_semgrep_issues(semgrep_cfn)
    safety_count = count_safety_issues(safety_report)
    npm_counts = count_npm_vulnerabilities(npm_audit)
    cfn_lint_count = len(cfn_lint) if cfn_lint and isinstance(cfn_lint, list) else 0
    
    summary = {
        "scan_date": datetime.now().isoformat(),
        "project": "aws-drs-orchestrator-fresh",
        "results": {
            "python_security": {
                "bandit": bandit_counts,
                "semgrep_findings": semgrep_python_counts,
                "vulnerable_dependencies": safety_count
            },
            "frontend_security": {
                "npm_vulnerabilities": npm_counts
            },
            "infrastructure_security": {
                "cfn_lint_issues": cfn_lint_count,
                "semgrep_findings": semgrep_cfn_counts
            }
        },
        "summary": {
            "total_critical_issues": (
                bandit_counts['high'] + 
                semgrep_python_counts['error'] + 
                semgrep_cfn_counts['error'] +
                npm_counts['critical']
            ),
            "total_high_issues": (
                bandit_counts['medium'] + 
                semgrep_python_counts['warning'] +
                semgrep_cfn_counts['warning'] +
                npm_counts['high'] +
                safety_count
            ),
            "total_issues": (
                bandit_counts['total'] + 
                semgrep_python_counts['total'] +
                semgrep_cfn_counts['total'] +
                npm_counts['total'] +
                safety_count +
                cfn_lint_count
            )
        }
    }
    
    # Write summary
    summary_dir = Path("reports/security")
    summary_dir.mkdir(parents=True, exist_ok=True)
    with open(summary_dir / "security-summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print("\n🔍 SECURITY SCAN SUMMARY")
    print("=" * 50)
    print(f"Scan Date: {summary['scan_date']}")
    print(f"Project: {summary['project']}")
    print()
    
    print("📋 Python Security:")
    print(f"  Bandit Issues: {bandit_counts['total']} (High: {bandit_counts['high']}, Medium: {bandit_counts['medium']}, Low: {bandit_counts['low']})")
    print(f"  Semgrep Findings: {semgrep_python_counts['total']} (Error: {semgrep_python_counts['error']}, Warning: {semgrep_python_counts['warning']})")
    print(f"  Vulnerable Dependencies: {safety_count}")
    
    print("\n🌐 Frontend Security:")
    print(f"  NPM Vulnerabilities: {npm_counts['total']} (Critical: {npm_counts['critical']}, High: {npm_counts['high']}, Moderate: {npm_counts['moderate']})")
    
    print("\n☁️ Infrastructure Security:")
    print(f"  CloudFormation Issues: {cfn_lint_count}")
    print(f"  Semgrep Findings: {semgrep_cfn_counts['total']} (Error: {semgrep_cfn_counts['error']}, Warning: {semgrep_cfn_counts['warning']})")
    
    print("\n📊 OVERALL SUMMARY:")
    print(f"  Critical Issues: {summary['summary']['total_critical_issues']}")
    print(f"  High Issues: {summary['summary']['total_high_issues']}")
    print(f"  Total Issues: {summary['summary']['total_issues']}")
    
    # Determine if scan passed based on security thresholds
    critical_issues = summary['summary']['total_critical_issues']
    high_issues = summary['summary']['total_high_issues']
    total_issues = summary['summary']['total_issues']
    
    # Security thresholds (configurable)
    CRITICAL_THRESHOLD = int(os.environ.get('SECURITY_THRESHOLD_CRITICAL', '0'))
    HIGH_THRESHOLD = int(os.environ.get('SECURITY_THRESHOLD_HIGH', '10'))
    TOTAL_THRESHOLD = int(os.environ.get('SECURITY_THRESHOLD_TOTAL', '50'))
    
    if critical_issues > CRITICAL_THRESHOLD:
        print(f"\n❌ SECURITY SCAN FAILED: {critical_issues} critical issues found (threshold: {CRITICAL_THRESHOLD})")
        print("   Action Required: Fix all critical issues before deployment")
        print("   Critical issues block deployment and must be resolved immediately")
        return 1
    elif high_issues > HIGH_THRESHOLD:
        print(f"\n⚠️ SECURITY SCAN WARNING: {high_issues} high-severity issues found (threshold: {HIGH_THRESHOLD})")
        print("   Recommendation: Review and fix high-severity issues")
        print("   High-severity issues should be addressed within 24-48 hours")
        return 0  # Don't fail build, but warn
    elif total_issues > TOTAL_THRESHOLD:
        print(f"\n⚠️ SECURITY SCAN INFO: {total_issues} total issues found (threshold: {TOTAL_THRESHOLD})")
        print("   Recommendation: Consider addressing medium/low severity issues")
        return 0
    else:
        print("\n✅ SECURITY SCAN PASSED: Security posture is acceptable")
        if total_issues > 0:
            print(f"   Note: {total_issues} low-severity issues found - consider addressing during maintenance")
        return 0

if __name__ == "__main__":
    try:
        exit_code = generate_summary()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ ERROR: Security summary generation failed: {e}")
        print("Check that security scan reports exist in reports/security/raw/")
        sys.exit(1)