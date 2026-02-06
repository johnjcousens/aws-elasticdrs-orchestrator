---
inclusion: manual
---

# ProServe Secure Coding Guidelines

Reference: AWS ProServe Secure Coding Guidelines

When generating project documentation or code, follow these rules to ensure compliance with AWS ProServe Secure Coding Guidelines:

## Authentication Rules
- Always implement authentication by default
- Use AWS native authentication mechanisms (Cognito, API Gateway)
- Never create custom authentication schemes
- Implement secure session management with proper cookie settings (secure flag, httpOnly)
- Use lambda authorizers for API endpoints

## Input Validation Rules
- Never trust user input
- Implement input validation and sanitization
- Use safe APIs for handling user input
- Implement OWASP top 10 protections
- Use AWS Lambda Powertools for event validation

## IAM and Access Control Rules
- Never use root accounts
- Avoid using IAM users
- Always implement least privilege principle
- Use IAM roles instead of individual user permissions
- Implement MFA where applicable
- Rotate access keys regularly

## Secrets Management Rules
- Never store secrets in code or config files
- Use AWS Secrets Manager for sensitive data
- Use Parameter Store for configuration data
- Never expose secrets in logs or environment variables
- Implement proper secret rotation mechanisms

## Encryption Rules
- Enable encryption at rest by default
- Use AWS KMS for encryption
- Implement TLS for all endpoints
- Ensure secure communication between services

## Logging and Monitoring Rules
- Implement comprehensive logging
- Use CloudWatch for monitoring
- Set up appropriate alerting mechanisms
- Maintain audit trails using CloudTrail
- Implement proper log retention policies

## Code Structure Rules
- Include standard copyright and license headers
- Initialize SDK clients outside handlers
- Implement proper error handling
- Use appropriate logging levels
- Follow language-specific coding standards
- Create modular and reusable code

## Dependencies Management Rules
- Minimize third-party dependencies
- Use vulnerability scanning tools
- Keep dependencies updated
- Use specific versions of libraries
- Choose libraries with active communities

## Infrastructure as Code Rules
- Use nested stacks for complex deployments
- Implement stack policies for critical resources
- Never hardcode credentials
- Use parameter constraints
- Implement proper metadata and documentation
- Use NoEcho for sensitive parameters

## Security Testing Rules
- Implement security testing in CI/CD pipeline
- Use tools like git-secrets
- Scan for vulnerabilities
- Conduct regular security reviews
- Implement DDoS protection measures

These rules should be implemented as validation checks in the code generation process to ensure compliance with AWS ProServe security standards.
