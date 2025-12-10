# Product Overview

## Project Purpose

AWS DRS Orchestration is a serverless disaster recovery orchestration platform for AWS Elastic Disaster Recovery (DRS) that enables enterprise organizations to orchestrate complex multi-tier application recovery with wave-based execution, dependency management, and automated health checks using AWS-native services.

## Value Proposition

- **Wave-Based Recovery**: Execute disaster recovery in coordinated waves with explicit dependencies between tiers (database → application → web)
- **Protection Groups**: Organize DRS source servers into logical groups for coordinated recovery with automatic discovery
- **Pause/Resume Execution**: Pause execution before specific waves for manual validation, then resume when ready
- **Drill Mode**: Test recovery procedures without impacting production environments
- **Real-Time Monitoring**: Track execution progress with 3-second polling, detailed status updates, and comprehensive audit trails
- **Instance Lifecycle Management**: Terminate recovery instances after drill completion to manage costs
- **API-First Design**: Complete REST API for DevOps integration and automation workflows
- **Enterprise-Grade**: Built on AWS serverless architecture with CloudFormation IaC for reproducible deployments

## Key Features

### Protection Groups

- Organize DRS source servers into logical groups
- Automatic server discovery across all 30 AWS DRS-supported regions
- Visual server selection with real-time status indicators (Available/Assigned)
- Single server per group constraint (globally enforced across all users)
- Real-time search and filtering in server discovery panel
- Conflict detection prevents duplicate server assignments
- Server validation against DRS API (prevents fake/invalid server IDs)

### Recovery Plans

- Define multi-wave recovery sequences with unlimited waves
- Each wave can reference its own Protection Group (multi-PG support)
- Sequential wave execution with dependencies
- Configurable pause points before any wave (except Wave 1)
- Dependency validation with circular dependency detection
- Support for both Drill and Recovery execution types


### Execution Engine

- Step Functions-based orchestration with `waitForTaskToken` callback pattern
- Wave-by-wave execution with automatic status polling
- Pause/Resume capability using Step Functions task tokens (up to 1 year timeout)
- DRS job monitoring with LAUNCHED status detection
- Comprehensive execution history and audit trails
- Real-time progress tracking with 3-second UI polling intervals
- Terminate Instances action for post-drill cleanup
- **Server Conflict Detection**: Prevents starting executions when servers are in use by another active/paused execution (UI buttons grayed out with reason)
- **Status Values**: PENDING, POLLING, INITIATED, LAUNCHING, STARTED, IN_PROGRESS, RUNNING, PAUSED, COMPLETED, PARTIAL, FAILED, CANCELLED

### DRS Service Limits Validation

- **Hard Limit Enforcement**: 300 replicating servers per account per region
- **Job Size Validation**: Maximum 100 servers per recovery job
- **Concurrent Job Monitoring**: Maximum 20 concurrent jobs
- **Total Server Tracking**: Maximum 500 servers across all active jobs
- **Real-time Quota Display**: Live usage metrics in UI with status indicators
- **Proactive Blocking**: Prevents operations that would exceed limits

### Frontend Application

- CloudScape Design System UI with 23 MVP components (32 total including Phase 2)
- Cognito-based authentication with 45-minute auto-logout
- CloudFront CDN distribution for global performance
- Real-time status updates and execution monitoring with 3-second polling
- DRS Job Events timeline with auto-refresh
- DRS Service Limits validation and quota display
- Intuitive protection group and recovery plan management

## AWS DRS Regional Availability

The solution supports disaster recovery orchestration in all **30 AWS regions** where Elastic Disaster Recovery (DRS) is available:

| Region Group | Count | Regions |
|--------------|-------|---------|
| **Americas** | 6 | US East (N. Virginia, Ohio), US West (Oregon, N. California), Canada (Central), South America (São Paulo) |
| **Europe** | 8 | Ireland, London, Frankfurt, Paris, Stockholm, Milan, Spain, Zurich |
| **Asia Pacific** | 10 | Tokyo, Seoul, Osaka, Singapore, Sydney, Mumbai, Hyderabad, Jakarta, Melbourne, Hong Kong |
| **Middle East & Africa** | 4 | Bahrain, UAE, Cape Town, Tel Aviv |
| **GovCloud** | 2 | US-East, US-West |

*Note: Regional availability is determined by AWS DRS service availability, not the orchestration solution.*

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
6. **Controlled Recovery**: Pause execution before critical waves for manual validation before proceeding

## Phase 2: Advanced Features

| Priority | Feature | Description |
|----------|---------|-------------|
| 3 | **DRS Source Server Management** | Complete DRS source server configuration from UI |
| 4 | **DRS Tag Synchronization** | Synchronize EC2 instance tags to DRS source servers |
| 5 | **SSM Automation Integration** | Pre-wave and post-wave SSM automation |
| 6 | **Step Functions Visualization** | Real-time state machine execution visualization |
| 7 | **Multi-Account Support** | Cross-account orchestration, scale beyond 300 servers |
| 8 | **Cross-Account DRS Monitoring** | Centralized monitoring across multiple accounts |
| 9 | **SNS Notification Integration** | Real-time notifications via Email, SMS, Slack |
| 10 | **Scheduled Drills** | Automated recurring drill execution |
| 11 | **CodeBuild & CodeCommit Migration** | AWS-native CI/CD pipeline |

## Architecture Highlights

- **Serverless**: 5 Lambda functions, Step Functions, API Gateway, DynamoDB
- **Infrastructure as Code**: 7 CloudFormation templates (1 master + 6 nested stacks)
- **Security**: Cognito authentication, IAM least-privilege policies, encryption at rest
- **Cost-Effective**: Pay-per-use serverless architecture ($12-40/month estimated)
- **Scalable**: Handles multiple concurrent executions and unlimited protection groups/plans
- **Data Storage**: 3 DynamoDB tables (protection-groups, recovery-plans, execution-history)
