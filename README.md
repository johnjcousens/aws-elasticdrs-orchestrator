# AWS DRS Orchestration Solution

Enterprise-grade disaster recovery orchestration for AWS Elastic Disaster Recovery (DRS) with wave-based execution, dependency management, and automated health checks.

[![AWS](https://img.shields.io/badge/AWS-DRS-FF9900?logo=amazonaws)](https://aws.amazon.com/disaster-recovery/)
[![CloudFormation](https://img.shields.io/badge/IaC-CloudFormation-232F3E?logo=amazonaws)](cfn/)
[![React](https://img.shields.io/badge/Frontend-React%2019-61DAFB?logo=react)](frontend/)
[![Python](https://img.shields.io/badge/Backend-Python%203.12-3776AB?logo=python)](lambda/)
[![Release](https://img.shields.io/badge/Release-MVP%20Drill%20Prototype%20Complete-green)](https://github.com/your-repo/releases/tag/MVP-DRILL-PROTOTYPE)

## 🚧 **MVP Drill Prototype Complete**

**Latest Version**: MVP Drill Prototype Complete (December 30, 2025)  
**Git Tag**: `MVP-DRILL-PROTOTYPE`

### 🚀 **What's Complete in MVP Drill Prototype**

- **Complete Disaster Recovery Platform**: Full-featured disaster recovery orchestration with multi-account support
- **Enhanced Tag-Based Selection**: Fixed DRS source server tag querying with complete hardware details
- **Multi-Account Management**: Account context system with enforcement logic and persistent state
- **Production-Ready Architecture**: 5 Lambda functions, 7 CloudFormation templates, comprehensive monitoring
- **Documentation Standards**: Updated to follow "Keep a Changelog" best practices
- **Enterprise Scale**: Supports all 30 AWS DRS regions with up to 300 replicating servers per account

**[View Complete Release Notes →](CHANGELOG.md#mvp-drill-prototype---december-30-2025)**

## Overview

AWS DRS Orchestration enables organizations to orchestrate complex multi-tier application recovery with wave-based execution, dependency management, and automated health checks using AWS-native serverless services.

### Key Capabilities

- **Cost-Effective**: $12-40/month operational cost with pay-per-use serverless pricing
- **Unlimited Waves**: Flexible wave-based orchestration with no artificial constraints
- **Platform Agnostic**: Supports any source platform (VMware, physical servers, cloud)
- **Sub-Second RPO**: Leverages AWS DRS continuous replication capabilities
- **Fully Serverless**: No infrastructure to manage, scales automatically

## Key Features

### Multi-Account Management 🆕

- **Account Context System**: Complete account management with enforcement logic and persistent state
- **Auto-Selection**: Single accounts automatically selected as default for seamless user experience
- **Account Selector**: Top navigation dropdown for intuitive account switching with full page context updates
- **Setup Wizard**: Guided first-time account configuration for new users
- **Default Preferences**: Persistent default account selection integrated into existing 3-tab settings panel
- **Page-Level Enforcement**: Features blocked until target account selected (multi-account scenarios only)
- **Enterprise Scale**: Foundation for managing DRS across multiple AWS accounts

### Protection Groups

- **Automatic Server Discovery**: Real-time DRS source server discovery across all AWS DRS-supported regions
- **Enhanced Tag-Based Selection** 🆕: Fixed to query DRS source server tags (not EC2 instance tags) with complete hardware details
- **Hardware Information Display**: Comprehensive server details including CPU cores, RAM (GiB), and IP address displayed in clean format during server selection
- **Tag-Based Server Selection**: Define Protection Groups using DRS source server tags (e.g., `DR-Application=HRP`, `DR-Tier=Database`)
- **Visual Server Selection**: Intuitive interface with assignment status indicators and detailed hardware specifications
- **Conflict Prevention**: Single server per group constraint prevents recovery conflicts; tag conflicts detected automatically
- **Real-Time Search**: Filter servers by hostname, Server ID, or Protection Group name

### Recovery Plans

- **Wave-Based Orchestration**: Define multi-wave recovery sequences with unlimited flexibility
- **Dependency Management**: Automatic wave dependency handling with circular dependency detection
- **Drill Mode**: Test recovery procedures without impacting production
- **Automation Hooks**: Pre-wave and post-wave actions for validation and health checks

### Execution Monitoring

- **Real-Time Dashboard**: Live execution progress with wave-level status tracking
- **Invocation Source Tracking**: Track execution origin (UI, CLI, API, EVENTBRIDGE, SSM, STEPFUNCTIONS)
- **Enhanced History Management** 🆕: Improved History page with selective deletion, fixed invocation source filtering, and descriptive search functionality
- **Date Range Filtering** 🆕: Comprehensive date filtering for execution history with American date format (MM-DD-YYYY), quick filter buttons (Last Hour, Today, Last Week, etc.), and custom date range selection
- **Pause/Resume Control**: Pause executions between waves for validation and resume when ready
- **Instance Termination**: Terminate recovery instances after successful testing with accurate progress tracking
- **DRS Job Events**: Real-time DRS job event monitoring with 3-second auto-refresh and collapsible view
- **Execution History**: Complete audit trail of all recovery executions with source badges and selective cleanup
- **CloudWatch Integration**: Deep-link to CloudWatch Logs for troubleshooting
- **Auto-Refresh**: All pages auto-refresh (30s for lists, 3-5s for active executions)

### EC2 Launch Configuration

- **Launch Template Management**: Configure EC2 launch settings per Protection Group
- **Complete Instance Type Support** 🆕: Access to ALL available EC2 instance types supported by DRS in each region (968+ types including modern families like m6a, m7i, c7g, r7i, and all current-generation instances)
- **Network Configuration**: Select subnets and security groups for recovery
- **IAM Instance Profiles**: Assign instance profiles to recovery instances
- **DRS Launch Settings**: Instance type right sizing, launch disposition, copy private IP/tags, OS licensing
- **Automatic Application**: Settings applied to all servers in Protection Group on save

### Configuration Export/Import

- **Full Backup**: Export all Protection Groups and Recovery Plans to JSON file
- **Portable Format**: Uses `ProtectionGroupName` instead of IDs for cross-environment portability
- **Non-Destructive Import**: Additive-only import skips existing resources by name
- **Name Resolution**: Automatically resolves Protection Group names to IDs during import
- **Dry Run Mode**: Validate import without making changes
- **Server Validation**: Verifies DRS source servers exist before import
- **Settings Modal**: Access via gear icon in top navigation bar

## Architecture

![AWS DRS Orchestration Architecture](docs/architecture/AWS-DRS-Orchestration-Architecture.png)

*[View/Edit Source Diagram](docs/architecture/AWS-DRS-Orchestration-Architecture.drawio)*

The solution follows a serverless, event-driven architecture with clear separation between frontend, API, compute, data, and DRS integration layers. Users access the React frontend via CloudFront, authenticate through Cognito, and interact with the REST API backed by Lambda functions. Step Functions orchestrates wave-based recovery execution, coordinating with AWS DRS to launch recovery instances.

### Technology Stack

| Layer      | Technology                                               |
| ---------- | -------------------------------------------------------- |
| Frontend   | React 19.1, TypeScript 5.9, CloudScape Design System 3.0 |
| API        | Amazon API Gateway (REST), Amazon Cognito                |
| Compute    | AWS Lambda (Python 3.12), AWS Step Functions             |
| Database   | Amazon DynamoDB (3 tables with GSI)                      |
| Hosting    | Amazon S3, Amazon CloudFront                             |
| DR Service | AWS Elastic Disaster Recovery (DRS)                      |

## AWS DRS Regional Availability

The solution orchestrates disaster recovery in all **30 AWS regions** where Elastic Disaster Recovery (DRS) is available:

| Region Group                   | Count | Regions                                                                                                    |
| ------------------------------ | ----- | ---------------------------------------------------------------------------------------------------------- |
| **Americas**             | 6     | US East (N. Virginia, Ohio), US West (Oregon, N. California), Canada (Central), South America (São Paulo) |
| **Europe**               | 8     | Ireland, London, Frankfurt, Paris, Stockholm, Milan, Spain, Zurich                                         |
| **Asia Pacific**         | 10    | Tokyo, Seoul, Osaka, Singapore, Sydney, Mumbai, Hyderabad, Jakarta, Melbourne, Hong Kong                   |
| **Middle East & Africa** | 4     | Bahrain, UAE, Cape Town, Tel Aviv                                                                          |
| **GovCloud**             | 2     | US-East, US-West                                                                                           |

*Regional availability determined by AWS DRS service. As AWS expands DRS, the solution automatically supports new regions.*

## Quick Start

### Prerequisites

- AWS Account with DRS configured and source servers replicating
- AWS CLI v2 configured with appropriate permissions
- S3 bucket for deployment artifacts

### Deploy with CloudFormation

```bash
# Deploy the complete solution
aws cloudformation deploy \
  --template-url https://your-bucket.s3.us-east-1.amazonaws.com/cfn/master-template.yaml \
  --stack-name drs-orchestration \
  --parameter-overrides \
    ProjectName=drs-orchestration \
    Environment=prod \
    SourceBucket=your-bucket \
    AdminEmail=admin@yourcompany.com \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1
```

Deployment takes approximately 20-30 minutes.

### Get Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name drs-orchestration \
  --query 'Stacks[0].Outputs' \
  --output table
```

| Output           | Description              |
| ---------------- | ------------------------ |
| CloudFrontURL    | Frontend application URL |
| ApiEndpoint      | REST API endpoint        |
| UserPoolId       | Cognito User Pool ID     |
| UserPoolClientId | Cognito App Client ID    |

### Create Admin User

```bash
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name drs-orchestration \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username admin@yourcompany.com \
  --user-attributes Name=email,Value=admin@yourcompany.com Name=email_verified,Value=true \
  --temporary-password "TempPass123!" \
  --message-action SUPPRESS

aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username admin@yourcompany.com \
  --password "YourSecurePassword123!" \
  --permanent
```

## Usage Guide

### Creating a Protection Group

1. Navigate to **Protection Groups** in the sidebar
2. Click **Create Protection Group**
3. Enter a unique name and select the AWS region
4. Select source servers from the discovery list (green = available, red = assigned)
5. Click **Create**

### Creating a Recovery Plan

1. Navigate to **Recovery Plans** in the sidebar
2. Click **Create Recovery Plan**
3. Enter plan name and configure waves:

| Wave | Tier        | Protection Groups        | Depends On |
| ---- | ----------- | ------------------------ | ---------- |
| 1    | Database    | DB-Primary, DB-Secondary | -          |
| 2    | Application | App-Servers              | Wave 1     |
| 3    | Web         | Web-Servers              | Wave 2     |

4. Configure optional pre/post-wave automation
5. Click **Create**

### Executing a Recovery

1. Navigate to **Recovery Plans**
2. Select a plan and click **Execute**
3. Choose execution type:
   - **Drill**: Test recovery without production impact
   - **Recovery**: Full disaster recovery execution
4. Monitor progress in **Executions** page
5. **Control execution**:
   - **Pause**: Stop between waves for validation
   - **Resume**: Continue paused execution
   - **Cancel**: Stop execution and cleanup
   - **Terminate Instances**: Remove recovery instances after testing

## Infrastructure

### CloudFormation Stacks

The solution uses a modular nested stack architecture for maintainability:

| Stack                         | Purpose             | Key Resources                     |
| ----------------------------- | ------------------- | --------------------------------- |
| `master-template.yaml`      | Root orchestrator   | Parameter propagation, outputs    |
| `database-stack.yaml`       | Data persistence    | 3 DynamoDB tables with encryption |
| `lambda-stack.yaml`         | Compute layer       | Lambda functions, IAM roles     |
| `api-stack.yaml`            | API & Auth          | API Gateway, Cognito              |
| `step-functions-stack.yaml` | Orchestration       | Step Functions state machine      |
| `security-stack.yaml`       | Security (optional) | WAF, CloudTrail                   |
| `frontend-stack.yaml`       | Frontend hosting    | S3, CloudFront                    |

### DynamoDB Tables

| Table                       | Purpose             | Key Schema                            |
| --------------------------- | ------------------- | ------------------------------------- |
| `protection-groups-{env}` | Server groupings    | `GroupId` (PK)                      |
| `recovery-plans-{env}`    | Wave configurations | `PlanId` (PK)                       |
| `execution-history-{env}` | Audit trail         | `ExecutionId` (PK), `PlanId` (SK) |

## Cost Estimate

| Component       | Monthly Cost (Est.)    |
| --------------- | ---------------------- |
| Lambda          | $1-5                   |
| API Gateway     | $3-10                  |
| DynamoDB        | $1-5                   |
| CloudFront      | $1-5                   |
| S3              | <$1                    |
| Step Functions  | $1-5                   |
| Cognito         | Free tier              |
| **Total** | **$12-40/month** |

*Costs vary based on usage. DRS replication costs are separate and depend on protected server count.*

## Security

- **Encryption at Rest**: All data encrypted (DynamoDB, S3)
- **Encryption in Transit**: HTTPS enforced via CloudFront
- **Authentication**: Cognito JWT token-based authentication
- **Authorization**: IAM least-privilege policies
- **Optional**: WAF protection and CloudTrail audit logging

## Documentation

### Essential Guides

| Document | Description |
|----------|-------------|
| [API Reference Guide](docs/guides/API_REFERENCE_GUIDE.md) | Complete REST API documentation with examples |
| [Development Workflow Guide](docs/guides/DEVELOPMENT_WORKFLOW_GUIDE.md) | Development, testing, and deployment procedures |
| [Troubleshooting Guide](docs/guides/TROUBLESHOOTING_GUIDE.md) | Common issues and debugging procedures |
| [Deployment Guide](docs/guides/DEPLOYMENT_AND_OPERATIONS_GUIDE.md) | Step-by-step deployment instructions |
| [Multi-Account Setup Guide](docs/guides/MULTI_ACCOUNT_SETUP_GUIDE.md) | Complete multi-account hub and spoke setup |
| [Orchestration Integration](docs/guides/ORCHESTRATION_INTEGRATION_GUIDE.md) | CLI, SSM, Step Functions, API integration |

### Requirements & Architecture

| Document | Description |
|----------|-------------|
| [Product Requirements](docs/requirements/PRODUCT_REQUIREMENTS_DOCUMENT.md) | Complete PRD with features and specifications |
| [Architecture Design](docs/architecture/ARCHITECTURAL_DESIGN_DOCUMENT.md) | System architecture and design decisions |
| [Architecture Diagrams](docs/architecture/ARCHITECTURE_DIAGRAMS.md) | Visual reference - Complete mermaid diagrams |

### Implementation & Testing

| Document | Description |
|----------|-------------|
| [Testing Guide](docs/guides/TESTING_AND_QUALITY_ASSURANCE.md) | Testing procedures and quality assurance |
| [Local Development](docs/guides/LOCAL_DEVELOPMENT.md) | Development environment setup |
| [Manual Test Instructions](docs/guides/MANUAL_TEST_INSTRUCTIONS.md) | Manual testing procedures |

For complete documentation index, see [Documentation Index](.kiro/steering/docs-index.md).

## Future Enhancements

### Active Development Roadmap

| Priority | Feature Category | LOE | Description | Status |
|----------|------------------|-----|-------------|--------|
| 6 | **Scheduled Drills** | 3-5d | Automated scheduled drill executions with EventBridge rules | Planned |
| 7 | **SNS Notification Integration** | 1-2w | Real-time notifications for execution status changes via Email, SMS, Slack | Planned |
| 9 | **Step Functions Visualization** | 2-3w | Real-time visualization of Step Functions state machine execution | Planned |
| 10-18 | **Cross-Account Features** | 8-12w | Cross-account orchestration, monitoring, and extended source servers | Planned |
| 12 | **DRS Source Server Management** | 8-10w | Complete DRS server configuration including tags, disk settings, replication | Planned |

For detailed implementation plans, see:
- [Cross-Account Features](docs/implementation/CROSS_ACCOUNT_FEATURES.md)
- [DRS Source Server Management](docs/implementation/DRS_SOURCE_SERVER_MANAGEMENT.md)
- [Automation & Orchestration](docs/implementation/AUTOMATION_AND_ORCHESTRATION.md)
- [Notifications & Monitoring](docs/implementation/NOTIFICATIONS_AND_MONITORING.md)
- [Recovery Enhancements](docs/implementation/RECOVERY_ENHANCEMENTS.md)
- [Infrastructure Improvements](docs/implementation/INFRASTRUCTURE_IMPROVEMENTS.md)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Repository Snapshots & Rollback

The repository uses Git tags to mark significant milestones:

| Tag | Description | Date |
|-----|-------------|------|
| `MVP-DRILL-PROTOTYPE` | **MVP Drill Prototype Complete** - Complete disaster recovery orchestration platform with multi-account support, tag-based selection, and comprehensive drill capabilities | December 30, 2025 |
| `v2.0.0-mvp-drill-prototype` | **MVP Drill Only Prototype v2.0** - Core drill functionality with comprehensive documentation | December 30, 2025 |
| `mvp-demo-ready` | MVP Demo Ready - Complete working state with all core features | December 9, 2025 |

### Rollback to a Tag

```bash
# View the repository at the tagged state
git checkout mvp-demo-ready

# Create a new branch from tag for development
git checkout -b my-feature-branch mvp-demo-ready

# Return to main branch
git checkout main
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete project history since November 8, 2025.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Built for enterprise disaster recovery on AWS