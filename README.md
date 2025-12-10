# AWS DRS Orchestration Solution

Enterprise-grade disaster recovery orchestration for AWS Elastic Disaster Recovery (DRS) with wave-based execution, dependency management, and automated health checks.

[![AWS](https://img.shields.io/badge/AWS-DRS-FF9900?logo=amazonaws)](https://aws.amazon.com/disaster-recovery/)
[![CloudFormation](https://img.shields.io/badge/IaC-CloudFormation-232F3E?logo=amazonaws)](cfn/)
[![React](https://img.shields.io/badge/Frontend-React%2019-61DAFB?logo=react)](frontend/)
[![Python](https://img.shields.io/badge/Backend-Python%203.12-3776AB?logo=python)](lambda/)

## Overview

AWS DRS Orchestration enables organizations to orchestrate complex multi-tier application recovery with wave-based execution, dependency management, and automated health checks using AWS-native serverless services.

### Key Capabilities

- **Cost-Effective**: $12-40/month operational cost with pay-per-use serverless pricing
- **Unlimited Waves**: Flexible wave-based orchestration with no artificial constraints
- **Platform Agnostic**: Supports any source platform (VMware, physical servers, cloud)
- **Sub-Second RPO**: Leverages AWS DRS continuous replication capabilities
- **Fully Serverless**: No infrastructure to manage, scales automatically

## Key Features

### Protection Groups

- **Automatic Server Discovery**: Real-time DRS source server discovery across all AWS DRS-supported regions
- **Visual Server Selection**: Intuitive interface with assignment status indicators
- **Conflict Prevention**: Single server per group constraint prevents recovery conflicts
- **Real-Time Search**: Filter servers by hostname, Server ID, or Protection Group name

### Recovery Plans

- **Wave-Based Orchestration**: Define multi-wave recovery sequences with unlimited flexibility
- **Dependency Management**: Automatic wave dependency handling with circular dependency detection
- **Drill Mode**: Test recovery procedures without impacting production
- **Automation Hooks**: Pre-wave and post-wave actions for validation and health checks

### Execution Monitoring

- **Real-Time Dashboard**: Live execution progress with wave-level status tracking
- **Pause/Resume Control**: Pause executions between waves for validation and resume when ready
- **Instance Termination**: Terminate recovery instances after successful testing
- **DRS Job Events**: Real-time DRS job event monitoring with 3-second auto-refresh and collapsible view
- **Loading State Management**: Prevents multiple button clicks during operations with visual feedback
- **Execution History**: Complete audit trail of all recovery executions
- **CloudWatch Integration**: Deep-link to CloudWatch Logs for troubleshooting

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

### Endpoints

#### Protection Groups

| Method | Endpoint                    | Description                  |
| ------ | --------------------------- | ---------------------------- |
| GET    | `/protection-groups`      | List all protection groups   |
| POST   | `/protection-groups`      | Create protection group      |
| GET    | `/protection-groups/{id}` | Get protection group details |
| PUT    | `/protection-groups/{id}` | Update protection group      |
| DELETE | `/protection-groups/{id}` | Delete protection group      |

#### Recovery Plans

| Method | Endpoint                 | Description               |
| ------ | ------------------------ | ------------------------- |
| GET    | `/recovery-plans`      | List all recovery plans   |
| POST   | `/recovery-plans`      | Create recovery plan      |
| GET    | `/recovery-plans/{id}` | Get recovery plan details |
| PUT    | `/recovery-plans/{id}` | Update recovery plan      |
| DELETE | `/recovery-plans/{id}` | Delete recovery plan      |

#### Executions

| Method | Endpoint                                 | Description                   |
| ------ | ---------------------------------------- | ----------------------------- |
| GET    | `/executions`                          | List execution history        |
| POST   | `/executions`                          | Start new execution           |
| GET    | `/executions/{id}`                     | Get execution details         |
| POST   | `/executions/{id}/pause`               | Pause execution between waves |
| POST   | `/executions/{id}/resume`              | Resume paused execution       |
| POST   | `/executions/{id}/cancel`              | Cancel running execution      |
| POST   | `/executions/{id}/terminate-instances` | Terminate recovery instances  |

#### DRS Integration

| Method | Endpoint                                | Description                 |
| ------ | --------------------------------------- | --------------------------- |
| GET    | `/drs/source-servers?region={region}` | Discover DRS source servers |

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

| Document                                                                | Description                                   |
| ----------------------------------------------------------------------- | --------------------------------------------- |
| [Product Requirements](docs/requirements/PRODUCT_REQUIREMENTS_DOCUMENT.md) | Complete PRD with features and specifications |
| [Deployment Guide](docs/guides/DEPLOYMENT_AND_OPERATIONS_GUIDE.md)         | Step-by-step deployment instructions          |
| [Architecture Design](docs/architecture/ARCHITECTURAL_DESIGN_DOCUMENT.md)  | System architecture and design decisions      |
| [API Reference](docs/guides/AWS_DRS_API_REFERENCE.md)                      | DRS API integration patterns                  |
| [Testing Guide](docs/guides/TESTING_AND_QUALITY_ASSURANCE.md)              | Testing procedures and quality assurance      |

### Documentation Index

See [Appendix: Complete Documentation Index](#appendix-complete-documentation-index) for full documentation catalog with detailed descriptions.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Repository Snapshots & Rollback

The repository uses Git tags to mark significant milestones. These tags capture the complete state of all files and can be used to rollback the entire repository.

### Available Tags

| Tag                 | Description                                                               | Date             |
| ------------------- | ------------------------------------------------------------------------- | ---------------- |
| `mvp-demo-ready`  | MVP Demo Ready - Complete working state with all core features functional | December 9, 2025 |
| `future-plans-v1` | All future implementation plans documented                                | December 9, 2025 |

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

### Requirements & Planning

| Document                                                                         | Description                                                                         |
| -------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| [Product Requirements Document](docs/requirements/PRODUCT_REQUIREMENTS_DOCUMENT.md) | Complete PRD with problem statement, features, technical specs, and success metrics |

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

| Document                                                                       | Description                                                          |
| ------------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| [Deployment and Operations Guide](docs/guides/DEPLOYMENT_AND_OPERATIONS_GUIDE.md) | Complete deployment procedures, configuration, and operations        |
| [Deployment Recovery Guide](docs/guides/DEPLOYMENT_RECOVERY_GUIDE.md)             | **CRITICAL** - How to redeploy from scratch using S3 artifacts |
| [Deployment Success Summary](docs/guides/DEPLOYMENT_SUCCESS_SUMMARY.md)           | Latest deployment verification and test results                      |
| [CI/CD Pipeline Guide](docs/guides/CICD_PIPELINE_GUIDE.md)                        | GitLab CI/CD setup and automation workflows                          |
| [S3 Sync Automation](docs/guides/S3_SYNC_AUTOMATION.md)                           | Automated deployment bucket synchronization                          |

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

---

## Changelog

### December 10, 2025

**DRS Capacity Auto-Refresh** - `9c7177b`

- Added 30-second auto-refresh interval to DRS Capacity panel on Dashboard
- DRS quotas now poll automatically like executions, keeping capacity data current
- Fixed TypeScript error with region value capture in interval callback

**Dashboard DRS Regions Expansion** - `9c7177b`

- Expanded Dashboard DRS region selector from 7 to all 28 commercial DRS regions
- Organized by geography: Americas (6), Europe (8), Asia Pacific (10), Middle East & Africa (4)

**DRS Uninitialized Region Error Messages** - `9c7177b`

- Improved error handling for uninitialized DRS regions
- Detects `UninitializedAccountException` and `UnrecognizedClientException` errors
- Returns friendly message: "DRS not initialized in {region}. Initialize DRS in the AWS Console."

**DRS Replicating Server Count Fix** - `9c7177b`

- Fixed incorrect replicating server count showing 0 instead of actual count
- Root cause: DRS API returns `CONTINUOUS` state, not `CONTINUOUS_REPLICATION`
- Updated `VALID_REPLICATION_STATES` constant and capacity calculation

**API Gateway CORS Fix for /drs/quotas** - `9c7177b`

- Added missing `/drs/quotas` endpoint to API Gateway CloudFormation template
- Created `DRSQuotasResource`, `DRSQuotasGetMethod`, and `DRSQuotasOptionsMethod`
- Fixed CORS preflight for DRS quota requests

**Multi-Account Support Implementation Plan Update**

- Added Phase 3.0: Dashboard DRS Capacity account selector design
- Added cross-account DRS quota API endpoint specification
- Added `get_drs_account_capacity_cross_account()` Lambda function design
- Added recommended implementation order prioritizing Dashboard account dropdown

### December 9, 2025

**UI/UX Enhancements** - `6fbd084`, `b8f370d`, `931b08c`, `9a5f14c`, `c73f7f8`, `7d452cd`, `fc6c26c`

- Added AWS smile logo to TopNavigation header
- Updated title to "Elastic Disaster Recovery Orchestrator"
- Navigation collapse state management for AWS Console-style hamburger menu
- Login page redesigned to match AWS Console design standards
- Native HTML inputs on login page for consistent password manager icon positioning
- Standardized frontend icons - replaced emojis with CloudScape icons
- Added CloudScape icons to Protection Groups actions menu

**Getting Started Page Improvements** - `136ecc5`, `dee6fdd`, `178977e`

- Enhanced Getting Started page with improved Quick Start Guide
- Fixed card alignment with fitHeight and flex layout
- Improved layout and guide content

**DRS Service Limits Unit Tests** - `fd578cc`, `b65e25e`

- Added Vitest test framework to frontend with jsdom environment
- Created 21 frontend unit tests for `drsQuotaService.ts`
- Created 27 backend unit tests for Lambda validation functions
- Tests validate DRS limits without requiring actual DRS infrastructure
- Uses mocked boto3 clients for backend API testing
- Added test documentation: [DRS Service Limits Testing](docs/validation/DRS_SERVICE_LIMITS_TESTING.md)

**DRS Service Limits Compliance (Frontend Phase 2)** - `06bca16`

- New `drsQuotaService.ts` with DRS_LIMITS constants and helper functions
- New `DRSQuotaStatus.tsx` component with progress bars for quota visualization
- Added `getDRSQuotas()` method to API client for `/drs/quotas` endpoint
- Wave size validation in RecoveryPlanDialog (max 100 servers per wave)
- DRS limit error handling in RecoveryPlansPage with specific toast messages

**DRS Service Limits Compliance (Backend Phase 1)** - `52c649e`

- Added comprehensive DRS service limits validation to prevent execution failures
- New `DRS_LIMITS` constants with all AWS DRS service quotas:
  - MAX_SERVERS_PER_JOB: 100 (hard limit)
  - MAX_CONCURRENT_JOBS: 20 (hard limit)
  - MAX_SERVERS_IN_ALL_JOBS: 500 (hard limit)
  - MAX_REPLICATING_SERVERS: 300 (hard limit, cannot increase)
  - Warning/Critical thresholds for capacity monitoring
- New validation functions: `validate_wave_sizes()`, `validate_concurrent_jobs()`, `validate_servers_in_all_jobs()`, `validate_server_replication_states()`, `get_drs_account_capacity()`
- New `/drs/quotas` API endpoint for quota monitoring
- Integrated validations into `execute_recovery_plan()` with specific error codes

**DRS Regional Availability Update** - `fa80b39`

- Updated RegionSelector with all 28 commercial AWS DRS regions
- Changed label format to show region code first: `us-east-1 (N. Virginia)`
- Updated documentation to reflect 30 total regions (28 commercial + 2 GovCloud)

**Improved DRS Initialization Error Messages** - `aed36c0`

- Differentiated between "DRS Not Initialized" (warning) and "No Replicating Servers" (info)
- More actionable error messages in both frontend and backend

**Deployment Workflow Updates** - `9030a07`

- Updated CI/CD documentation to reflect current `./scripts/sync-to-deployment-bucket.sh` process
- Clarified 5 Lambda functions and 6 nested CloudFormation stacks architecture
- Added timing information: fast Lambda updates (~5s) vs full deployments (5-10min)
- Updated deployment verification rules with accurate architecture counts
- Emphasized S3 bucket as source of truth for all deployments

**Resume Execution Fix** - `9030a07`

- Fixed 400 Bad Request error when resuming paused executions
- Root cause: Step Functions `WaitForResume` state had `OutputPath: '$.Payload'` but callback outputs from `SendTaskSuccess` are returned directly at root level
- Solution: Removed `OutputPath` from `WaitForResume` state in `cfn/step-functions-stack.yaml`
- Updated `resume_execution()` in Lambda to return full application state via `SendTaskSuccess`

**DRS Job Events Auto-Refresh** - `9030a07`

- Fixed DRS Job Events not auto-updating in the execution details UI
- Separated polling into its own `useEffect` with a ref to prevent interval recreation
- Reduced polling interval from 5s to 3s for faster updates
- Made DRS Job Events collapsible via ExpandableSection (expanded by default)
- Auto-refresh continues regardless of collapsed state
- Added event count in header: `DRS Job Events (X)`

**Loading State Management** - `9030a07`

- Added `loading` prop to `ConfirmDialog` component that disables both Cancel and Confirm buttons
- Updated Protection Groups delete dialog with loading state
- Updated Recovery Plans delete dialog with loading state
- Updated Cancel Execution dialog with loading state
- Updated Terminate Instances dialog with loading state
- Resume button already had proper `disabled={resuming}` and `loading={resuming}` props
- Prevents accidental multiple operations and provides clear visual feedback

### December 8, 2025

**Documentation Deep Research** - `aec77e7`, `82185a0`, `9f351b0`, `29b745c`, `df4db12`, `5aed175`

- Comprehensive documentation updates for DR platform APIs
- Fixed Mermaid sequence diagram syntax errors
- Updated S3 sync automation guide with accurate S3 structure
- Updated CI/CD guide with ECR Public images to avoid Docker Hub rate limits
- Removed competitor references and clarified AWS DRS regional availability

**CI/CD Pipeline Improvements** - `d2f2850`, `b45aaf8`, `8814702`, `6d8b087`, `e198980`, `675d233`, `b159293`

- Use ECR Public images to avoid Docker Hub rate limits
- Correct aws-config.js structure in GitLab CI
- Disable test jobs (tests/ directory is gitignored)
- Resolve Fn::Sub variable error with CommaDelimitedList parameter
- Fix cfn-lint CI pipeline configuration

**Lambda Code Cleanup** - `89cf462`

- Refactored and cleaned up deprecated Lambda code
- Updated architecture diagrams

### December 7, 2025

**First Working Prototype** - `db1f41a`, `00f4eb3`

- First working Step Functions integrated prototype
- Dynamic DRS source server discovery
- Fixed Step Functions LAUNCHED status detection

**Critical IAM Permission Fixes** - `242b696`, `efeae49`, `8132665`, `60988cd`

- Added ec2:StartInstances to IAM policy - both servers now launch
- Fixed ec2:DeleteVolume IAM condition blocking DRS staging volume cleanup
- Added ec2:DetachVolume permission for DRS credential passthrough
- Added missing IAM permissions for DRS recovery operations

**Architecture Simplification** - `1a797c7`, `d912534`

- Removed polling infrastructure, use Step Functions only
- Added Step Functions to fix EC2 launch issue

**UI Improvements v1.1** - `aaf4059`

- Various UI improvements and refinements

**Documentation Updates** - `7e88a47`, `18acc84`, `0fc0bc7`, `d169e70`

- Production-ready README with mermaid diagrams
- Added CI/CD setup and post-deployment guide
- Added DRS + Step Functions coordination analysis
- Repository cleanup for production

### December 6, 2025

**🎉 MILESTONE: First Successful DRS Drill Execution** - `1f0f94f`

- First successful end-to-end DRS drill execution through the platform

**CloudScape Design System Migration Complete** - `c499193`, `f0892b3`, `5623c1d`

- Complete CloudScape Design System migration (100%)
- ExecutionsPage migration complete
- All pages now use CloudScape components

**GitLab CI/CD Pipeline** - `08aa58e`, `1683fc6`, `5e06334`

- Added GitLab CI/CD pipeline with comprehensive deployment automation
- Fixed CloudFormation output key names in CI/CD pipeline
- Added Session 64 handoff document for CI/CD pipeline

## Future Enhancements

| Priority | Feature                                    | Description                                                                                                                                                                                                                      | Status      | Documentation                                                                          | Completion Date | Git Commits              |
| -------- | ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | -------------------------------------------------------------------------------------- | --------------- | ------------------------ |
| ~~1~~   | ~~DRS Regional Availability Update~~      | ~~Update UI and documentation to reflect all 30 AWS DRS regions (28 commercial + 2 GovCloud).~~                                                                                                                                 | ✅ Complete | [Implementation Plan](docs/implementation/DRS_REGIONAL_AVAILABILITY_UPDATE_PLAN.md)       | Dec 9, 2025     | `fa80b39`, `aed36c0` |
| ~~2~~   | ~~DRS Service Limits Compliance~~         | ~~Implement UI validation for AWS DRS hard limits: 300 replicating servers (hard limit), 500 max servers in all jobs, 20 concurrent jobs. Includes 48 unit tests ([test docs](docs/validation/DRS_SERVICE_LIMITS_TESTING.md)).~~ | ✅ Complete | [Implementation Plan](docs/implementation/DRS_SERVICE_LIMITS_IMPLEMENTATION_PLAN.md)      | Dec 9, 2025     | `52c649e`, `06bca16`, `fd578cc`, `b65e25e` |
| 3        | **CodeBuild & CodeCommit Migration** | Migrate from GitLab CI/CD to AWS-native CodePipeline + CodeBuild with CodeCommit repository, leveraging proven patterns from archived DR orchestrator pipeline.                                                                  | Planned     | [Implementation Plan](docs/implementation/CODEBUILD_CODECOMMIT_MIGRATION_PLAN.md)         | -               | -                        |
| 4        | **DRS Launch Settings Management**   | Configure EC2 launch templates for DRS source servers directly from the UI. Includes single-server configuration, bulk updates, and template library.                                                                            | Planned     | [Implementation Plan](docs/implementation/DRS_LAUNCH_SETTINGS_IMPLEMENTATION_PLAN.md)     | -               | -                        |
| 5        | **DRS Tag Synchronization**          | Synchronize EC2 instance tags and instance types to DRS source servers through UI with on-demand sync, bulk operations, real-time progress monitoring, and sync history. Integrates archived tag sync tool with visual controls. | Planned     | [Implementation Plan](docs/implementation/DRS_TAG_SYNC_IMPLEMENTATION_PLAN.md)            | -               | -                        |
| 6        | **SSM Automation Integration**       | Pre-wave and post-wave SSM automation document execution including manual approval gates, health checks, and custom scripts.                                                                                                     | Planned     | [Implementation Plan](docs/implementation/SSM_AUTOMATION_IMPLEMENTATION.md)               | -               | -                        |
| 7        | **Step Functions Visualization**     | Real-time visualization of Step Functions state machine execution with state timeline, current state indicator, detailed state input/output data, and CloudWatch Logs integration directly in the UI.                            | Planned     | [Implementation Plan](docs/implementation/STEP_FUNCTIONS_VISUALIZATION_IMPLEMENTATION.md) | -               | -                        |
| 8        | **Multi-Account Support**            | Orchestrate recovery across multiple AWS accounts with hub-and-spoke architecture, cross-account IAM roles, and unified management UI. Scale beyond 300 servers using multiple staging accounts (250/account recommended).       | Planned     | [Implementation Guide](docs/implementation/MULTI_ACCOUNT_DRS_IMPLEMENTATION.md) | -               | -                        |
| 9        | **Cross-Account DRS Monitoring**     | Centralized monitoring and alerting for DRS across multiple AWS accounts with dynamic account management, cross-account metrics collection, and unified dashboards.                                                              | Planned     | [Implementation Plan](docs/implementation/CROSS_ACCOUNT_DRS_MONITORING_IMPLEMENTATION.md) | -               | -                        |
| 10       | **SNS Notification Integration**     | Real-time notifications for execution status changes, DRS events, and system health via Email, SMS, Slack, and PagerDuty.                                                                                                        | Planned     | [Implementation Plan](docs/implementation/SNS_NOTIFICATION_IMPLEMENTATION_PLAN.md)        | -               | -                        |
| 11       | **Scheduled Drills**                 | Automated scheduled drill executions with reporting                                                                                                                                                                              | Planned     | -                                                                                      | -               | -                        |

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Built for enterprise disaster recovery on AWS
