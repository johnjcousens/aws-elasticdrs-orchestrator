# Product Overview

## Project Purpose

AWS DRS Orchestration is a serverless disaster recovery orchestration platform for AWS Elastic Disaster Recovery (DRS) that enables enterprise organizations to orchestrate complex multi-tier application recovery with wave-based execution, dependency management, and automated health checks using AWS-native services.

## Value Proposition

- **Wave-Based Recovery**: Execute disaster recovery in coordinated waves with explicit dependencies between tiers (database → application → web)
- **Protection Groups**: Organize DRS source servers into logical groups for coordinated recovery with automatic discovery
- **Drill Mode**: Test recovery procedures without impacting production environments
- **Real-Time Monitoring**: Track execution progress with detailed status updates and comprehensive audit trails
- **API-First Design**: Complete REST API for DevOps integration and automation workflows
- **Enterprise-Grade**: Built on AWS serverless architecture with CloudFormation IaC for reproducible deployments

## Key Features

### Protection Groups
- Organize DRS source servers into logical groups
- Automatic server discovery across AWS DRS-supported regions
- Visual server selection with assignment tracking
- Single server per group constraint to prevent conflicts
- Real-time search and filtering capabilities

### Recovery Plans
- Define multi-wave recovery sequences with unlimited waves
- Sequential wave execution with dependencies
- Dependency validation with circular dependency detection
- Support for both Drill and Recovery execution types

### Execution Engine
- Step Functions-based orchestration for reliability
- Wave-by-wave execution with status polling
- DRS job monitoring with LAUNCHED status detection
- Comprehensive execution history and audit trails
- Real-time progress tracking and error handling

### Frontend Application
- CloudScape Design System UI components
- Cognito-based authentication and authorization
- CloudFront CDN distribution for global performance
- Real-time status updates and execution monitoring
- Intuitive protection group and recovery plan management

## AWS DRS Regional Availability

The solution supports disaster recovery orchestration in all AWS regions where Elastic Disaster Recovery (DRS) is available:

**Americas**: US East (N. Virginia, Ohio), US West (Oregon, N. California), Canada (Central)
**Europe**: Ireland, London, Frankfurt, Paris, Stockholm, Milan
**Asia Pacific**: Tokyo, Sydney, Singapore

*Note: Regional availability is determined by AWS DRS service availability, not the orchestration solution. As AWS expands DRS to additional regions, the solution automatically supports them.*

## Target Users

- **Disaster Recovery Teams**: Manage and execute DR plans for enterprise applications
- **DevOps Engineers**: Automate DR testing and integrate with CI/CD pipelines
- **Cloud Architects**: Design and implement multi-tier application recovery strategies
- **Compliance Officers**: Validate DR capabilities and maintain audit trails

## Use Cases

1. **Regular DR Testing**: Execute drill mode recoveries to validate DR readiness without production impact
2. **Actual DR Events**: Orchestrate full disaster recovery with wave-based execution and dependency management
3. **Multi-Tier Applications**: Recover complex applications with database, application, and web tiers in sequence
4. **Compliance Validation**: Demonstrate DR capabilities with comprehensive execution history and audit trails
5. **DevOps Integration**: Automate DR testing as part of CI/CD pipelines using the REST API

## Architecture Highlights

- **Serverless**: Lambda functions, Step Functions, API Gateway, DynamoDB
- **Infrastructure as Code**: Complete CloudFormation templates with nested stacks
- **Security**: Cognito authentication, IAM least-privilege policies, encryption at rest
- **Cost-Effective**: Pay-per-use serverless architecture ($12-40/month estimated)
- **Scalable**: Handles multiple concurrent executions and unlimited protection groups/plans
