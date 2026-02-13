# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 3.0.x   | :white_check_mark: |
| 2.x.x   | :x:                |
| < 2.0   | :x:                |

## Security Standards

This project follows AWS security best practices and implements multiple layers of security controls:

### Authentication & Authorization
- **Cognito JWT Authentication**: All API endpoints require valid JWT tokens
- **Role-Based Access Control (RBAC)**: 5 distinct roles with granular permissions
- **Principle of Least Privilege**: Users receive minimum required permissions

### Data Protection
- **Encryption in Transit**: All API communications use HTTPS/TLS 1.2+
- **Encryption at Rest**: DynamoDB tables use AWS managed encryption
- **Input Validation**: All user inputs are validated and sanitized
- **Output Encoding**: All responses are properly encoded to prevent XSS

### Infrastructure Security
- **IAM Roles**: Lambda functions use least-privilege IAM roles
- **VPC Security**: Optional VPC deployment with security groups
- **CloudTrail Logging**: All API calls are logged for audit purposes
- **WAF Protection**: API Gateway protected by AWS WAF (optional)

### Code Security
- **Static Analysis**: Bandit, Semgrep, and ESLint security scans
- **Dependency Scanning**: Safety and npm audit for vulnerability detection
- **Code Quality**: Automated linting and formatting with security rules
- **Secret Management**: No hardcoded secrets, uses AWS Secrets Manager

## Security Scanning

### Automated Scans
The project includes automated security scanning in CI/CD:

```bash
# Python security scans
bandit -r lambda/ -ll
semgrep --config=auto lambda/
safety scan

# Frontend security scans
npm audit --audit-level moderate
eslint src/ --ext .ts,.tsx

# Infrastructure security scans
cfn-lint cfn/*.yaml
```

### Manual Security Testing
Run comprehensive security tests locally:

```bash
# Install security tools
pip install bandit semgrep safety
npm install -g eslint-plugin-security

# Run all security scans
make security-scan
```

## Vulnerability Response

### Severity Levels
- **Critical (CVSS 9.0-10.0)**: Fix within 24-48 hours
- **High (CVSS 7.0-8.9)**: Fix within 7 days
- **Medium (CVSS 4.0-6.9)**: Fix within 30 days
- **Low (CVSS 0.1-3.9)**: Fix in next release cycle

### Response Process
1. **Assessment**: Evaluate impact and exploitability
2. **Containment**: Implement temporary mitigations if needed
3. **Fix Development**: Create and test security patches
4. **Deployment**: Deploy fixes following change management
5. **Verification**: Confirm vulnerability is resolved
6. **Documentation**: Update security documentation

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

### Preferred Method: GitHub Security Advisories
1. Go to the [Security tab](https://github.com/johnjcousens/hrp-drs-tech-adapter/security/advisories)
2. Click "Report a vulnerability"
3. Provide detailed information about the vulnerability
4. Allow reasonable time for investigation and remediation

### Alternative: Private Disclosure
1. **Do not** create public GitHub issues for security vulnerabilities
2. Contact the maintainers privately via GitHub
3. Include detailed information about the vulnerability
4. Allow reasonable time for investigation and remediation

### What to Include
- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Suggested remediation (if known)
- Your contact information for follow-up

## Security Controls Implementation

### Current Status (v3.0.1)
- ✅ Authentication & Authorization (Cognito + RBAC)
- ✅ Input Validation & Output Encoding
- ✅ Secure Communication (HTTPS/TLS)
- ✅ Infrastructure Security (IAM, CloudTrail)
- ✅ Automated Security Scanning (CI/CD pipeline)
- ✅ Dependency Vulnerability Scanning (Safety, npm audit)
- ✅ Static Code Analysis (Bandit, Semgrep, ESLint)
- ✅ Infrastructure Security Scanning (cfn-lint)

### Planned Enhancements
- [ ] AWS WAF integration for API protection
- [ ] Enhanced logging and monitoring
- [ ] Secrets Manager integration
- [ ] VPC deployment option
- [ ] Rate limiting and DDoS protection
- [ ] Security headers implementation

## Compliance

### Standards Alignment
- **AWS Well-Architected Security Pillar**
- **NIST Cybersecurity Framework**
- **ISO 27001 Security Controls**
- **SOC 2 Type II Requirements**

### Audit Trail
- All API calls logged to CloudTrail
- User actions tracked in application logs
- Security events monitored and alerted
- Regular security assessments conducted

## Security Training

### Developer Requirements
- AWS Security training completion
- Secure coding practices certification
- Regular security awareness updates
- Incident response training

### Security Resources
- [AWS Security Best Practices](https://aws.amazon.com/security/security-resources/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [AWS Well-Architected Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/)

## Contact Information

- **Security Issues**: Use [GitHub Security Advisories](https://github.com/johnjcousens/hrp-drs-tech-adapter/security/advisories)
- **General Issues**: [GitHub Issues](https://github.com/johnjcousens/hrp-drs-tech-adapter/issues)
- **Project Repository**: [github.com/johnjcousens/hrp-drs-tech-adapter](https://github.com/johnjcousens/hrp-drs-tech-adapter)

## Acknowledgments

We appreciate the security research community's efforts in responsibly disclosing vulnerabilities. Contributors who report valid security issues will be acknowledged in our security advisories (with permission).

---

**Last Updated**: January 15, 2026
**Next Review**: April 15, 2026