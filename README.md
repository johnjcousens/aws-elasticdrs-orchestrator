# AWS DRS Orchestration Solution

Enterprise-grade disaster recovery orchestration for AWS Elastic Disaster Recovery (DRS) with wave-based execution, dependency management, and automated health checks.

[![AWS](https://img.shields.io/badge/AWS-DRS-FF9900?logo=amazonaws)](https://aws.amazon.com/disaster-recovery/)
[![CloudFormation](https://img.shields.io/badge/IaC-CloudFormation-232F3E?logo=amazonaws)](cfn/)
[![React](https://img.shields.io/badge/Frontend-React%2019-61DAFB?logo=react)](frontend/)
[![Python](https://img.shields.io/badge/Backend-Python%203.12-3776AB?logo=python)](lambda/)
[![Release](https://img.shields.io/badge/Release-Multi--Account%20Prototype%201.0-brightgreen)](https://github.com/your-repo/releases/tag/v1.0.0-multi-account-prototype)

## 🎉 **Multi-Account Prototype 1.0 Released!**

**Latest Release**: [v1.7.0 - Multi-Account Prototype 1.0](CHANGELOG.md#170---december-17-2025) (December 17, 2025)  
**Git Tag**: `v1.0.0-multi-account-prototype`

### 🚀 **What's New**

- **Multi-Account Management**: Complete account management system with enforcement and auto-selection
- **Enhanced Tag-Based Selection**: Fixed DRS source server tag querying with full hardware details
- **Account Selector**: Intuitive account switching in top navigation
- **Settings Integration**: Default account preferences in existing 3-tab settings panel
- **Production Ready**: All artifacts deployed to S3 and ready for CloudFormation deployment

### 🎯 **Key Achievements**

- **23 files changed**: 1,421 insertions, 515 deletions
- **Complete testing**: Tag selection with us-west-2 DRS servers validated
- **Backward compatible**: No breaking changes to existing functionality
- **Enterprise scale**: Foundation for managing DRS across multiple AWS accounts

**[View Complete Release Notes →](CHANGELOG.md#170---december-17-2025)**

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
- **Clean UX** 🆕: Removed confusing non-functional checkboxes from tag preview for cleaner interface

### Recovery Plans

- **Wave-Based Orchestration**: Define multi-wave recovery sequences with unlimited flexibility
- **Dependency Management**: Automatic wave dependency handling with circular dependency detection
- **Drill Mode**: Test recovery procedures without impacting production
- **Automation Hooks**: Pre-wave and post-wave actions for validation and health checks

### Execution Monitoring

- **Real-Time Dashboard**: Live execution progress with wave-level status tracking
- **Invocation Source Tracking**: Track execution origin (UI, CLI, API, EVENTBRIDGE, SSM, STEPFUNCTIONS)
- **Pause/Resume Control**: Pause executions between waves for validation and resume when ready
- **Instance Termination**: Terminate recovery instances after successful testing
- **DRS Job Events**: Real-time DRS job event monitoring with 3-second auto-refresh and collapsible view
- **Loading State Management**: Prevents multiple button clicks during operations with visual feedback
- **Execution History**: Complete audit trail of all recovery executions with source badges
- **CloudWatch Integration**: Deep-link to CloudWatch Logs for troubleshooting
- **Auto-Refresh**: All pages auto-refresh (30s for lists, 3-5s for active executions)
- **Existing Instance Detection**: Pre-drill check warns about existing recovery instances with source plan tracking
- **Instance Details**: Shows EC2 name, IP, instance type, and launch time for existing instances

### EC2 Launch Configuration

- **Launch Template Management**: Configure EC2 launch settings per Protection Group
- **Complete Instance Type Support** 🆕: Access to ALL available EC2 instance types supported by DRS in each region (968+ types including modern families like m6a, m7i, c7g, r7i, and all current-generation instances)
- **Network Configuration**: Select subnets and security groups for recovery
- **IAM Instance Profiles**: Assign instance profiles to recovery instances
- **DRS Launch Settings**:
  - **Instance Type Right Sizing**: BASIC (DRS selects), IN_AWS (periodic updates), or NONE (use template)
  - **Launch Disposition**: Start instance automatically (STARTED) or keep stopped (STOPPED)
  - **Copy Private IP**: Preserve source server's private IP address
  - **Transfer Server Tags**: Copy source server tags to recovery instance
  - **OS Licensing**: BYOL (Bring Your Own License) or AWS-provided license
- **Automatic Application**: Settings applied to all servers in Protection Group on save

### Configuration Export/Import

- **Full Backup**: Export all Protection Groups and Recovery Plans to JSON file
- **Portable Format**: Uses `ProtectionGroupName` instead of IDs for cross-environment portability
- **Non-Destructive Import**: Additive-only import skips existing resources by name
- **Name Resolution**: Automatically resolves Protection Group names to IDs during import
- **Dry Run Mode**: Validate import without making changes
- **Server Validation**: Verifies DRS source servers exist before import
- **Tag Validation**: Confirms tag-based selections resolve to servers
- **Cascade Handling**: Reports Recovery Plan failures when Protection Groups fail
- **Settings Modal**: Access via gear icon in top navigation bar

### API & Integration

- **Optimistic Locking**: Version-based concurrency control prevents conflicting updates
- **Comprehensive Error Handling**: Standardized error codes (MISSING_FIELD, INVALID_NAME, VERSION_CONFLICT, etc.)
- **Health Endpoint**: `/health` endpoint for monitoring and load balancer health checks
- **Config Export/Import**: `GET /config/export` and `POST /config/import` endpoints
- **51 API Tests**: Full test coverage for all API operations

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
  --output text \
  --profile your-aws-profile)

aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username admin@yourcompany.com \
  --user-attributes Name=email,Value=admin@yourcompany.com Name=email_verified,Value=true \
  --temporary-password "TempPass123!" \
  --message-action SUPPRESS \
  --profile your-aws-profile

aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username admin@yourcompany.com \
  --password "YourSecurePassword123!" \
  --permanent \
  --profile your-aws-profile
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

## API Reference

### Authentication

All API requests require a valid Cognito JWT token:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://your-api-endpoint.execute-api.us-east-1.amazonaws.com/prod/protection-groups
```

### Core Endpoints

#### Protection Groups

| Method | Endpoint                         | Description                           |
| ------ | -------------------------------- | ------------------------------------- |
| GET    | `/protection-groups`           | List all protection groups            |
| POST   | `/protection-groups`           | Create protection group               |
| GET    | `/protection-groups/{id}`      | Get protection group details          |
| PUT    | `/protection-groups/{id}`      | Update protection group               |
| DELETE | `/protection-groups/{id}`      | Delete protection group               |
| POST   | `/protection-groups/resolve`   | Preview servers matching tags         |

#### Recovery Plans

| Method | Endpoint                                      | Description                           |
| ------ | --------------------------------------------- | ------------------------------------- |
| GET    | `/recovery-plans`                           | List all recovery plans               |
| POST   | `/recovery-plans`                           | Create recovery plan                  |
| GET    | `/recovery-plans/{id}`                      | Get recovery plan details             |
| PUT    | `/recovery-plans/{id}`                      | Update recovery plan                  |
| DELETE | `/recovery-plans/{id}`                      | Delete recovery plan                  |
| POST   | `/recovery-plans/{id}/execute`              | Execute recovery plan                 |
| GET    | `/recovery-plans/{id}/check-existing-instances` | Check for existing recovery instances |

#### Executions

| Method | Endpoint                                 | Description                           |
| ------ | ---------------------------------------- | ------------------------------------- |
| GET    | `/executions`                          | List execution history                |
| POST   | `/executions`                          | Start new execution                   |
| GET    | `/executions/{id}`                     | Get execution details                 |
| POST   | `/executions/{id}/pause`               | Pause execution between waves         |
| POST   | `/executions/{id}/resume`              | Resume paused execution               |
| POST   | `/executions/{id}/cancel`              | Cancel running execution              |
| POST   | `/executions/{id}/terminate-instances` | Terminate recovery instances          |
| GET    | `/executions/{id}/job-logs`            | Get DRS job logs for execution        |
| DELETE | `/executions`                          | Delete completed executions (bulk)    |

### DRS Integration

#### DRS Source Servers

| Method | Endpoint                                | Description                              |
| ------ | --------------------------------------- | ---------------------------------------- |
| GET    | `/drs/source-servers?region={region}` | Discover DRS source servers              |
| GET    | `/drs/quotas?region={region}`         | Get DRS service quotas (region required) |
| GET    | `/drs/accounts?region={region}`       | Get DRS account information              |
| POST   | `/drs/tag-sync`                       | Sync EC2 tags to DRS source servers     |

#### EC2 Resources (for Launch Config)

| Method | Endpoint                                   | Description                       |
| ------ | ------------------------------------------ | --------------------------------- |
| GET    | `/ec2/subnets?region={region}`           | List VPC subnets for dropdown     |
| GET    | `/ec2/security-groups?region={region}`   | List security groups for dropdown |
| GET    | `/ec2/instance-profiles?region={region}` | List IAM instance profiles        |
| GET    | `/ec2/instance-types?region={region}`    | List EC2 instance types           |

### Multi-Account Management

#### Target Accounts

| Method | Endpoint                    | Description                    |
| ------ | --------------------------- | ------------------------------ |
| GET    | `/accounts/targets`       | List target accounts           |
| POST   | `/accounts/targets`       | Add target account             |
| PUT    | `/accounts/targets/{id}`  | Update target account          |
| DELETE | `/accounts/targets/{id}`  | Remove target account          |

### Configuration Management

#### Config Export/Import

| Method | Endpoint           | Description                           |
| ------ | ------------------ | ------------------------------------- |
| GET    | `/config/export` | Export all Protection Groups and Plans |
| POST   | `/config/import` | Import Protection Groups and Plans     |

#### Health Check

| Method | Endpoint    | Description                   |
| ------ | ----------- | ----------------------------- |
| GET    | `/health` | Service health check endpoint |

### Request/Response Examples

#### Create Protection Group with Tag-Based Selection

```bash
curl -X POST "${API_ENDPOINT}/protection-groups" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "GroupName": "Database-Servers",
    "Region": "us-east-1",
    "ServerSelectionTags": {
      "DR-Application": "HRP",
      "DR-Tier": "Database"
    },
    "LaunchConfig": {
      "SubnetId": "subnet-12345678",
      "SecurityGroupIds": ["sg-12345678"],
      "InstanceType": "r5.xlarge",
      "CopyPrivateIp": true,
      "CopyTags": true,
      "Licensing": {"osByol": false},
      "TargetInstanceTypeRightSizingMethod": "BASIC",
      "LaunchDisposition": "STARTED"
    }
  }'
```

#### Preview Servers Matching Tags

```bash
curl -X POST "${API_ENDPOINT}/protection-groups/resolve" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "region": "us-east-1",
    "ServerSelectionTags": {
      "DR-Application": "HRP",
      "DR-Tier": "Database"
    }
  }'
```

#### Create Recovery Plan with Multi-Wave Configuration

```bash
curl -X POST "${API_ENDPOINT}/recovery-plans" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "PlanName": "Multi-Tier-Application",
    "Description": "3-tier application recovery",
    "Waves": [
      {
        "WaveName": "Database Tier",
        "WaveNumber": 1,
        "ProtectionGroupId": "pg-database-uuid",
        "PauseBeforeWave": false
      },
      {
        "WaveName": "Application Tier",
        "WaveNumber": 2,
        "ProtectionGroupId": "pg-application-uuid",
        "PauseBeforeWave": true,
        "DependsOn": [1]
      },
      {
        "WaveName": "Web Tier",
        "WaveNumber": 3,
        "ProtectionGroupId": "pg-web-uuid",
        "PauseBeforeWave": false,
        "DependsOn": [2]
      }
    ]
  }'
```

#### Start Drill Execution

```bash
curl -X POST "${API_ENDPOINT}/executions" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "PlanId": "plan-uuid-here",
    "ExecutionType": "DRILL",
    "InitiatedBy": "cli-automation"
  }'
```

#### Pause Execution

```bash
curl -X POST "${API_ENDPOINT}/executions/{execution-id}/pause" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json"
```

#### Resume Paused Execution

```bash
curl -X POST "${API_ENDPOINT}/executions/{execution-id}/resume" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json"
```

#### Terminate Recovery Instances

```bash
curl -X POST "${API_ENDPOINT}/executions/{execution-id}/terminate-instances" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json"
```

#### Get DRS Service Quotas

```bash
curl -X GET "${API_ENDPOINT}/drs/quotas?region=us-east-1" \
  -H "Authorization: Bearer ${TOKEN}"
```

#### Export Configuration

```bash
curl -X GET "${API_ENDPOINT}/config/export" \
  -H "Authorization: Bearer ${TOKEN}" \
  -o drs-orchestration-config.json
```

#### Import Configuration

```bash
curl -X POST "${API_ENDPOINT}/config/import" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d @drs-orchestration-config.json
```

### Query Parameters

#### List Protection Groups
- `accountId`: Filter by target account ID

#### List Recovery Plans
- `accountId`: Filter by target account ID
- `name`: Filter by plan name (partial match)
- `nameExact`: Filter by exact plan name
- `tag`: Filter by tag key=value
- `hasConflict`: Filter by conflict status (true/false)
- `status`: Filter by last execution status

#### List Executions
- `limit`: Number of results (max 100)
- `nextToken`: Pagination token
- `accountId`: Filter by target account ID

#### DRS Source Servers
- `region`: AWS region (required)
- `accountId`: Target account ID

### Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `MISSING_FIELD` | Required field missing | 400 |
| `INVALID_NAME` | Name validation failed | 400 |
| `PG_NAME_EXISTS` | Protection Group name exists | 409 |
| `RP_NAME_EXISTS` | Recovery Plan name exists | 409 |
| `VERSION_CONFLICT` | Optimistic locking conflict | 409 |
| `SERVER_CONFLICT` | Server already assigned | 409 |
| `TAG_CONFLICT` | Tags already in use | 409 |
| `PLAN_ALREADY_EXECUTING` | Plan has active execution | 409 |
| `EXECUTION_NOT_FOUND` | Execution not found | 404 |
| `WAVE_SIZE_LIMIT_EXCEEDED` | Wave exceeds 100 servers | 400 |
| `CONCURRENT_JOBS_LIMIT_EXCEEDED` | DRS job limit reached | 429 |
| `UNHEALTHY_SERVER_REPLICATION` | Server replication unhealthy | 400 |

### Response Format

All API responses follow this structure:

```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*"
  },
  "body": {
    // Response data in camelCase format
  }
}
```

### Data Formats

- **Timestamps**: Unix timestamps in seconds
- **UUIDs**: Standard UUID format for IDs
- **Field Names**: camelCase in responses, PascalCase in DynamoDB
- **Status Values**: UPPERCASE strings
- **Regions**: AWS region codes (e.g., "us-east-1")

For complete API documentation including all endpoints, request/response examples, error codes, and integration patterns (CLI, SSM, Step Functions, EventBridge, Python SDK), see the [Orchestration Integration Guide](docs/guides/ORCHESTRATION_INTEGRATION_GUIDE.md).

## Infrastructure

### CloudFormation Stacks

The solution uses a modular nested stack architecture for maintainability:

| Stack                         | Purpose             | Key Resources                     |
| ----------------------------- | ------------------- | --------------------------------- |
| `master-template.yaml`      | Root orchestrator   | Parameter propagation, outputs    |
| `database-stack.yaml`       | Data persistence    | 3 DynamoDB tables with encryption |
| `lambda-stack.yaml`         | Compute layer       | 5 Lambda functions, IAM roles     |
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

## Development

### Deployment Workflow

**Primary deployment script** for all code changes:

```bash
# Sync all code to S3 deployment bucket
./scripts/sync-to-deployment-bucket.sh

# Fast Lambda updates (~5 seconds)
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# Full CloudFormation deployment (5-10 minutes)
./scripts/sync-to-deployment-bucket.sh --deploy-cfn

# Build and deploy frontend
./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-frontend

# Preview changes without deploying
./scripts/sync-to-deployment-bucket.sh --dry-run
```

**CRITICAL**: Always sync to S3 before deployment. The S3 bucket is the source of truth for all deployments.

#### Stack Configuration

The deployment script has been updated to use the correct stack name:

- **Stack Name**: `drs-orch-v4` (not `drs-orchestration-dev`)
- **Lambda Functions**: `drsorchv4-*-test` naming pattern
- **Frontend Bucket**: `drsorchv4-fe-***REMOVED***-test`
- **CloudFront Distribution**: `***REMOVED***`

#### Deployment Verification

After deployment, verify the correct resources are updated:

```bash
# Check CloudFront URL matches your environment
aws cloudformation describe-stacks \
  --stack-name drs-orch-v4 \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
  --output text

# Verify Lambda function was updated
aws lambda get-function \
  --function-name drsorchv4-api-handler-test \
  --query 'Configuration.LastModified' \
  --output text

# Check frontend bucket sync
aws s3 ls s3://drsorchv4-fe-***REMOVED***-test/assets/ | head -5
```

#### Recent Updates

**December 17, 2025**: **Complete EC2 Instance Type Support Enhancement** - Enhanced EC2 Launch Configuration to display ALL available instance types supported by DRS in each region (968+ types for us-west-2). Users can now select from the complete range of modern instance families including m6a, m7i, c7g, r7i, and all other current-generation types. Resolved browser caching issues that previously limited selection to a small subset of common instances.

**December 17, 2025**: **Multi-Account Prototype 1.0 Released** - Complete multi-account management system with enhanced tag-based server selection. All artifacts synced to S3 deployment bucket and ready for production deployment using master CloudFormation template. See [v1.7.0 Release Notes](CHANGELOG.md#170---december-17-2025) for complete details.

**December 16, 2025**: Enhanced DRS Source Server Display with detailed hardware information in Protection Group creation. The server discovery panel now shows comprehensive hardware details including CPU cores, RAM (GiB), and IP address in a clean format: "FQDN | CPU: X cores | RAM: X GiB | IP: X.X.X.X". Backend Lambda extracts hardware info from DRS source server metadata and EC2 instance details.

**December 15, 2025**: Updated deployment scripts to use correct stack name `drs-orch-v4` instead of `drs-orchestration-dev`. This resolves deployment mismatches where code was being deployed to the wrong CloudFormation stack and CloudFront distribution.

### Frontend Development

```bash
cd frontend
npm install
npm run dev      # Development server at localhost:5173
npm run build    # Production build
npm run lint     # ESLint validation
```

### Frontend Testing

Unit tests for frontend services using Vitest:

```bash
cd frontend
npm run test           # Run all tests once
npm run test:watch     # Run tests in watch mode
npm run test:coverage  # Run tests with coverage report
```

Tests validate DRS service limits and quota handling without requiring actual DRS infrastructure. See [Frontend Tests](frontend/src/services/__tests__/drsQuotaService.test.ts).

### Backend Testing

Python unit tests for Lambda validation functions using pytest with mocked boto3:

```bash
cd tests/python
pip install -r requirements.txt
python -m pytest unit/test_drs_service_limits.py -v
```

Tests validate DRS service limits validation logic with mocked AWS API responses. See [Backend Tests](tests/python/unit/test_drs_service_limits.py).

### Lambda Development

```bash
cd lambda
pip install -r requirements.txt

# Use sync script for deployment (recommended)
./scripts/sync-to-deployment-bucket.sh --update-lambda-code
```

### Validate CloudFormation

```bash
make validate    # AWS validate-template
make lint        # cfn-lint validation
```

## Troubleshooting

### Common Issues

| Issue                     | Cause                           | Solution                                                |
| ------------------------- | ------------------------------- | ------------------------------------------------------- |
| `PG_NAME_EXISTS`        | Duplicate protection group name | Use a unique name                                       |
| `INVALID_SERVER_IDS`    | Server IDs not found in DRS     | Verify servers with `aws drs describe-source-servers` |
| `CIRCULAR_DEPENDENCY`   | Wave dependencies form a loop   | Review and fix dependency chain                         |
| `EXECUTION_IN_PROGRESS` | Plan already executing          | Wait for completion or cancel                           |

### DRS Recovery Failures

If recovery jobs fail with `UnauthorizedOperation` errors, verify the OrchestrationRole has required EC2 and DRS permissions. See [DRS IAM Analysis](docs/reference/DRS_COMPLETE_IAM_ANALYSIS.md) for complete permission requirements.

## Documentation

### Quick Links

| Document                                                                 | Description                                   |
| ------------------------------------------------------------------------ | --------------------------------------------- |
| [Product Requirements](docs/requirements/PRODUCT_REQUIREMENTS_DOCUMENT.md)  | Complete PRD with features and specifications |
| [Deployment Guide](docs/guides/DEPLOYMENT_AND_OPERATIONS_GUIDE.md)          | Step-by-step deployment instructions          |
| [Multi-Account Setup Guide](MULTI_ACCOUNT_SETUP_GUIDE.md) 🆕               | Complete multi-account hub and spoke setup    |
| [Multi-Account Implementation Status](MULTI_ACCOUNT_IMPLEMENTATION_STATUS.md) 🆕 | Implementation status and bug fixes |
| [Orchestration Integration](docs/guides/ORCHESTRATION_INTEGRATION_GUIDE.md) | CLI, SSM, Step Functions, API integration     |
| [Architecture Design](docs/architecture/ARCHITECTURAL_DESIGN_DOCUMENT.md)   | System architecture and design decisions      |
| [API Reference](docs/guides/AWS_DRS_API_REFERENCE.md)                       | DRS API integration patterns                  |
| [Testing Guide](docs/guides/TESTING_AND_QUALITY_ASSURANCE.md)               | Testing procedures and quality assurance      |

### Documentation Index

See [Appendix: Complete Documentation Index](#appendix-complete-documentation-index) for full documentation catalog with detailed descriptions.

## Agentic AI Coding

### Amazon Q Developer Integration

This repository includes comprehensive configuration for Amazon Q Developer to enable advanced agentic AI coding capabilities:

#### Amazon Q Rules & Memory Bank

| Document                                                                    | Purpose                                        |
| --------------------------------------------------------------------------- | ---------------------------------------------- |
| [CI/CD &amp; IaC Workflow](.amazonq/rules/cicd-iac-workflow.md)                | Enforce proper Infrastructure as Code workflow |
| [Deployment Verification](.amazonq/rules/deployment-verification.md)           | Verify deployment can be reproduced            |
| [Frontend Design Consistency](.amazonq/rules/frontend-design-consistency.md)   | AWS CloudScape design system rules             |
| [Kiro Steering Alignment](.amazonq/rules/kiro-steering-alignment.md)           | Complete project guidance alignment            |
| [Update Requirements Workflow](.amazonq/rules/update-requirements-workflow.md) | Automated documentation sync workflow          |
| [Development Guidelines](.amazonq/rules/memory-bank/guidelines.md)             | Code quality standards and patterns            |
| [Product Overview](.amazonq/rules/memory-bank/product.md)                      | Business context and features                  |
| [Project Structure](.amazonq/rules/memory-bank/structure.md)                   | Repository organization                        |
| [Technology Stack](.amazonq/rules/memory-bank/tech.md)                         | Complete tech stack reference                  |

#### Kiro Steering Documents

| Document                                                                        | Purpose                                                                                   |
| ------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| [Product Overview](.kiro/steering/product.md)                                      | Business problem, solution overview, and features                                         |
| [Project Structure](.kiro/steering/structure.md)                                   | Repository organization and component architecture                                        |
| [Technology Stack](.kiro/steering/tech.md)                                         | Complete technology stack and development commands                                        |
| [CI/CD Guide](.kiro/steering/cicd.md)                                              | Deployment architecture and GitLab pipeline                                               |
| [Frontend Design Consistency](.kiro/steering/frontend-design-consistency.md)       | AWS CloudScape design system rules                                                        |
| [Debugging Rules](.kiro/steering/debugging-rules.md)                               | DRS integration and troubleshooting guide                                                 |
| [CloudScape Best Practices](.kiro/steering/cloudscape-best-practices.md)           | CloudScape component usage and patterns                                                   |
| [CloudScape Component Reference](.kiro/steering/cloudscape-component-reference.md) | Quick reference for CloudScape components                                                 |
| [Terminal Rules](.kiro/steering/terminal-rules.md)                                 | Terminal output suppression and connection guidelines                                     |
| [File Writing Rules](.kiro/steering/file-writing.md)                               | File creation and editing guidelines                                                      |
| [Update Requirements Workflow](.kiro/steering/update-requirements-workflow.md)     | Automated documentation sync workflow (trigger: "update docs", "align docs", "sync docs") |

#### Key Benefits

- **Consistent Development**: Enforces AWS CloudScape design patterns
- **Automated Workflows**: CI/CD and deployment verification rules
- **Documentation Sync**: Automated requirements document alignment
- **Context Awareness**: Complete project understanding for AI assistance
- **Quality Assurance**: Built-in code quality and architectural guidance

### Usage with Amazon Q Developer

1. **Install Amazon Q Developer** in your IDE
2. **Open the repository** - Amazon Q will automatically load project rules
3. **Use natural language** to request features, fixes, or documentation updates
4. **Leverage workflows** - Say "update requirements documents" to trigger automated sync
5. **Follow guidance** - Amazon Q enforces CloudScape patterns and deployment workflows

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Repository Snapshots & Rollback

The repository uses Git tags to mark significant milestones. These tags capture the complete state of all files and can be used to rollback the entire repository.

### Available Tags

| Tag                                | Description                                                               | Date              |
| ---------------------------------- | ------------------------------------------------------------------------- | ----------------- |
| `v1.0.0-multi-account-prototype` | **Multi-Account Prototype 1.0** - Complete multi-account management system with enhanced tag-based selection | December 17, 2025 |
| `mvp-demo-ready`                 | MVP Demo Ready - Complete working state with all core features functional | December 9, 2025  |
| `future-plans-v1`                | All future implementation plans documented                                | December 9, 2025  |

### View All Tags

```bash
# List all tags with descriptions
git tag -l -n1

# Show detailed tag information
git show mvp-demo-ready
```

### Rollback Entire Repository to a Tag

**Option 1: Checkout tag (detached HEAD - read-only exploration)**

```bash
# View the repository at the tagged state
git checkout mvp-demo-ready

# Return to main branch when done
git checkout main
```

**Option 2: Create a new branch from tag (for development)**

```bash
# Create a new branch starting from the tagged state
git checkout -b my-feature-branch mvp-demo-ready
```

**Option 3: Hard reset main branch to tag (⚠️ DESTRUCTIVE)**

```bash
# WARNING: This discards all commits after the tag
git checkout main
git reset --hard mvp-demo-ready

# If you need to push the reset (force push required)
git push --force origin main
```

**Option 4: Revert to tag state while preserving history**

```bash
# Create a new commit that reverts to the tagged state
git checkout main
git revert --no-commit HEAD..mvp-demo-ready
git commit -m "Revert to mvp-demo-ready state"
```

### Best Practices

- **Before major changes**: Create a new tag to mark the stable state
- **After successful demos**: Tag the repository for easy reference
- **Use descriptive tag names**: Include version or milestone info (e.g., `v1.0-release`, `pre-refactor`)

### Create a New Tag

```bash
# Create annotated tag (recommended)
git tag -a my-tag-name -m "Description of this milestone"

# Push tag to remote
git push origin my-tag-name

# Push all tags
git push origin --tags
```

---

## Appendix: Complete Documentation Index

### Requirements & Planning (Source of Truth)

These documents are the **authoritative source** for all system specifications. When conflicts exist between other documentation and requirements documents, the requirements documents take precedence.

| Document                                                                                     | Description                                                                         |
| -------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| [Product Requirements Document](docs/requirements/PRODUCT_REQUIREMENTS_DOCUMENT.md)             | Complete PRD with problem statement, features, technical specs, and success metrics |
| [Software Requirements Specification](docs/requirements/SOFTWARE_REQUIREMENTS_SPECIFICATION.md) | Functional requirements, API contracts, validation rules                            |
| [UX/UI Design Specifications](docs/requirements/UX_UI_DESIGN_SPECIFICATIONS.md)                 | Component specs (23 MVP + 9 Phase 2), user flows, accessibility                     |

### Architecture & Design

| Document                                                                                | Description                                                                         |
| --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| [Architecture Diagrams](docs/architecture/ARCHITECTURE_DIAGRAMS.md)                        | **Visual reference** - Complete mermaid diagrams for all components and flows |
| [Architectural Design Document](docs/architecture/ARCHITECTURAL_DESIGN_DOCUMENT.md)        | System architecture, component design, and technology decisions                     |
| [Step Functions Analysis](docs/architecture/STEP_FUNCTIONS_ANALYSIS.md)                    | Orchestration engine design and state machine patterns                              |
| [DRS Coordination Patterns](docs/architecture/DRS_STEP_FUNCTIONS_COORDINATION_ANALYSIS.md) | Wave-based execution and DRS job coordination                                       |
| [AWS Services Deep Dive](docs/architecture/AWS_SERVICES_ARCHITECTURE_DEEP_DIVE.md)         | Detailed analysis of AWS services used in the solution                              |

### Core Reference Documents

| Document                                                     | Description                                                                                   |
| ------------------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| [Product Overview](.kiro/steering/product.md)                   | **Core reference** - Business problem, solution overview, features, and success metrics |
| [Project Structure](.kiro/steering/structure.md)                | **Core reference** - Repository organization, component architecture, and data flows    |
| [Technology Stack](.kiro/steering/tech.md)                      | **Core reference** - Complete technology stack, AWS services, and development commands  |
| [Development Guidelines](docs/guides/DEVELOPMENT_GUIDELINES.md) | Code quality standards, architectural patterns, and best practices                            |

### Deployment & Operations

| Document                                                                       | Description                                                                                    |
| ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| [Solution Handoff Guide](docs/handoff/SOLUTION_HANDOFF_GUIDE.md)                  | **CUSTOMER HANDOFF** - Complete guide for continuing development with Amazon Q Developer |
| [Deployment and Operations Guide](docs/guides/DEPLOYMENT_AND_OPERATIONS_GUIDE.md) | Complete deployment procedures, configuration, and operations                                  |
| [Deployment Recovery Guide](docs/guides/DEPLOYMENT_RECOVERY_GUIDE.md)             | **CRITICAL** - How to redeploy from scratch using S3 artifacts                           |
| [Deployment Success Summary](docs/guides/DEPLOYMENT_SUCCESS_SUMMARY.md)           | Latest deployment verification and test results                                                |
| [CI/CD Pipeline Guide](docs/guides/CICD_PIPELINE_GUIDE.md)                        | GitLab CI/CD setup and automation workflows                                                    |
| [S3 Sync Automation](docs/guides/S3_SYNC_AUTOMATION.md)                           | Automated deployment bucket synchronization                                                    |

### API & Integration

| Document                                                                                     | Description                                                                  |
| -------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| [AWS DRS API Reference](docs/guides/AWS_DRS_API_REFERENCE.md)                                   | DRS API integration patterns and best practices                              |
| [DRS Complete IAM Analysis](docs/reference/DRS_COMPLETE_IAM_ANALYSIS.md)                        | **CRITICAL** - Complete IAM permission requirements for DRS operations |
| [DRS Service Role Policy Analysis](docs/reference/AWS_DRS_SERVICE_ROLE_POLICY_ANALYSIS.md)      | Analysis of DRS service-linked role permissions                              |
| [VMware SRM API Summary](docs/reference/VMware_SRM_REST_API_Summary.md)                         | VMware Site Recovery Manager API reference                                   |
| [Azure Site Recovery Analysis](docs/reference/AZURE_SITE_RECOVERY_RESEARCH_AND_API_ANALYSIS.md) | Azure Site Recovery competitive analysis                                     |
| [Zerto DR Analysis](docs/reference/ZERTO_RESEARCH_AND_API_ANALYSIS.md)                          | Zerto disaster recovery competitive analysis                                 |

### Testing & Quality

| Document                                                                   | Description                                                   |
| -------------------------------------------------------------------------- | ------------------------------------------------------------- |
| [Testing and Quality Assurance](docs/guides/TESTING_AND_QUALITY_ASSURANCE.md) | Comprehensive testing strategy, test cases, and QA procedures |
| [DRS Service Limits Testing](docs/validation/DRS_SERVICE_LIMITS_TESTING.md)   | Unit tests for DRS service limits validation (48 tests)       |

### Research & Analysis

| Document                                                                                         | Description                                                                         |
| ------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| [DRS Launch Template Settings Research](docs/research/DRS_LAUNCH_TEMPLATE_SETTINGS_RESEARCH.md)     | Complete analysis of which launch template settings are safe to edit vs AWS-managed |
| [DRS Template Manager Analysis](docs/research/DRS_TEMPLATE_MANAGER_ANALYSIS.md)                     | Analysis of AWS's official DRS template management tool and supported settings      |
| [DRS Configuration Synchronizer Analysis](docs/research/DRS_CONFIGURATION_SYNCHRONIZER_ANALYSIS.md) | Analysis of AWS's enterprise configuration management tool for DRS                  |

### Troubleshooting

| Document                                                                                  | Description                                                         |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| [DRS Drill Failure Analysis](docs/troubleshooting/DRS_DRILL_FAILURE_ANALYSIS.md)             | Common drill failure patterns and resolution steps                  |
| [IAM Permission Troubleshooting](docs/troubleshooting/IAM_ROLE_ANALYSIS_DRS_PERMISSIONS.md)  | **CRITICAL** - IAM permission requirements for DRS operations |
| [CloudFormation Deployment Issues](docs/troubleshooting/CLOUDFORMATION_DEPLOYMENT_ISSUES.md) | Common CloudFormation deployment problems and solutions             |

### Critical Discoveries

**DRS IAM Permission Model**: When Lambda calls `drs:StartRecovery`, DRS uses the **calling role's IAM permissions** (not its service-linked role) to perform EC2 operations. The OrchestrationRole must have comprehensive EC2 permissions including:

- `ec2:CreateLaunchTemplate`
- `ec2:CreateLaunchTemplateVersion`
- `ec2:ModifyLaunchTemplate`
- `ec2:StartInstances`
- `ec2:RunInstances`
- `ec2:CreateVolume`
- `ec2:AttachVolume`

See [IAM Permission Troubleshooting](docs/troubleshooting/IAM_ROLE_ANALYSIS_DRS_PERMISSIONS.md) for complete details.

### Project Status

| Document                              | Description                                     |
| ------------------------------------- | ----------------------------------------------- |
| [Project Status](docs/PROJECT_STATUS.md) | Current project status, milestones, and roadmap |

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete project history since November 8, 2025.

## Future Enhancements

| Priority | Feature                                                   | LOE       | Description                                                                                                                                                                                                                                                                                                                                                                             | Status        | Documentation                                                                                                                                                                                                                                                                                                                      | Completion Date | Git Commits                                        |
| -------- | --------------------------------------------------------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- | -------------------------------------------------- |
| ~~1~~   | ~~DRS Regional Availability Update~~                     | ~~2d~~   | ~~Update UI and documentation to reflect all 30 AWS DRS regions (28 commercial + 2 GovCloud).~~                                                                                                                                                                                                                                                                                        | ✅ Complete   | [Implementation Plan](docs/implementation/DRS_REGIONAL_AVAILABILITY_UPDATE_PLAN.md)                                                                                                                                                                                                                                                   | Dec 9, 2025     | `fa80b39`, `aed36c0`                           |
| ~~2~~   | ~~DRS Service Limits Compliance~~                        | ~~3d~~   | ~~Implement UI validation for AWS DRS hard limits: 300 replicating servers (hard limit), 500 max servers in all jobs, 20 concurrent jobs. Includes 48 unit tests ([test docs](docs/validation/DRS_SERVICE_LIMITS_TESTING.md)).~~                                                                                                                                                          | ✅ Complete   | [Implementation Plan](docs/implementation/DRS_SERVICE_LIMITS_IMPLEMENTATION_PLAN.md)                                                                                                                                                                                                                                                  | Dec 9, 2025     | `52c649e`, `06bca16`, `fd578cc`, `b65e25e` |
| ~~3~~   | ~~**Dual Mode Orchestration**~~                    | ~~3-4w~~ | ~~Unified tag-based orchestration supporting UI, CLI, SSM, and Step Functions invocation methods. Tag-based Protection Groups with EC2 tag resolution, tag conflict prevention, InvocationSourceBadge tracking, SSM runbook, execution registry, enhanced orchestration state object for parent Step Function integration.~~                                                           | ✅ Complete   | [Implementation Plan](docs/implementation/DUAL_MODE_ORCHESTRATION_DESIGN.md)                                                                                                                                                                                                                                                          | Dec 12, 2025    | `3409505`, `f50658c`                           |
| ~~4~~   | ~~**EC2 Launch Template & DRS Launch Settings**~~  | ~~1-2w~~ | ~~Full EC2 Launch Template and DRS Launch Settings configuration via UI and API. Includes: Subnet, Security Groups, Instance Profile, Instance Type, Instance Type Right Sizing (BASIC/IN_AWS/NONE), Launch Disposition (STARTED/STOPPED), OS Licensing (BYOL/AWS), Copy Private IP, Transfer Server Tags. Settings applied to all servers in Protection Group.~~                      | ✅ Complete   | [EC2 Template MVP v2](docs/implementation/EC2_LAUNCH_TEMPLATE_MVP_PLAN_V2.md)                                                                                                                                                                                                                                                         | Dec 13, 2025    | `2272e5e`, `74ac444`, `a75eb67`              |
| ~~5~~   | ~~**Configuration Export/Import**~~                | ~~2-3d~~ | ~~Full backup and restore of Protection Groups and Recovery Plans via JSON export/import. Includes: one-click export, dry-run validation, non-destructive additive import, server/tag validation, LaunchConfig preservation and automatic application to DRS on import. Uses ProtectionGroupName for cross-environment portability. Access via Settings gear icon.~~                   | ✅ Complete   | [Config Export/Import Spec](docs/implementation/CONFIG_EXPORT_IMPORT_SPEC.md)                                                                                                                                                                                                                                                         | Dec 14, 2025    | `9a34e74`, `eb3ba49`, `be7b4e0`, `e3e7469` |
| ~~6~~   | ~~**DRS Source Server Hardware Display**~~         | ~~4h~~   | ~~Enhanced Protection Group creation with detailed hardware information display. Shows CPU cores, RAM (GiB), and IP address in clean format "FQDN \| CPU: X cores \| RAM: X GiB \| IP: X.X.X.X" during server selection. Backend extracts hardware details from DRS source server metadata and EC2 instance information.~~        | ✅ Complete   | Frontend: `ServerListItem.tsx`, Backend: `lambda/index.py` (lines 4380-4550)                                                                                                                                                                                                                                                         | Dec 16, 2025    | `b63511c`                                   |
| 6        | **Scheduled Drills**                                | 3-5d      | Automated scheduled drill executions with EventBridge rules and reporting dashboard.                                                                                                                                                                                                                                                                                                    | Planned       | -                                                                                                                                                                                                                                                                                                                                  | -               | -                                                  |
| 6        | **CodeBuild & CodeCommit Migration**                | 4-6d      | Migrate from GitLab CI/CD to AWS-native CodePipeline + CodeBuild with CodeCommit repository, leveraging proven patterns from archived DR orchestrator pipeline.                                                                                                                                                                                                                         | Planned       | [Implementation Plan](docs/implementation/CODEBUILD_CODECOMMIT_MIGRATION_PLAN.md)                                                                                                                                                                                                                                                     | -               | -                                                  |
| 7        | **SNS Notification Integration**                    | 1-2w      | Real-time notifications for execution status changes, DRS events, and system health via Email, SMS, Slack, and PagerDuty.                                                                                                                                                                                                                                                               | Planned       | [Implementation Plan](docs/implementation/SNS_NOTIFICATION_IMPLEMENTATION_PLAN.md)                                                                                                                                                                                                                                                    | -               | -                                                  |
| ~~8~~   | ~~**DRS Tag Synchronization**~~                     | ~~1d~~   | ~~Scheduled Lambda syncs EC2 instance tags to DRS source servers across all 28 DRS regions. Enables `copyTags=True` in launch configuration so tags propagate to recovery instances. Includes API endpoint `/drs/tag-sync` for manual sync and comprehensive error handling for disconnected servers.~~                                                                                | ✅ Complete   | [Implementation Plan](docs/implementation/DRS_TAG_SYNC_IMPLEMENTATION_PLAN.md), `lambda/drs_tag_sync.py`, API: `/drs/tag-sync`                                                                                                                                                                                                       | Dec 14, 2025    | `e3e7469`, `be7b4e0`                           |
| 9        | **Step Functions Visualization**                    | 2-3w      | Real-time visualization of Step Functions state machine execution with state timeline, current state indicator, detailed state input/output data, and CloudWatch Logs integration directly in the UI.                                                                                                                                                                                   | Planned       | [Implementation Plan](docs/implementation/STEP_FUNCTIONS_VISUALIZATION_IMPLEMENTATION.md)                                                                                                                                                                                                                                             | -               | -                                                  |
| 10       | **SSM Automation Integration**                      | 2-3w      | Pre-wave and post-wave SSM automation document execution including manual approval gates, health checks, and custom scripts.                                                                                                                                                                                                                                                            | Planned       | [Implementation Plan](docs/implementation/SSM_AUTOMATION_IMPLEMENTATION.md)                                                                                                                                                                                                                                                           | -               | -                                                  |
| 11       | **Cross-Account DRS Monitoring**                    | 2-3w      | Centralized monitoring and alerting for DRS across multiple AWS accounts with dynamic account management, cross-account metrics collection, and unified dashboards. *(Monitoring/alerting only; see #13 for orchestration, #18 for replication setup)*                                                                                                                                  | Planned       | [Implementation Plan](docs/implementation/CROSS_ACCOUNT_DRS_MONITORING_IMPLEMENTATION.md)                                                                                                                                                                                                                                             | -               | -                                                  |
| 12       | **DRS Source Server Management (Remaining)**        | 3-4w      | Remaining DRS source server configuration: Server Info dashboard, Tags Management, Disk Settings, Replication Settings, and Post-Launch Actions. EC2 Launch Template and Launch Settings now complete. *(Detailed config panels; see #17 for Source Servers list page)*                                                                                                                 | Planned       | [Server Info MVP](docs/implementation/DRS_SERVER_INFO_MVP_PLAN.md), [Tags MVP](docs/implementation/DRS_TAGS_MVP_PLAN.md), [Disk Settings MVP](docs/implementation/DRS_DISK_SETTINGS_MVP_PLAN.md), [Replication MVP](docs/implementation/DRS_REPLICATION_SETTINGS_MVP_PLAN.md), [Post-Launch MVP](docs/implementation/DRS_POST_LAUNCH_MVP_PLAN.md) | -               | -                                                  |
| ~~13~~   | ~~**Multi-Account Support (Foundation)**~~          | ~~4-6w~~ | ~~Complete multi-account management system with account context, enforcement logic, auto-selection for single accounts, account selector in top navigation, settings integration with default preferences, and page-level enforcement for multi-account scenarios. Foundation for enterprise-scale DRS management across multiple AWS accounts.~~                                                                                                                                                | ✅ Complete   | [Multi-Account Prototype 1.0](CHANGELOG.md#170---december-17-2025), Account Management: `AccountManagementPanel.tsx`, Context: `AccountContext.tsx`, Selector: `AccountSelector.tsx`, Enforcement: `AccountRequiredWrapper.tsx` | Dec 17, 2025   | `905a682` (v1.0.0-multi-account-prototype)    |
| 13       | **Cross-Account Orchestration**                     | 3-4w      | Cross-account recovery orchestration with hub-and-spoke architecture, cross-account IAM roles, and federated recovery plans. Scale beyond 300 servers using multiple staging accounts (250/account recommended). *(Builds on Multi-Account Foundation completed in v1.7.0)*                                                                                                                | Planned       | [Implementation Guide](docs/implementation/MULTI_ACCOUNT_DRS_IMPLEMENTATION.md), Foundation: Multi-Account Prototype 1.0 (v1.7.0)                                                                                                                                                                                                   | -               | -                                                  |
| 14       | **DRS Agent Installation & Replication Monitoring** | 8-9w      | End-to-end DRS agent installation via SSM with progress tracking, replication initialization visualization (11 steps), continuous replication monitoring, reverse replication & failback management, and unified replication dashboard with aggregate metrics and alerts. *(SOURCE server agent install; see #15 for RECOVERY instance agent install)*                                  | Planned       | [Implementation Plan](docs/implementation/DRS_AGENT_INSTALLATION_REPLICATION_MONITORING.md)                                                                                                                                                                                                                                           | -               | -                                                  |
| 15       | **Failover & Failback Orchestration**               | 10-12w    | Complete DR lifecycle: automatic failover session tracking, agent installation on recovery instances, automatic Protection Group and Recovery Plan mirroring with original region settings (subnet, security groups, etc.), reverse replication monitoring, and one-click failback execution. *(RECOVERY instance agent install; see #14 for SOURCE server agent install)*              | Planned       | [Implementation Plan](docs/implementation/FAILOVER_FAILBACK_ORCHESTRATION_PLAN.md), [Spec](.kiro/specs/failover-failback-orchestration/requirements.md)                                                                                                                                                                                  | -               | -                                                  |
| 16       | **DRS Recovery Deep Dive Enhancements**             | 4w        | Enhanced recovery capabilities: point-in-time snapshot selection UI, detailed job log monitoring with event streaming, recovery instance tracking, comprehensive error handling with retry logic. Covers all DRS recovery APIs (StartRecovery, DescribeJobs, DescribeJobLogItems, DescribeRecoverySnapshots, DescribeRecoveryInstances, TerminateRecoveryInstances).                    | ✅ Documented | [Deep Dive Plan](docs/implementation/DRS_RECOVERY_DEEP_DIVE.md)                                                                                                                                                                                                                                                                       | -               | -                                                  |
| 17       | **DRS Source Servers Page**                         | 3-4w      | Dedicated Source Servers page replicating AWS DRS Console functionality. Displays all DRS source servers with real-time replication status, recovery readiness, last recovery results, and pending actions. Includes server details page with tabs for Overview, Replication, Launch Settings, Recovery History, and Tags. *(List page; see #12 for detailed config panels)*            | ✅ Documented | [Implementation Plan](docs/implementation/DRS_SOURCE_SERVERS_PAGE_PLAN.md)                                                                                                                                                                                                                                                            | -               | -                                                  |
| 18       | **DRS Extended Source Servers & Cross-Account**     | 6-8w      | Cross-account disaster recovery with Extended Source Servers. Enables production in Account A replicating to staging in Account B. Includes CreateExtendedSourceServer API, cross-account IAM setup, staging area configuration, cross-account recovery orchestration, and multi-account management UI. *(Replication setup; see #13 for orchestration, #11 for monitoring)*            | ✅ Documented | [Implementation Plan](docs/implementation/DRS_EXTENDED_SOURCE_SERVERS_IMPLEMENTATION.md)                                                                                                                                                                                                                                              | -               | -                                                  |

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Built for enterprise disaster recovery on AWS
