#!/usr/bin/env python3
"""
Security Threshold Checker for AWS DRS Orchestration
Checks security scan results against defined thresholds
"""

import json
import os
import sys


def main():
    """Check security scan results against thresholds."""
    if not os.path.exists("reports/security/security-summary.json"):
        print("ERROR: Security summary not generated!")
        sys.exit(1)

    # Load security summary
    with open("reports/security/security-summary.json", "r") as f:
        data = json.load(f)

    # Extract counts
    critical = data["summary"]["total_critical_issues"]
    high = data["summary"]["total_high_issues"]
    total = data["summary"]["total_issues"]

    # Get thresholds from environment
    critical_threshold = int(
        os.environ.get("SECURITY_THRESHOLD_CRITICAL", "0")
    )
    high_threshold = int(os.environ.get("SECURITY_THRESHOLD_HIGH", "10"))
    total_threshold = int(os.environ.get("SECURITY_THRESHOLD_TOTAL", "50"))

    # Display results
    print(f"Security scan results:")
    print(f"  Critical issues: {critical} (threshold: {critical_threshold})")
    print(f"  High issues: {high} (threshold: {high_threshold})")
    print(f"  Total issues: {total} (threshold: {total_threshold})")

    # Check thresholds and exit appropriately
    if critical > critical_threshold:
        print("❌ SECURITY SCAN FAILED: Critical security issues found!")
        print("Build will fail due to critical security vulnerabilities.")
        sys.exit(1)
    elif high > high_threshold:
        print("⚠️ SECURITY SCAN WARNING: High-severity issues found!")
        print("Consider addressing these issues before deployment.")
    elif total > total_threshold:
        print("ℹ️ SECURITY SCAN INFO: Many security issues found.")
        print("Consider addressing medium/low severity issues.")
    else:
        print("✅ SECURITY SCAN PASSED: Security posture is acceptable.")


if __name__ == "__main__":
    main()
