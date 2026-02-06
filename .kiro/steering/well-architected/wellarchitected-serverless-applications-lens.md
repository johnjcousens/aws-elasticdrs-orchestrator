---
inclusion: manual
---

# AWS Well-Architected Framework - Serverless Applications Lens

## Document Overview

Best practices for designing, deploying, and architecting serverless application workloads in AWS, covering the six pillars: operational excellence, security, reliability, performance efficiency, cost optimization, and sustainability.

## Design Principles

1. **Speedy, simple, singular**: Functions should be concise, short, single-purpose
2. **Think concurrent requests, not total requests**: Design for concurrency model
3. **Share nothing**: Use persistent storage for durable requirements
4. **Assume no hardware affinity**: Use hardware-agnostic code
5. **Orchestrate with state machines, not functions**: Use Step Functions for workflows
6. **Use events to trigger transactions**: Design for asynchronous event behavior
7. **Design for failures and duplicates**: Operations must be idempotent

## Operational Excellence

### Metrics and Alerts
- Understand CloudWatch metrics for every AWS service
- Configure alarms at individual and aggregated levels
- Use Lambda Powertools or CloudWatch EMF for custom metrics
- Focus on: Business metrics, Customer experience, System metrics, Operational metrics

### Logging
- Standardize with structured logging (JSON format)
- Include correlation IDs and pass to downstream systems
- Use appropriate logging levels and sampling

### Distributed Tracing
- Enable AWS X-Ray active tracing
- Use annotations and subsegments for performance statistics
- Implement retries, backoffs, and circuit breakers

### Deployment
- Use infrastructure as code and version control
- Isolate development and production in separate environments
- Use AWS SAM or similar frameworks
- Favor safe deployments (blue/green, canary) over all-at-once

## Security

### API Authentication
- Use AWS_IAM, Cognito user pools, Lambda authorizers, or resource policies
- Avoid API Keys for authorization (use for tracking only)
- Don't pass credentials through query strings or headers

### Access Control
- Follow least-privileged access for Lambda functions
- Create smaller functions with scoped activities
- Avoid sharing IAM roles across multiple Lambda functions

### Data Protection
- Encrypt sensitive data at all layers
- Use AWS Secrets Manager for secrets
- Enable code signing for Lambda

## Reliability

### Throttling and Concurrency
- Enable throttling at API level
- Return appropriate HTTP status codes (429 for throttling)
- Implement concurrency controls for Lambda functions

### Error Handling
- Use dead-letter queues (DLQ) for failed transactions
- Configure Lambda error handling controls
- Use Step Functions to minimize custom try/catch logic
- Handle partial failures in non-atomic operations

## Performance Efficiency

### Lambda Optimization
- Test different memory settings
- Optimize static initialization
- Consider provisioned concurrency for latency-sensitive functions
- Use container reuse and global scope for expensive operations
- Break down monolithic functions into microservices

### Service Selection
- API Gateway: Edge for geographically dispersed, Regional for regional customers
- DynamoDB: On-demand for unpredictable traffic, provisioned for consistent
- Step Functions: Standard for long-running, Express for high-volume

## Cost Optimization

### Resource Optimization
- Use AWS Compute Optimizer for Lambda memory recommendations
- Consider ARM/Graviton processors
- Set appropriate log retention periods
- Use VPC endpoints instead of NAT Gateways when possible

### Code Optimization
- Use global variables to maintain connections
- Consider connection pooling with RDS Proxy
- Use Athena SQL or S3 Select to retrieve only needed data

## Deployment Strategies

### Blue/Green Deployments
- Near zero-downtime releases
- Keep old environment warm for quick rollback
- Use CloudWatch high-resolution metrics for monitoring

### Canary Deployments
- Deploy percentage of requests to new code
- Monitor for errors and regressions
- Use Lambda aliases with AWS CodeDeploy

## Lambda Configuration Best Practices

- Configure memory based on performance testing
- Set timeout values based on execution patterns
- Use provisioned concurrency for scale without latency fluctuations
- Configure VPC access only when necessary
- Use Lambda extensions judiciously

## DynamoDB Best Practices

- Use on-demand tables unless performance tests exceed quotas
- Follow best practices for well-distributed hash keys
- Use DAX for read-heavy workloads
- Consider TTL to expire unwanted data

## Step Functions Best Practices

- Standard Workflows: Long-running, durable, auditable
- Express Workflows: High-volume, event-processing
- Avoid polling loops - use Callbacks or .sync integration
- Ensure Express Workflow logic is idempotent
