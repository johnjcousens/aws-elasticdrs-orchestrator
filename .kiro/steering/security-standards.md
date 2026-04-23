---
inclusion: always
---
# Security Standards

Consolidated security requirements for the AWS DRS Orchestration platform. Covers general secure coding principles, ProServe guidelines, and DRS-specific controls.

## General Secure Coding Principles

### Authentication & Authorization

- Implement authentication by default using established frameworks
- Never create custom authentication schemes
- Implement proper session management with secure cookie settings (secure flag, httpOnly)
- Use multi-factor authentication where applicable

### Input Validation

- Never trust user input
- Implement input validation and sanitization
- Use parameterized queries for database operations
- Validate file uploads and restrict file types
- Implement rate limiting for APIs

### Data Protection

- Encrypt sensitive data at rest and in transit
- Use strong encryption algorithms and proper key management
- Never store secrets in code or configuration files
- Use secure communication protocols (HTTPS/TLS)

### Error Handling & Logging

- Don't expose sensitive information in error messages
- Log security-relevant events
- Implement proper log retention policies
- Monitor for suspicious activities

### Dependencies & Libraries

- Keep dependencies updated and use vulnerability scanning tools
- Minimize third-party dependencies
- Choose libraries with active maintenance
- Review security advisories regularly

## ProServe-Specific Guidelines

### AWS Authentication

- Use AWS native authentication mechanisms (Cognito, API Gateway)
- Use Lambda authorizers for API endpoints
- Use AWS Lambda Powertools for event validation
- Implement OWASP top 10 protections

### IAM & Access Control

- Never use root accounts or IAM users directly
- Implement least privilege principle for all roles
- Use IAM roles instead of individual user permissions
- Rotate access keys regularly
- Use permissions boundaries for Lambda execution roles

### Secrets Management

- Use AWS Secrets Manager for sensitive data
- Use Parameter Store for configuration data
- Never expose secrets in logs or environment variables
- Implement proper secret rotation mechanisms

### Encryption

- Enable encryption at rest by default
- Use AWS KMS for encryption
- Implement TLS for all endpoints

### Infrastructure as Code

- Use nested stacks for complex deployments
- Implement stack policies for critical resources
- Never hardcode credentials
- Use parameter constraints and NoEcho for sensitive parameters

### Security Testing

- Implement security testing in CI/CD pipeline (git-secrets, Bandit, cfn_nag)
- Scan for vulnerabilities regularly
- Implement DDoS protection measures

## DRS-Specific Security Controls

### Priority Levels

- **HIGH**: Critical — must implement
- **MEDIUM**: Important — should implement
- **LOW**: Nice-to-have — consider implementing

### DRS Service Configuration

- HIGH: Dedicated IAM roles for DRS service with least privilege
- HIGH: Replication in private subnets only
- HIGH: Encryption for replicated EBS volumes
- HIGH: Staging area subnets isolated from production
- HIGH: Proper security groups for replication servers
- MEDIUM: VPC endpoints for DRS API calls
- MEDIUM: CloudTrail logging for all DRS API calls
- LOW: Custom KMS keys for EBS encryption

### Cross-Account DR Architecture

- HIGH: IAM roles with trust relationships (no long-term credentials)
- HIGH: STS AssumeRole for cross-account access
- HIGH: Restrict cross-account permissions to specific DRS actions
- MEDIUM: AWS Organizations SCPs for DR accounts

### Recovery Instance Security

- HIGH: Launch recovery instances in private subnets
- HIGH: Hardened AMIs for recovery instances
- HIGH: Security groups configured before recovery launch
- HIGH: IMDSv2 for all recovery instances
- HIGH: Proper IAM instance profiles
- MEDIUM: Systems Manager for post-recovery management

## Infrastructure Security Controls

### Network Security

- HIGH: Lambda functions in VPC when accessing private resources
- HIGH: VPC endpoints for AWS service access (DynamoDB, S3, Secrets Manager)
- HIGH: Security groups with minimal required access
- HIGH: No 0.0.0.0/0 inbound access on any security group
- HIGH: VPC Flow Logs for network monitoring

### Data Storage

- HIGH: Encryption at rest for all data stores (DynamoDB, S3)
- HIGH: Encryption in transit (TLS 1.2+) for all communications
- HIGH: S3 bucket policies blocking public access (BlockPublicAccess.BLOCK_ALL)
- HIGH: S3 versioning enabled
- HIGH: DynamoDB point-in-time recovery enabled

### Logging & Monitoring

- HIGH: CloudWatch Logs for all Lambda functions
- HIGH: API Gateway access logging
- HIGH: X-Ray tracing for distributed tracing
- HIGH: CloudWatch alarms for error rates and latency
- HIGH: CloudTrail for API audit logging
- MEDIUM: Structured logging (JSON format)
- MEDIUM: Log retention minimum 90 days

### Compute Services

- HIGH: Lambda — proper error handling, Secrets Manager for sensitive env vars, least privilege execution roles
- HIGH: Step Functions — Standard Workflows for long-running DR operations, Catch blocks for error handling
- HIGH: API Gateway — request validation, Cognito authorizers, HTTPS only, throttling

### Frontend Services

- HIGH: CloudFront — HTTPS only with TLS 1.2+, security headers (CSP, HSTS, X-Frame-Options), OAI for S3
- HIGH: Cognito — MFA enabled, strong password policies, short-lived access tokens

## Implementation Checklist

### Before Deployment

- [ ] All IAM roles follow least privilege principle
- [ ] All data stores have encryption enabled
- [ ] All network access restricted to required paths
- [ ] All secrets stored in Secrets Manager
- [ ] All logging enabled and configured
- [ ] Security groups have no 0.0.0.0/0 inbound rules

### After Deployment

- [ ] CloudTrail capturing all API calls
- [ ] CloudWatch alarms configured
- [ ] Authentication and authorization flows tested
- [ ] Encryption verified (check KMS key usage)
- [ ] VPC Flow Logs reviewed for unexpected traffic
- [ ] Security scan passed (cfn_nag, Bandit)
