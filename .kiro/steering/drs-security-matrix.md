---
inclusion: manual
---

# DRS Security Matrix

Security requirements and controls specific to AWS Elastic Disaster Recovery (DRS) orchestration infrastructure.

## Priority Levels
- **HIGH**: Critical requirements - Must implement
- **MEDIUM**: Important recommendations - Should implement
- **LOW**: Nice-to-have optimizations - Consider implementing

## DRS-Specific Security Controls

### DRS Service Configuration
- HIGH: Use dedicated IAM roles for DRS service with least privilege
- HIGH: Configure replication in private subnets only
- HIGH: Enable encryption for replicated EBS volumes
- HIGH: Use staging area subnets isolated from production
- HIGH: Implement proper security groups for replication servers
- MEDIUM: Configure VPC endpoints for DRS API calls
- MEDIUM: Enable CloudTrail logging for all DRS API calls
- LOW: Implement custom KMS keys for EBS encryption

### Cross-Account DR Architecture
- HIGH: Use IAM roles with trust relationships (no long-term credentials)
- HIGH: Implement STS AssumeRole for cross-account access
- HIGH: Restrict cross-account permissions to specific DRS actions
- HIGH: Use resource-based policies where applicable
- MEDIUM: Implement AWS Organizations SCPs for DR accounts
- LOW: Use AWS RAM for sharing resources across accounts

### Recovery Instance Security
- HIGH: Launch recovery instances in private subnets
- HIGH: Apply hardened AMIs for recovery instances
- HIGH: Configure security groups before recovery launch
- HIGH: Use IMDSv2 for all recovery instances
- HIGH: Implement proper IAM instance profiles
- MEDIUM: Configure Systems Manager for post-recovery management
- LOW: Implement AWS Inspector for vulnerability scanning

## General Infrastructure Security

### IAM & Access Control
- HIGH: Implement principle of least privilege for all IAM roles
- HIGH: Use service roles appropriately (Lambda, API Gateway, Step Functions)
- HIGH: Implement resource policies for cross-service access
- HIGH: Document any use of wildcard permissions with justification
- HIGH: Use permissions boundaries for Lambda execution roles
- MEDIUM: Implement ABAC (Attribute-Based Access Control) where appropriate
- LOW: Use custom policies instead of AWS managed policies

### Network Security
- HIGH: Deploy Lambda functions in VPC when accessing private resources
- HIGH: Use VPC endpoints for AWS service access (DynamoDB, S3, Secrets Manager)
- HIGH: Implement security groups with minimal required access
- HIGH: No 0.0.0.0/0 inbound access on any security group
- HIGH: Enable VPC Flow Logs for network monitoring
- MEDIUM: Use AWS PrivateLink for cross-VPC communication
- LOW: Implement Network Firewall for advanced traffic inspection

### Data Protection
- HIGH: Enable encryption at rest for all data stores (DynamoDB, S3)
- HIGH: Enable encryption in transit (TLS 1.2+) for all communications
- HIGH: Use Secrets Manager for sensitive configuration (API keys, credentials)
- HIGH: Implement S3 bucket policies blocking public access
- HIGH: Enable S3 versioning for audit trail
- MEDIUM: Use customer-managed KMS keys for sensitive data
- LOW: Implement S3 Object Lock for compliance requirements

### Logging & Monitoring
- HIGH: Enable CloudWatch Logs for all Lambda functions
- HIGH: Enable API Gateway access logging
- HIGH: Enable X-Ray tracing for distributed tracing
- HIGH: Configure CloudWatch alarms for error rates and latency
- HIGH: Enable CloudTrail for API audit logging
- MEDIUM: Implement structured logging (JSON format)
- MEDIUM: Configure log retention policies (minimum 90 days)
- LOW: Implement CloudWatch Logs Insights queries for analysis

### Secrets Management
- HIGH: Use Secrets Manager for database credentials and API keys
- HIGH: Never store secrets in environment variables or code
- HIGH: Implement automatic rotation for secrets where possible
- HIGH: Use KMS encryption for secrets
- MEDIUM: Implement secret versioning for rollback capability
- LOW: Use customer-managed KMS keys for secrets encryption

## Compute Services

### Lambda Functions
- HIGH: Implement proper error handling with structured responses
- HIGH: Use Secrets Manager for sensitive environment variables
- HIGH: Configure appropriate timeout (not exceeding 15 minutes)
- HIGH: Configure appropriate memory based on workload
- HIGH: Enable X-Ray tracing for performance monitoring
- HIGH: Implement least privilege IAM execution roles
- MEDIUM: Configure dead-letter queues for async invocations
- MEDIUM: Use Lambda Powertools for observability
- LOW: Implement provisioned concurrency for latency-sensitive functions

### Step Functions
- HIGH: Use Standard Workflows for long-running DR operations
- HIGH: Implement proper error handling with Catch blocks
- HIGH: Configure CloudWatch logging for execution history
- HIGH: Use IAM roles with minimal required permissions
- MEDIUM: Implement retry logic with exponential backoff
- MEDIUM: Use Express Workflows for high-volume, short operations
- LOW: Implement custom metrics for workflow monitoring

## API & Frontend Services

### API Gateway
- HIGH: Enable access logging to CloudWatch
- HIGH: Implement request validation (JSON schema)
- HIGH: Use Cognito authorizers for authentication
- HIGH: Enable HTTPS only (no HTTP)
- HIGH: Configure throttling and rate limiting
- MEDIUM: Implement WAF for public endpoints
- MEDIUM: Use request/response mapping templates
- LOW: Implement API keys for usage tracking

### CloudFront
- HIGH: Enable HTTPS only with TLS 1.2+
- HIGH: Configure security headers (CSP, HSTS, X-Frame-Options)
- HIGH: Use Origin Access Identity for S3 origins
- HIGH: Enable access logging
- HIGH: Configure proper cache behaviors
- MEDIUM: Implement WAF for edge protection
- MEDIUM: Use custom SSL certificate
- LOW: Implement geo-restrictions if required

### Cognito
- HIGH: Enable MFA for user authentication
- HIGH: Configure strong password policies
- HIGH: Implement proper token expiration (short-lived access tokens)
- HIGH: Use secure callback URLs only
- MEDIUM: Enable advanced security features
- MEDIUM: Configure user pool triggers for custom logic
- LOW: Implement custom authentication flows if needed

## Data Storage

### DynamoDB
- HIGH: Enable encryption at rest (AWS managed or CMK)
- HIGH: Enable point-in-time recovery
- HIGH: Implement least privilege IAM policies for table access
- HIGH: Use VPC endpoints for private access
- MEDIUM: Enable DynamoDB Streams for audit/change tracking
- MEDIUM: Implement TTL for temporary data
- LOW: Use DAX for read-heavy workloads

### S3 Buckets
- HIGH: Block public access using BlockPublicAccess.BLOCK_ALL
- HIGH: Enable server access logging
- HIGH: Enable server-side encryption (SSE-S3 minimum)
- HIGH: Enable enforceSSL in bucket policy
- HIGH: Enable versioning
- HIGH: Implement least privilege bucket policies
- MEDIUM: Implement lifecycle policies for cost optimization
- MEDIUM: Use KMS encryption for sensitive data
- LOW: Enable S3 Inventory for large buckets

## Implementation Checklist

### Before Deployment
- [ ] All IAM roles follow least privilege principle
- [ ] All data stores have encryption enabled
- [ ] All network access is restricted to required paths
- [ ] All secrets are stored in Secrets Manager
- [ ] All logging is enabled and configured
- [ ] Security groups have no 0.0.0.0/0 inbound rules

### After Deployment
- [ ] Verify CloudTrail is capturing all API calls
- [ ] Verify CloudWatch alarms are configured
- [ ] Test authentication and authorization flows
- [ ] Verify encryption is working (check KMS key usage)
- [ ] Review VPC Flow Logs for unexpected traffic
- [ ] Run security scan (cfn_nag, Bandit)
