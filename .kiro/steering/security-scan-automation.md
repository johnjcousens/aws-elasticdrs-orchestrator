# Security Scan Automation

## CRITICAL: Automatic Security Scanning Trigger

**ALWAYS perform comprehensive security scanning when the user requests:**
- "security scan"
- "code review" 
- "security review"
- "check security"
- "analyze security"
- "scan for vulnerabilities"
- "security analysis"
- "review this file" (for security-sensitive files)

## Comprehensive Security Scan Protocol

### 1. Full Codebase Security Scan (Default)

When user requests security scanning without specifying files, run ALL security tools:

```bash
# Create reports directory
mkdir -p security-reports

# Python Security Analysis
bandit -r lambda/ scripts/ -ll -f json -o security-reports/bandit-report.json
bandit -r lambda/ scripts/ -ll --format screen > security-reports/bandit-summary.txt

# Dependency Vulnerability Scanning
safety check --json > security-reports/safety-report.json

# Advanced Security Pattern Matching
semgrep --config=python.lang.security lambda/ scripts/ --json --output security-reports/semgrep-report.json --severity ERROR --severity WARNING

# CloudFormation Security Analysis
cfn-lint cfn/*.yaml --format json > security-reports/cfn-lint-report.json

# Generate comprehensive security summary
python scripts/generate-security-summary.py

# Check against security thresholds
python scripts/check-security-thresholds.py
```

### 2. File-Specific Security Analysis

When user asks to review a specific file, analyze that file with appropriate tools:

#### For Python Files (.py)
```bash
# Bandit security scan on specific file
bandit -ll [filename] --format screen

# Check if file imports any dependencies that might have vulnerabilities
grep -n "^import\|^from" [filename] | head -10

# Look for common security patterns
grep -n "password\|secret\|key\|token\|auth" [filename] -i
```

#### For CloudFormation Files (.yaml)
```bash
# CFN-Lint security analysis
cfn-lint [filename] --format screen

# Semgrep security patterns for YAML
semgrep --config=yaml.lang.security [filename] --severity ERROR --severity WARNING
```

#### For TypeScript/React Files (.ts, .tsx)
```bash
# ESLint security rules
npx eslint [filename] --ext .ts,.tsx --format compact

# Check for common frontend security issues
grep -n "innerHTML\|dangerouslySetInnerHTML\|eval\|document.write" [filename] -i
```

### 3. Security Report Analysis

**ALWAYS provide detailed analysis of findings:**

1. **Categorize Issues by Severity**
   - Critical: Immediate action required
   - High: Address before deployment
   - Medium: Address in next sprint
   - Low: Address when convenient

2. **Assess False Positives**
   - Identify security features misidentified as vulnerabilities
   - Explain why certain findings are acceptable
   - Provide context for development-only tools

3. **Provide Remediation Guidance**
   - Specific code fixes for each issue
   - Best practice recommendations
   - Links to security documentation

4. **Generate Security Assessment**
   - Overall security posture rating
   - Compliance with enterprise standards
   - Production readiness assessment

### 4. Trigger Keywords

**Automatically run security scans when user mentions:**
- "security scan"
- "code review"
- "security review" 
- "check security"
- "analyze security"
- "scan for vulnerabilities"
- "security analysis"
- "is this secure"
- "security check"
- "vulnerability scan"
- "security audit"
- "review [filename]" (if filename contains security-sensitive patterns)

### 5. Security-Sensitive File Patterns

**Automatically trigger security analysis for files containing:**
- `security_utils.py`
- `rbac_middleware.py`
- `auth` in filename
- `login` in filename
- `password` in filename
- `token` in filename
- CloudFormation IAM policies
- API Gateway configurations
- Cognito configurations

### 6. Security Report Format

**ALWAYS provide structured security reports:**

```markdown
# Security Analysis Report

**Date**: [Current Date]
**Scope**: [Full Codebase | Specific File]
**Tools Used**: [List of security tools]

## Executive Summary
- Critical Issues: X
- High Severity Issues: X
- Medium Severity Issues: X
- Low Severity Issues: X

## Detailed Findings
[For each finding, provide:]
- **Issue**: Description
- **Severity**: Critical/High/Medium/Low
- **File**: Filename and line number
- **Assessment**: False positive / Legitimate concern
- **Remediation**: Specific fix or explanation

## Security Posture Assessment
- Overall Rating: Excellent/Good/Needs Improvement/Poor
- Production Readiness: Ready/Needs Fixes/Not Ready
- Compliance Status: Compliant/Minor Issues/Major Issues

## Recommendations
[Prioritized list of actions]
```

### 7. Integration with Development Workflow

**After security scanning:**
1. If critical issues found → Recommend immediate fixes before deployment
2. If high issues found → Provide specific remediation steps
3. If only low/medium issues → Note acceptable for deployment with future improvements
4. Always update security documentation if new patterns discovered

### 8. Continuous Security Monitoring

**Remind user of security best practices:**
- Run security scans before major deployments
- Keep security tools updated (show current versions)
- Monitor for new vulnerabilities in dependencies
- Review security findings in GitHub Actions pipeline

## Security Tool Versions (Current)

- **Bandit**: 1.9.2
- **Safety**: 2.3.4  
- **Semgrep**: 1.146.0
- **CFN-Lint**: 0.83.8
- **ESLint**: Latest (via npm)

## Example Usage Patterns

**User**: "Can you do a security scan?"
**Action**: Run full codebase security analysis with all tools

**User**: "Review this file for security issues" 
**Action**: Run file-specific security analysis with appropriate tools

**User**: "Is lambda/shared/security_utils.py secure?"
**Action**: Comprehensive analysis of security_utils.py with detailed assessment

**User**: "Security review before deployment"
**Action**: Full security scan + production readiness assessment

This automation ensures consistent, comprehensive security analysis every time security is mentioned, maintaining the excellent security posture of the AWS DRS Orchestration project.