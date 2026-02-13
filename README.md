# AWS DRS Orchestration Solution

Disaster recovery orchestration for AWS Elastic Disaster Recovery (DRS) with wave-based execution, dependency management, and automated health checks.

[![AWS](https://img.shields.io/badge/AWS-DRS-FF9900?logo=amazonaws)](https://aws.amazon.com/disaster-recovery/)
[![Version](https://img.shields.io/badge/version-6.0.0-blue)](CHANGELOG.md)
[![CloudFormation](https://img.shields.io/badge/IaC-CloudFormation-232F3E?logo=amazonaws)](cfn/)
[![React](https://img.shields.io/badge/Frontend-React%2019.1.1-61DAFB?logo=react)](frontend/)
[![Python](https://img.shields.io/badge/Backend-Python%203.12-3776AB?logo=python)](lambda/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Overview

AWS DRS Orchestration enables organizations to orchestrate complex multi-tier application recovery with wave-based execution, dependency management, and automated health checks using AWS-native serverless services.

### Key Capabilities

- **Cost-Effective**: $12-40/month operational cost with pay-per-use serverless pricing
- **Unlimited Waves**: Flexible wave-based orchestration with no artificial constraints
- **Platform Agnostic**: Supports any source platform (physical servers, cloud instances, virtual machines)
- **Sub-Second RPO**: Leverages AWS DRS continuous replication capabilities
- **Fully Serverless**: No infrastructure to manage, scales automatically
- **Launch Config Sync**: Automatically applies Protection Group launch configurations to DRS at execution time

## Key Features

### Per-Server Launch Configuration (v1.1.0)
- **Individual Server Customization**: Override protection group defaults for specific servers requiring unique launch settings
- **Static Private IP Assignment**: Assign static IPs to servers with real-time validation against subnet CIDR ranges
- **Granular Launch Template Control**: Configure subnet, security groups, instance type, licensing, and launch disposition per server
- **Duplicate IP Prevention**: Built-in validation prevents assigning the same static IP to multiple servers
- **Flexible Configuration Model**: Servers inherit group defaults by default, override only what's needed
- **UI-Driven Management**: Configure per-server settings through intuitive Server Configurations tab in Protection Group dialog

### Direct Lambda Invocation Mode (v5.0.0)
- **Dual Invocation Support**: All three Lambda handlers (Query, Data Management, Execution) support both API Gateway and direct Lambda invocation
- **44 Operations via CLI/SDK**: Complete DR automation without API Gateway — invoke Lambda directly from AWS CLI, SDK, Step Functions, or EventBridge
- **60% Cost Reduction**: Eliminates API Gateway request charges for automation workloads ($8-30/month vs $12-40/month full stack)
- **Native AWS Authentication**: IAM roles replace Cognito tokens for machine-to-machine communication
- **Backward Compatible**: All existing API Gateway endpoints and frontend integrations continue to work unchanged
- **CI/CD Pipeline Ready**: Bash and Python integration examples for automated DR workflows

### SNS Email Notifications & Callback (v6.0.0)
- **Pause/Resume via Email**: When execution pauses between waves, operators receive an SNS email with ready-to-run AWS CLI commands to resume or cancel — no frontend or API Gateway required
- **CloudShell Integration**: Email includes a direct link to AWS CloudShell in the correct region for one-click access
- **Infrastructure Status Feedback**: After resume/cancel, a DynamoDB query runs automatically in CloudShell showing real execution status
- **State Reconstruction**: CLI resume with `--task-output '{}'` works seamlessly — full execution state (waves, account context, server IDs) restored from DynamoDB snapshot
- **Wave Merge Persistence**: Race condition fix ensures all waves are visible in the UI immediately after CLI resume, keeping frontend, API, and CLI in sync
- **Plain-Text Email Format**: All notification types (start, complete, fail, pause) use clean plain-text formatting compatible with any email client

### Wave-Based Orchestration Engine
- **Step Functions Integration**: `waitForTaskToken` pattern enables pause/resume with up to 1-year timeouts
- **Dependency Management**: Waves execute only after dependencies complete successfully
- **Manual Validation Points**: Pause before critical waves for human approval
- **Email Pause/Resume Notifications**: SNS email with CloudShell link and copy-paste CLI commands to resume or cancel directly from email — no frontend or API Gateway required
- **DynamoDB State Reconstruction**: Resume from CLI with `--task-output '{}'` — full execution state restored from DynamoDB snapshot
- **Real-Time Control**: Resume, cancel, or terminate operations during execution
- **Parallel Execution**: Servers within waves launch in parallel with DRS-safe 15-second delays
- **Launch Config Sync**: Protection Group settings (subnet, security groups, instance type) applied to DRS before recovery

### Dynamic Tag Synchronization
- **EventBridge Scheduling**: Automated EC2 → DRS tag sync with configurable intervals (1-24 hours)
- **Immediate Sync Triggers**: Automatic manual sync when settings are updated
- **Multi-Region Support**: Synchronizes across all 30 AWS DRS regions automatically

### Protection Groups & Recovery Plans
- **Tag-Based Selection**: Servers automatically included/excluded based on current tags
- **Multi-Protection-Group Waves**: Single wave can orchestrate multiple protection groups
- **Conflict Detection**: Prevents servers from being assigned to multiple groups globally
- **Launch Configuration Inheritance**: Group-level settings applied to all member servers at execution time
- **Per-Server Launch Customization**: Override group defaults for individual servers with custom launch settings
- **Static IP Assignment**: Assign static private IP addresses to specific servers (validated against subnet CIDR)
- **Granular Launch Control**: Configure subnet, security groups, instance type, licensing, and launch disposition per server
- **Simplified DRS Management**: Eliminates need to manually configure each server's launch template in the DRS console

### Comprehensive REST API
- **58 API Endpoints**: Complete REST API across 9 categories with RBAC security
- **Cross-Account Operations**: Manage DRS across multiple AWS accounts
- **Direct Lambda Invocation**: Bypass API Gateway for AWS-native automation
- **DRS Operations**: Supports core orchestration operations (describe servers, start recovery, get/update launch configuration, describe jobs and events, describe recovery instances)

## Architecture

### Full-Stack Architecture (CloudFront + Cognito + API Gateway)

![AWS DRS Orchestration - Comprehensive Architecture](docs/architecture/AWS-DRS-Orchestration-Architecture-Comprehensive.png)

**Components**: CloudFront CDN, S3 Static Hosting, Cognito User Pool, API Gateway, 6 Lambda functions, Step Functions, DynamoDB (4 tables), EventBridge, CloudWatch, SNS, AWS DRS, Cross-Account IAM Roles

**User Roles**: DRSOrchestrationAdmin, DRSRecoveryManager, DRSPlanManager, DRSOperator, DRSReadOnly

### Backend-Only Architecture (Direct Lambda Invocation)

![AWS DRS Orchestration - Backend Only](docs/architecture/AWS-DRS-Orchestration-Backend-Only.png)

**Use Case**: CLI/SDK automation, internal operations tools, CI/CD pipeline integration

**Benefits**: 60% lower cost (no API Gateway), simpler architecture, native AWS authentication, ideal for automation

**Deployment**: Set `DeployFrontend=false` parameter in CloudFormation deployment

### Technology Stack

| Layer      | Technology                                                    |
| ---------- | ------------------------------------------------------------- |
| Frontend   | React 19.1.1, TypeScript 5.9.3, CloudScape Design System 3.0.1148 |
| API        | Amazon API Gateway (REST), Amazon Cognito                     |
| Compute    | AWS Lambda (Python 3.12), AWS Step Functions                  |
| Database   | Amazon DynamoDB (4 tables with GSI, native camelCase schema)  |
| Hosting    | Amazon S3, Amazon CloudFront                                  |
| DR Service | AWS Elastic Disaster Recovery (DRS)                           |

## Deployment Flexibility

The solution supports **3 flexible deployment modes** to accommodate different use cases, from standalone deployments to external platform integration:

| Mode | Resources Deployed | Frontend | Monthly Cost | Use Case |
|------|-------------------|----------|--------------|----------|
| **1. Default Standalone** | All (IAM + DB + Lambda + API) | ✅ Deployed | $12-40 | Complete self-contained solution with web UI |
| **2. API-Only Standalone** | All (IAM + DB + Lambda + API) | ❌ Skipped | $8-30 | Direct Lambda invocation OR Cognito RBAC API calls |
| **3. External IAM Integration** | All resources, external IAM role | ❌ Skipped | $8-30 | Centralized IAM management, external role |

**Mode 1** provides a complete standalone solution with CloudFront CDN, Cognito authentication, and React UI. **Mode 2** removes the frontend but keeps API Gateway for Cognito-authenticated RBAC API calls OR direct Lambda invocation with OrchestrationRole. **Mode 3** uses an externally-provided IAM role for all Lambda functions, enabling centralized permission management.

**📖 See [Deployment Flexibility Guide](docs/guides/DEPLOYMENT_FLEXIBILITY_GUIDE.md) for complete documentation, migration procedures, and troubleshooting.**

### Unified Orchestration Role

All Lambda functions use a **single unified IAM role** that consolidates permissions from 7 individual function roles:

**Key Benefits:**
- **Simplified Management**: One role instead of seven (~500 lines of CloudFormation removed)
- **Consistent Permissions**: All functions have access to required services
- **External Role Support**: Integrate with centralized permission management
- **16 Policy Statements**: Comprehensive permissions for DRS, EC2, Step Functions, DynamoDB, and more

**Critical Permissions Included:**
- `states:SendTaskHeartbeat` - Long-running Step Functions tasks
- `drs:CreateRecoveryInstanceForDrs` - AllowLaunchingIntoThisInstance pattern (IP preservation)
- `ec2:CreateLaunchTemplateVersion` - Launch template updates for pre-provisioned instances
- `ssm:CreateOpsItem` - Operational tracking and visibility

**For External Integration:** See [Orchestration Role Specification](docs/reference/ORCHESTRATION_ROLE_SPECIFICATION.md) for complete role requirements.

### Deployment Mode Examples

```bash
# Mode 1: Default Standalone (Full Stack with Frontend)
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name aws-drs-orchestration-dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    ProjectName=aws-drs-orchestration \
    Environment=dev \
    SourceBucket=aws-drs-orchestration-dev \
    AdminEmail=admin@example.com

# Mode 2: API-Only Standalone (No Frontend)
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name aws-drs-orchestration-dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    ProjectName=aws-drs-orchestration \
    Environment=dev \
    SourceBucket=aws-drs-orchestration-dev \
    AdminEmail=admin@example.com \
    DeployFrontend=false

# Mode 3: External IAM Role Integration
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name aws-drs-orchestration-dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    ProjectName=aws-drs-orchestration \
    Environment=dev \
    SourceBucket=aws-drs-orchestration-dev \
    AdminEmail=admin@example.com \
    OrchestrationRoleArn=arn:aws:iam::111122223333:role/ExternalOrchestrationRole \
    DeployFrontend=false
```

### CloudFormation Parameters

**Core Parameters:**
- `ProjectName` (String, default: 'aws-drs-orchestration') - Project identifier for resource naming
- `Environment` (String, default: 'dev') - Environment name (dev, test, prod)
- `SourceBucket` (String, required) - S3 bucket containing nested CloudFormation templates and Lambda code
- `AdminEmail` (String, required) - Admin email for Cognito user pool

**Deployment Mode Parameters:**
- `DeployFrontend` (String, default: 'true') - Deploy frontend (S3 + CloudFront)
- `OrchestrationRoleArn` (String, optional) - External IAM role ARN for Lambda functions

**Example with All Parameters:**
```bash
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name aws-drs-orchestration-dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    ProjectName=aws-drs-orchestration \
    Environment=dev \
    SourceBucket=aws-drs-orchestration-dev \
    AdminEmail=admin@example.com \
    DeployFrontend=true
```

**See [Deployment Flexibility Guide](docs/guides/DEPLOYMENT_FLEXIBILITY_GUIDE.md) for complete documentation.**

## Configuration Example

### Sample Recovery Plan with Per-Server Launch Configuration

Below is an example configuration showing a 3-tier application recovery plan with per-server launch customization:

```json
{
  "schemaVersion": "1.1",
  "exportedAt": "2026-01-29T02:47:18Z",
  "sourceRegion": "us-east-1",
  "sourceAccount": "123456789012",
  "protectionGroups": [
    {
      "groupName": "DatabaseServersWaveGroup",
      "description": "Database tier servers",
      "region": "us-west-2",
      "sourceServerIds": ["s-db001", "s-db002"],
      "launchConfig": {
        "subnetId": "subnet-db123456",
        "securityGroupIds": ["sg-db123456"],
        "instanceType": "r7a.large",
        "copyTags": true,
        "launchDisposition": "STARTED",
        "licensing": { "osByol": false }
      },
      "servers": [
        {
          "sourceServerId": "s-db001",
          "useGroupDefaults": false,
          "launchTemplate": {
            "subnetId": "subnet-db-az1",
            "staticPrivateIp": "10.100.56.13",
            "securityGroupIds": ["sg-db123456"],
            "instanceType": "r7a.large"
          }
        },
        {
          "sourceServerId": "s-db002",
          "useGroupDefaults": false,
          "launchTemplate": {
            "subnetId": "subnet-db-az2",
            "staticPrivateIp": "10.100.56.132",
            "securityGroupIds": ["sg-db123456"],
            "instanceType": "r7a.large"
          }
        }
      ]
    },
    {
      "groupName": "ApplicationServersWaveGroup",
      "description": "Application tier servers",
      "region": "us-west-2",
      "sourceServerIds": ["s-app001", "s-app002"],
      "launchConfig": {
        "subnetId": "subnet-app123456",
        "securityGroupIds": ["sg-app123456"],
        "instanceType": "c6a.large",
        "copyTags": true,
        "launchDisposition": "STARTED",
        "licensing": { "osByol": false }
      },
      "servers": [
        {
          "sourceServerId": "s-app001",
          "useGroupDefaults": false,
          "launchTemplate": {
            "subnetId": "subnet-app-az1",
            "staticPrivateIp": "10.100.216.147",
            "instanceType": "c6a.large"
          }
        },
        {
          "sourceServerId": "s-app002",
          "useGroupDefaults": false,
          "launchTemplate": {
            "subnetId": "subnet-app-az2",
            "staticPrivateIp": "10.100.216.65",
            "instanceType": "r6a.large"
          }
        }
      ]
    },
    {
      "groupName": "WebServersWaveGroup",
      "description": "Web tier servers",
      "region": "us-west-2",
      "sourceServerIds": ["s-web001", "s-web002"],
      "launchConfig": {
        "launchDisposition": "STARTED",
        "copyTags": true,
        "licensing": { "osByol": false }
      }
    }
  ],
  "recoveryPlans": [
    {
      "planName": "3TierFullStackRecoveryPlan",
      "description": "Database → Application → Web recovery sequence",
      "waves": [
        {
          "waveName": "Wave 1 - Database Tier",
          "waveNumber": 0,
          "protectionGroupIds": ["db-group-id"],
          "pauseBeforeWave": false,
          "dependsOnWaves": []
        },
        {
          "waveName": "Wave 2 - Application Tier",
          "waveNumber": 1,
          "protectionGroupIds": ["app-group-id"],
          "pauseBeforeWave": true,
          "dependsOnWaves": [0]
        },
        {
          "waveName": "Wave 3 - Web Tier",
          "waveNumber": 2,
          "protectionGroupIds": ["web-group-id"],
          "pauseBeforeWave": true,
          "dependsOnWaves": [1]
        }
      ]
    }
  ]
}
```

**Key Configuration Features:**
- **Schema Version 1.1**: Includes per-server launch configuration support
- **Protection Group Defaults**: Database and Application groups define default launch settings
- **Per-Server Overrides**: Individual servers override subnet and static IP assignments
- **Static IP Assignment**: Database and Application servers use static IPs validated against subnet CIDR
- **Wave Dependencies**: Application tier waits for Database, Web tier waits for Application
- **Manual Validation Points**: Pause before Application and Web tiers for health checks

## Quick Start

### Prerequisites

- AWS Account with DRS configured and source servers replicating
- AWS CLI v2 configured with appropriate permissions
- Node.js 18+ and npm (for frontend development)
- Python 3.12+ (for Lambda development and local CI/CD)
- S3 bucket for deployment artifacts

### Environment Setup

```bash
# Clone repository
git clone https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git
cd aws-elasticdrs-orchestrator

# Setup Python virtual environment (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### Cross-Account Setup (Simplified)

The solution uses **standardized cross-account role naming** to simplify multi-account configuration. When adding target or staging accounts, you only need to provide the account ID - the system automatically constructs the role ARN.

**Standardized Role Name**: `DRSOrchestrationRole` (no environment suffix)

**Setup Steps**:

1. **Deploy cross-account role in target/staging account**:
   ```bash
   aws cloudformation deploy \
     --template-file cfn/cross-account-role-stack.yaml \
     --stack-name drs-orchestration-role \
     --capabilities CAPABILITY_NAMED_IAM \
     --parameter-overrides \
       OrchestrationAccountId=YOUR_ORCHESTRATION_ACCOUNT_ID \
       ExternalId=YOUR_UNIQUE_EXTERNAL_ID
   ```

2. **Add account via API** (roleArn is optional):
   ```bash
   curl -X POST https://api-endpoint/accounts/target \
     -H "Authorization: Bearer $TOKEN" \
     -d '{
       "accountId": "123456789012",
       "accountName": "Production Account",
       "externalId": "YOUR_UNIQUE_EXTERNAL_ID"
     }'
   ```

   The system automatically constructs: `arn:aws:iam::123456789012:role/DRSOrchestrationRole`

**Backward Compatibility**: Existing accounts with custom role names continue to work. You can still provide an explicit `roleArn` if needed:
```bash
curl -X POST https://api-endpoint/accounts/target \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "accountId": "123456789012",
    "accountName": "Legacy Account",
    "externalId": "YOUR_UNIQUE_EXTERNAL_ID",
    "roleArn": "arn:aws:iam::123456789012:role/CustomRole-dev"
  }'
```

**See**: [DRS Cross-Account Setup Guide](docs/guides/DRS_CROSS_ACCOUNT_SETUP_VERIFICATION.md) for complete setup instructions.

### CloudFormation Deployment

```bash
# CloudFormation deployment
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name aws-drs-orchestration-dev \
  --parameter-overrides \
    ProjectName=aws-drs-orchestration \
    Environment=dev \
    SourceBucket=aws-drs-orchestration-dev \
    AdminEmail=your-email@example.com \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### Get Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name aws-drs-orchestration-dev \
  --query 'Stacks[0].Outputs' \
  --output table
```

| Output           | Description              |
| ---------------- | ------------------------ |
| CloudFrontURL    | Frontend application URL |
| ApiEndpoint      | REST API endpoint        |
| UserPoolId       | Cognito User Pool ID     |
| UserPoolClientId | Cognito App Client ID    |

## AWS DRS Regional Availability

The solution orchestrates disaster recovery in all **30 AWS regions** where Elastic Disaster Recovery (DRS) is available:

| Region Group                   | Count | Regions                                                                                                    |
| ------------------------------ | ----- | ---------------------------------------------------------------------------------------------------------- |
| **Americas**             | 6     | US East (N. Virginia, Ohio), US West (Oregon, N. California), Canada (Central), South America (São Paulo) |
| **Europe**               | 8     | Ireland, London, Frankfurt, Paris, Stockholm, Milan, Spain, Zurich                                         |
| **Asia Pacific**         | 10    | Tokyo, Seoul, Osaka, Singapore, Sydney, Mumbai, Hyderabad, Jakarta, Melbourne, Hong Kong                   |
| **Middle East & Africa** | 4     | Bahrain, UAE, Cape Town, Tel Aviv                                                                          |
| **GovCloud**             | 2     | US-East, US-West                                                                                           |

## Infrastructure

### CloudFormation Stacks (16 Templates)

The solution uses a modular nested stack architecture. The API Gateway is split across 6 stacks due to CloudFormation limits (500 resources/stack, 51,200 bytes template body, 1MB S3 template) and best practices for maintainability:

| Stack | Purpose | Key Resources |
| ----- | ------- | ------------- |
| `master-template.yaml` | Root orchestrator | Parameter propagation, nested stack coordination, **UnifiedOrchestrationRole** |
| `database-stack.yaml` | Data persistence | 4 DynamoDB tables with encryption (camelCase schema) |
| `lambda-stack.yaml` | Compute layer | 6 Lambda functions with reserved concurrency (100) |
| `api-auth-stack.yaml` | Authentication | Cognito User Pool, Identity Pool, RBAC groups |
| `api-gateway-core-stack.yaml` | API Gateway base | REST API, Cognito authorizer |
| `api-gateway-resources-stack.yaml` | API paths | URL path resources for all endpoints |
| `api-gateway-core-methods-stack.yaml` | CRUD methods | Protection Groups, Recovery Plans, Config endpoints |
| `api-gateway-operations-methods-stack.yaml` | Execution methods | Execution, workflow, DRS operation endpoints |
| `api-gateway-infrastructure-methods-stack.yaml` | Infrastructure methods | Discovery, cross-account, health endpoints |
| `api-gateway-deployment-stack.yaml` | API deployment | Stage deployment, access logging, throttling |
| `step-functions-stack.yaml` | Orchestration | State machine with waitForTaskToken |
| `eventbridge-stack.yaml` | Event scheduling | Execution polling rules |
| `frontend-stack.yaml` | Frontend hosting | S3 bucket, CloudFront distribution (conditional) |
| `waf-stack.yaml` | Web Application Firewall | WAF WebACL for CloudFront with rate limiting |
| `notification-stack.yaml` | Notifications | SNS topics, email subscriptions |
| `cross-account-role-stack.yaml` | Multi-account | Cross-account IAM roles |
| `github-oidc-stack.yaml` | CI/CD | OIDC authentication (optional) |

### Lambda Functions (6 Handlers)

All Lambda functions use the **UnifiedOrchestrationRole** (or externally-provided role in external integration mode). Shared utilities in `lambda/shared/` provide common functionality across all functions.

| Function | Directory | Purpose | Endpoints |
| -------- | --------- | ------- | --------- |
| `data-management-handler` | `lambda/data-management-handler/` | Protection groups, recovery plans, configuration management | 21 |
| `execution-handler` | `lambda/execution-handler/` | Recovery execution control, pause/resume, termination | 11 |
| `query-handler` | `lambda/query-handler/` | Read-only queries, DRS status, EC2 resource discovery | 12 |
| `orchestration-stepfunctions` | `lambda/orchestration-stepfunctions/` | Step Functions orchestration with launch config sync | N/A |
| `frontend-deployer` | `lambda/frontend-deployer/` | Frontend deployment automation (CloudFormation Custom Resource) | N/A |
| `notification-formatter` | `lambda/notification-formatter/` | SNS notification formatting | N/A |

**Total API Endpoints**: 58 endpoints across 3 API handlers

#### Shared Modules (`lambda/shared/`)

Common utilities used across all Lambda functions to eliminate code duplication and ensure consistency:

| Module | Purpose | Functions |
| ------ | ------- | --------- |
| `account_utils.py` | Multi-account management | `get_account_name()`, `ensure_default_account()`, `get_target_accounts()`, `validate_target_account()` |
| `conflict_detection.py` | Execution conflict prevention | `check_server_conflicts()`, `get_active_executions_for_plan()`, `query_drs_servers_by_tags()` |
| `cross_account.py` | Cross-account IAM operations | `create_drs_client()`, `determine_target_account_context()`, `get_current_account_id()` |
| `drs_limits.py` | DRS service limit validation | `validate_wave_sizes()`, `validate_concurrent_jobs()`, `validate_server_replication_states()` |
| `drs_utils.py` | DRS API helpers | `transform_drs_server_for_frontend()`, `map_replication_state_to_display()` |
| `execution_utils.py` | Execution state management | `can_terminate_execution()` |
| `response_utils.py` | API Gateway responses | `response()`, `DecimalEncoder` (includes security headers) |

**Benefits**: 638 lines of duplicate code eliminated, consistent error handling, single source of truth for business logic

### DynamoDB Tables (Native camelCase Schema)

| Table                       | Purpose             | Key Schema                            |
| --------------------------- | ------------------- | ------------------------------------- |
| `protection-groups-{env}` | Server groupings    | `groupId` (PK)                      |
| `recovery-plans-{env}`    | Wave configurations | `planId` (PK)                       |
| `execution-history-{env}` | Audit trail         | `executionId` (PK), `planId` (SK) |
| `target-accounts-{env}`   | Multi-account       | `accountId` (PK)                    |

## Cost Estimate

| Component       | Monthly Cost (Est.)    |
| --------------- | ---------------------- |
| Lambda          | $1-5                   |
| API Gateway     | $3-10                  |
| DynamoDB        | $1-5                   |
| CloudFront      | $1-5                   |
| S3              | <$1                    |
| Step Functions  | $1-5                   |
| WAF             | $5-10                  |
| Cognito         | Free tier              |
| **Total** | **$17-50/month** |

## Security & RBAC

### Role-Based Access Control
The solution implements comprehensive RBAC with 5 granular DRS-specific roles:

| Role | Description |
|------|-------------|
| **DRSOrchestrationAdmin** | Full administrative access |
| **DRSRecoveryManager** | Recovery operations lead |
| **DRSPlanManager** | DR planning focus |
| **DRSOperator** | On-call operations |
| **DRSReadOnly** | Audit and monitoring |

### Security Features
- **WAF Protection**: AWS WAF WebACL with rate limiting (2000 req/5min) and AWS managed rules
- **API Gateway Logging**: CloudWatch access logs for all API requests (30-day retention)
- **Lambda Concurrency Limits**: Reserved concurrency (100) prevents runaway scaling
- **Encryption**: All data encrypted at rest and in transit
- **Authentication**: Cognito JWT token-based authentication (45-minute session timeout)
- **Authorization**: API-level RBAC enforcement
- **Audit Trails**: Complete user action logging

### WAF Protection (waf-stack.yaml)

The solution includes AWS WAF protection for the CloudFront distribution with defense-in-depth security:

**Rate Limiting:**
- 2000 requests per 5 minutes per IP address
- Prevents DDoS and brute-force attacks
- Automatic blocking with CloudWatch metrics

**AWS Managed Rule Sets:**
| Rule Set | Purpose |
|----------|---------|
| AWSManagedRulesCommonRuleSet | OWASP Top 10 protection (SQL injection, XSS, etc.) |
| AWSManagedRulesKnownBadInputsRule | Blocks known malicious request patterns |
| AWSManagedRulesAmazonIpReputationList | Blocks requests from known bad IP addresses |

**WAF Deployment:**
- WAF is automatically deployed with the frontend stack when `DeployFrontend=true`
- WAF WebACL is created in `us-east-1` (required for CloudFront)
- CloudWatch metrics available under `AWS/WAFV2` namespace

**Monitoring WAF:**
```bash
# View blocked requests
AWS_PAGER="" aws cloudwatch get-metric-statistics \
  --namespace AWS/WAFV2 \
  --metric-name BlockedRequests \
  --dimensions Name=WebACL,Value=aws-drs-orchestration-waf-test \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum
```

**Cost:** WAF adds approximately $5-10/month depending on request volume.

## Documentation

### User Guides
- [Deployment Flexibility Guide](docs/guides/DEPLOYMENT_FLEXIBILITY_GUIDE.md) - 4 deployment modes, external IAM integration
- [Developer Guide](docs/guides/DEVELOPER_GUIDE.md) - Local development, testing, debugging workflows
- [DRS Execution Walkthrough](docs/guides/DRS_EXECUTION_WALKTHROUGH.md) - Complete drill and recovery procedures
- [DRS Pre-Provisioned Instance Recovery](docs/guides/DRS_PRE_PROVISIONED_INSTANCE_RECOVERY.md) - AllowLaunchingIntoThisInstance pattern
- [DRS Recovery and Failback Complete Guide](docs/guides/DRS_RECOVERY_AND_FAILBACK_COMPLETE_GUIDE.md) - End-to-end recovery procedures
- [API Development Quick Reference](docs/guides/API_DEVELOPMENT_QUICK_REFERENCE.md) - API development patterns

### Deployment & CI/CD
- [Quick Start Guide](docs/deployment/QUICK_START_GUIDE.md) - Fast deployment walkthrough
- [CI/CD Guide](docs/deployment/CICD_GUIDE.md) - Deployment workflows and automation
- [CI/CD Enforcement](docs/deployment/CI_CD_ENFORCEMENT.md) - Deployment policy and validation

### Requirements & Architecture
- [Product Requirements Document](docs/requirements/PRODUCT_REQUIREMENTS_DOCUMENT.md) - Complete PRD with feature specifications
- [Software Requirements Specification](docs/requirements/SOFTWARE_REQUIREMENTS_SPECIFICATION.md) - Technical specifications
- [UX/UI Design Specifications](docs/requirements/UX_UI_DESIGN_SPECIFICATIONS.md) - User interface design
- [Architecture](docs/architecture/ARCHITECTURE.md) - System architecture and AWS service integration
- [Lambda Handlers Architecture](docs/architecture/LAMBDA_HANDLERS_ARCHITECTURE.md) - Detailed Lambda handler architecture with Mermaid diagrams and direct invocation examples
- [Lambda Handlers Complete Analysis](docs/analysis/LAMBDA_HANDLERS_COMPLETE_ANALYSIS.md) - Comprehensive analysis of all three Lambda handlers (15,000+ lines of code)

### Reference Documentation
- [API Endpoints Reference](docs/reference/API_ENDPOINTS_CURRENT.md) - Complete API endpoint documentation (58 endpoints)
- [Orchestration Role Specification](docs/reference/ORCHESTRATION_ROLE_SPECIFICATION.md) - IAM role requirements
- [DRS IAM and Permissions Reference](docs/reference/DRS_IAM_AND_PERMISSIONS_REFERENCE.md) - Comprehensive IAM policy analysis
- [DRS Service Limits and Capabilities](docs/reference/DRS_SERVICE_LIMITS_AND_CAPABILITIES.md) - Service quotas and constraints
- [DRS Cross-Account Reference](docs/reference/DRS_CROSS_ACCOUNT_REFERENCE.md) - Multi-account configuration
- [DRS Launch Configuration Reference](docs/reference/DRS_LAUNCH_CONFIGURATION_REFERENCE.md) - Launch template management
- [DR Wave Priority Mapping](docs/reference/DR_WAVE_PRIORITY_MAPPING.md) - Wave and priority assignment strategy

### Troubleshooting
- [Deployment Troubleshooting Guide](docs/troubleshooting/DEPLOYMENT_TROUBLESHOOTING_GUIDE.md) - Common deployment issues
- [DRS Execution Troubleshooting Guide](docs/troubleshooting/DRS_EXECUTION_TROUBLESHOOTING_GUIDE.md) - Recovery execution debugging
- [Authentication Issues](docs/troubleshooting/AUTHENTICATION_ISSUES.md) - Cognito and API Gateway troubleshooting
- [Known Issues](docs/troubleshooting/KNOWN_ISSUES.md) - Current known issues and workarounds

## CI/CD Pipeline

The project uses CloudFormation for infrastructure deployment with comprehensive validation and security scanning capabilities.

### CloudFormation Deployment

Deploy the complete solution using AWS CloudFormation:

```bash
# Full deployment
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name aws-drs-orchestration-dev \
  --parameter-overrides \
    ProjectName=aws-drs-orchestration \
    Environment=dev \
    SourceBucket=aws-drs-orchestration-dev \
    AdminEmail=your-email@example.com \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### Built-in Protections

The CloudFormation templates include automatic safety checks:

- **Stack Protection**: Termination protection on production stacks
- **Encryption**: All data encrypted at rest and in transit
- **IAM Policies**: Least-privilege access controls
- **Resource Tagging**: Consistent tagging for cost allocation and governance

## Documentation

### API Reference

Complete API documentation for all Lambda handlers with direct invocation support:

- **[Query Handler API](docs/api-reference/QUERY_HANDLER_API.md)** - 18 read-only operations
  - List protection groups, recovery plans, executions
  - Get DRS source servers, jobs, recovery instances
  - Discover staging accounts and extended source servers
  - Query execution history and audit logs

- **[Data Management Handler API](docs/api-reference/DATA_MANAGEMENT_HANDLER_API.md)** - 18 CRUD operations
  - Create, update, delete protection groups
  - Create, update, delete recovery plans
  - Manage target accounts and staging accounts
  - Configure launch templates and per-server settings

- **[Execution Handler API](docs/api-reference/EXECUTION_HANDLER_API.md)** - 8 execution control operations
  - Start recovery executions
  - Resume, cancel, terminate executions
  - Get execution status and details
  - Manage execution lifecycle

### IAM & Security

- **[Orchestration Role Policy](docs/iam/ORCHESTRATION_ROLE_POLICY.md)** - Complete IAM policy specification
  - 16 policy statements with detailed permissions
  - DRS, EC2, Step Functions, DynamoDB, SNS, CloudWatch access
  - Cross-account role assumption patterns
  - External role integration guidance

### Migration & Troubleshooting

- **[Migration Guide](docs/guides/MIGRATION_GUIDE.md)** - Comprehensive migration procedures
  - API Gateway to Direct Lambda invocation migration
  - Cost analysis and comparison ($12-40/month vs $8-30/month)
  - Step-by-step migration procedures
  - Rollback procedures and testing strategies

- **[Error Codes Reference](docs/troubleshooting/ERROR_CODES.md)** - 13 error codes with troubleshooting
  - VALIDATION_ERROR, RESOURCE_NOT_FOUND, CONFLICT_ERROR
  - DRS_SERVICE_ERROR, EXECUTION_ERROR, AUTHORIZATION_ERROR
  - Detailed troubleshooting steps for each error type

### Integration Examples

Complete working examples for AWS service integration:

#### Python & Bash Scripts
- **[Python Example](examples/python/complete_dr_workflow.py)** - Complete DR workflow automation
  - Create protection groups and recovery plans
  - Start recovery execution with monitoring
  - Error handling and retry logic
  - IAM policy included

- **[Bash Example](examples/bash/dr_ci_pipeline.sh)** - CI/CD pipeline integration
  - Automated DR testing in CI/CD pipelines
  - Pre-deployment validation
  - Post-deployment verification
  - Exit code handling for pipeline integration

#### AWS CDK Examples
- **[CDK Stack](examples/cdk/)** - Complete TypeScript CDK stack
  - Lambda function definitions with direct invocation
  - DynamoDB table integration
  - Step Functions state machine
  - IAM role configuration

- **[DynamoDB Integration](examples/cdk/docs/DYNAMODB_INTEGRATION.md)** - DynamoDB patterns
  - Table schema and GSI configuration
  - Query and scan patterns
  - Batch operations and transactions
  - Error handling and retries

- **[Step Functions Integration](examples/cdk/docs/STEPFUNCTIONS_INTEGRATION.md)** - State machine patterns
  - Lambda invocation from Step Functions
  - Error handling and retries
  - Parallel execution patterns
  - Wait states and callbacks

- **[IAM Role Integration](examples/cdk/docs/IAM_ROLE_INTEGRATION.md)** - IAM configuration (1600+ lines)
  - Complete role and policy definitions
  - Cross-account access patterns
  - Service-specific permissions
  - Security best practices

#### AWS Service Integration
- **[Step Functions Example](examples/stepfunctions/)** - Lambda invocation patterns
  - Complete state machine definition
  - Task states with Lambda invocation
  - Error handling and retries
  - Parallel and sequential execution

- **[EventBridge Example](examples/eventbridge/)** - Event-driven invocation
  - 8 EventBridge rule definitions
  - Scheduled invocation (cron, rate)
  - Event pattern matching
  - Target configuration with input transformation

### Additional Guides

- **[Deployment Flexibility Guide](docs/guides/DEPLOYMENT_FLEXIBILITY_GUIDE.md)** - Deployment modes and configuration
- **[Developer Guide](docs/guides/DEVELOPER_GUIDE.md)** - Local development setup and workflows
- **[DRS Cross-Account Setup](docs/guides/DRS_CROSS_ACCOUNT_SETUP_VERIFICATION.md)** - Multi-account configuration

## Contributing

1. **Clone the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make changes and test locally**
4. **Commit changes** (`git commit -m 'Add amazing feature'`)
5. **Push to remote** (`git push origin feature/amazing-feature`)
6. **Open a Pull Request**

### Local Development

```bash
# Clone repository
git clone https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git
cd aws-elasticdrs-orchestrator

# Setup Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Frontend development
cd frontend
npm install
npm run dev  # Development server at localhost:5173

# CloudFormation deployment
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name aws-drs-orchestration-dev \
  --parameter-overrides \
    ProjectName=aws-drs-orchestration \
    Environment=dev \
    SourceBucket=aws-drs-orchestration-dev \
    AdminEmail=your-email@example.com \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
```

## Upcoming Features

### DRS AllowLaunchingIntoThisInstance Pattern

A comprehensive implementation of AWS DRS AllowLaunchingIntoThisInstance pattern that enables launching recovery instances into pre-provisioned EC2 instances, preserving instance identity (instance ID, private IP, network configuration) through complete disaster recovery cycles.

**Key Benefits**:
- **88-92% RTO Reduction**: Target RTO <30 minutes for 100 instances (vs 2-4 hours with standard DRS)
- **Instance Identity Preservation**: Maintains instance ID, private IP, and network configuration through failover/failback
- **Zero DNS Changes**: Eliminates need for DNS updates and application reconfiguration during failback
- **True Round-Trip DR**: Enables complete failover + failback to original instances

**Architecture**:
- Integrates with 3 existing Lambda handlers (data-management, execution, query)
- 4 new shared modules: instance_matcher, drs_client, drs_job_monitor, drs_error_handler
- 3 DynamoDB tables for configuration and state tracking
- 15+ new API Gateway endpoints
- Dual invocation pattern support (API Gateway + Direct Lambda)

**Test Coverage**: 104 tests planned (59 unit + 37 integration + 8 E2E)

## Directory Structure

```text
aws-elasticdrs-orchestrator/
├── cfn/                          # CloudFormation IaC (16 templates)
│   ├── master-template.yaml      # Root orchestrator for nested stacks
│   └── github-oidc-stack.yaml    # OIDC integration (optional)
├── frontend/                     # React + CloudScape UI (32+ components)
│   ├── src/                      # Source code
│   ├── public/                   # Static assets
│   └── package.json              # Dependencies
├── lambda/                       # Python Lambda functions (6 handlers + shared utilities)
│   ├── data-management-handler/  # Protection groups, recovery plans CRUD
│   ├── execution-handler/        # Recovery execution control
│   ├── query-handler/            # Read-only queries, DRS status
│   ├── orchestration-stepfunctions/  # Step Functions orchestration
│   ├── frontend-deployer/        # Frontend deployment automation
│   ├── notification-formatter/   # SNS notification formatting
│   └── shared/                   # Shared utilities (RBAC, DRS, security)
├── docs/                         # Comprehensive documentation
│   ├── guides/                   # User guides and walkthroughs
│   ├── reference/                # API and technical reference
│   ├── architecture/             # Architecture diagrams and docs
│   ├── deployment/               # Deployment guides
│   ├── requirements/             # Product and software requirements
│   └── troubleshooting/          # Troubleshooting guides
├── tests/                        # Test suites (unit, integration, E2E)
│   ├── unit/                     # Unit tests with property-based testing
│   ├── integration/              # Integration tests
│   └── e2e/                      # End-to-end tests
├── archive/                      # Historical reference materials
├── mise.toml                     # Tool version management
├── pyproject.toml                # Python project configuration
├── requirements-dev.txt          # Python development dependencies
└── README.md                     # This file
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/johnjcousens/aws-elasticdrs-orchestrator/issues)
- **Documentation**: [docs/](docs/)
- **Discussions**: [GitHub Discussions](https://github.com/johnjcousens/aws-elasticdrs-orchestrator/discussions)

---

**Built for disaster recovery on AWS**
