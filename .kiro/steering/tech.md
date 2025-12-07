# Technology Stack

## Architecture

**Serverless-first, cloud-native** architecture using AWS-managed services with modular CloudFormation nested stack design.

### Modular CloudFormation Architecture

The solution uses a **modular nested stack architecture** for better maintainability and scalability:

| Stack | Lines | Purpose |
|-------|-------|---------|
| **master-template.yaml** | 336 | Root orchestrator coordinating all nested stacks |
| **database-stack.yaml** | 130 | DynamoDB tables (3) with encryption & PITR |
| **lambda-stack.yaml** | 408 | Lambda functions (4) + IAM roles + CloudWatch Log Groups |
| **api-stack.yaml** | 696 | Cognito User Pool, API Gateway REST API, Step Functions |
| **security-stack.yaml** | 648 | WAF, CloudTrail, Secrets Manager (optional) |
| **frontend-stack.yaml** | 361 | S3 bucket, CloudFront distribution, Custom Resources |

**Benefits**: Each template under 750 lines, single-command deployment, modular updates, professional AWS patterns.

## Frontend

- **Framework**: React 18.3 with TypeScript 5.5
- **UI Library**: AWS CloudScape Design System (migrated from Material-UI Dec 2025)
- **Build Tool**: Vite 5.4
- **Routing**: React Router 6.26
- **HTTP Client**: Axios 1.7
- **Auth**: AWS Amplify (Cognito integration)
- **Hosting**: S3 + CloudFront
- **Components**: 23 React components (5 pages + 18 shared components)
- **Code Size**: ~3,000 lines of TypeScript

### Frontend Structure
```
frontend/src/
├── components/     # 18+ reusable components
│   ├── ProtectionGroupDialog.tsx    # Create/Edit Protection Groups
│   ├── RecoveryPlanDialog.tsx       # Create/Edit Recovery Plans
│   ├── ServerSelector.tsx           # Visual server selection
│   ├── RegionSelector.tsx           # AWS region dropdown
│   ├── StatusBadge.tsx              # Status indicators
│   ├── WaveProgress.tsx             # Wave execution timeline
│   └── ...
├── pages/          # 5 page components
│   ├── LoginPage.tsx                # Cognito authentication
│   ├── Dashboard.tsx                # Overview metrics
│   ├── ProtectionGroupsPage.tsx    # Protection Groups CRUD
│   ├── RecoveryPlansPage.tsx       # Recovery Plans CRUD
│   └── ExecutionsPage.tsx          # Execution monitoring
├── services/       # API client (api.ts)
├── contexts/       # AuthContext for authentication
├── theme/          # CloudScape theme configuration
└── types/          # TypeScript type definitions
```

### Frontend Features
- **Automatic Server Discovery**: Real-time DRS source server discovery by region
- **VMware SRM-Like Experience**: Visual server selection with assignment status
- **Real-Time Search**: Filter servers by hostname, Server ID, or Protection Group
- **Auto-Refresh**: Silent 30-second auto-refresh for server status
- **CloudScape Table**: Sortable, filterable tables with collection hooks
- **Responsive Design**: Desktop, tablet, mobile support
- **Accessibility**: WCAG 2.1 AA compliant (CloudScape built-in)

## Backend

- **Runtime**: Python 3.12
- **Compute**: AWS Lambda (4 functions)
  - `api-handler`: Main API logic (912 lines) - CRUD operations, DRS integration
  - `orchestration`: DRS recovery orchestration (556 lines) - Wave execution, job monitoring
  - `frontend-builder`: Automated frontend deployment - React build & S3 sync
  - `s3-cleanup`: Custom resource for stack deletion - Empties S3 buckets
- **Orchestration**: AWS Step Functions (35+ states) - Wave-based recovery workflow
- **API**: API Gateway REST API (30+ resources) - RESTful endpoints with Cognito auth
- **Auth**: AWS Cognito User Pools with JWT tokens
- **Database**: DynamoDB (3 tables, on-demand capacity)
  - `protection-groups-{env}`: Server groupings with assignment tracking
  - `recovery-plans-{env}`: Wave configurations with dependencies
  - `execution-history-{env}`: Execution audit trail with StatusIndex GSI

### DynamoDB Schema

**Protection Groups Table**
- **Primary Key**: `GroupId` (UUID)
- **Attributes**: `GroupName`, `Region`, `SourceServerIds[]`, `CreatedDate`, `LastModifiedDate`
- **Features**: Single server per group constraint, assignment tracking

**Recovery Plans Table**
- **Primary Key**: `PlanId` (UUID)
- **Attributes**: `PlanName`, `Waves[]`, `Dependencies`, `RPO`, `RTO`, `CreatedDate`
- **Features**: Wave dependencies, automation actions, unlimited waves

**Execution History Table**
- **Primary Key**: `ExecutionId` (UUID), `PlanId` (Sort Key)
- **GSI**: `StatusIndex` (Status, StartTime) - For active execution queries
- **Attributes**: `Status`, `Waves[]`, `StartTime`, `EndTime`, `ExecutionType`
- **Features**: Wave-level tracking, error details, audit trail

### Phase 2 Polling Infrastructure

**ExecutionFinder Lambda** (EventBridge scheduled)
- **Trigger**: Every 60 seconds via EventBridge rule
- **Purpose**: Discover new PENDING executions and trigger polling
- **Performance**: 20s detection (TARGET: <60s) → **3x FASTER** ✅

**ExecutionPoller Lambda** (Adaptive polling)
- **Trigger**: Invoked by ExecutionFinder for each active execution
- **Purpose**: Poll DRS job status and update execution records
- **Performance**: Every ~15s adaptive polling ✅
- **Features**: Automatic cleanup when execution completes

**StatusIndex GSI**
- **Purpose**: Fast queries for active executions (PENDING, POLLING, LAUNCHING)
- **Performance**: <21ms queries (TARGET: <100ms) → **4x FASTER** ✅

## Infrastructure

- **IaC**: AWS CloudFormation (6 nested stacks, 2,400+ lines YAML)
- **Deployment**: Single-command deployment via master template
- **S3 Repository**: `s3://aws-drs-orchestration` with versioning enabled
- **Git Integration**: All S3 objects tagged with git commit hash
- **Auto-Sync**: Git post-push hook automatically syncs to S3

### CloudFormation Stacks

**master-template.yaml** (336 lines)
- Root orchestrator coordinating all nested stacks
- Parameter propagation to child stacks
- Output aggregation from nested stacks

**database-stack.yaml** (130 lines)
- 3 DynamoDB tables with encryption & PITR
- StatusIndex GSI for execution queries
- On-demand capacity mode

**lambda-stack.yaml** (408 lines)
- 4 Lambda functions with IAM roles
- CloudWatch Log Groups with retention
- DRS permissions for recovery operations
- Multi-partition ARN support (AWS Standard, GovCloud, China)

**api-stack.yaml** (696 lines)
- Cognito User Pool with email verification
- API Gateway REST API (30+ resources)
- Step Functions state machine (35+ states)
- EventBridge rules for polling infrastructure

**security-stack.yaml** (648 lines)
- WAF for API protection (optional)
- CloudTrail for audit logging (optional)
- Secrets Manager for sensitive data (optional)

**frontend-stack.yaml** (361 lines)
- S3 bucket with encryption
- CloudFront distribution with HTTPS
- Custom resources for frontend build
- Automated React build & deployment

## Testing

- **E2E Tests**: Playwright with TypeScript
- **Test Location**: `tests/playwright/`
- **Configuration**: `playwright.config.ts`
- **Page Objects**: `tests/playwright/page-objects/`
- **Test Coverage**: Smoke tests for critical user flows

## Common Commands

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Development server (local)
npm run dev

# Build for production
npm run build

# Build with AWS config injection
./build.sh

# Lint
npm run lint

# Type check
npx tsc --noEmit
```

### Frontend Deployment
```bash
# Deploy to S3 (exclude aws-config.json to preserve CloudFormation-injected config)
aws s3 sync frontend/dist/ s3://drs-orchestration-fe-438465159935-test/ --delete --exclude "aws-config.json" --region us-east-1

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id E46O075T9AHF3 --paths '/*' --region us-east-1
```

### Backend Deployment

**Automated Lambda Deployment** (Recommended)
```bash
cd lambda

# Direct deployment (fastest - development)
python3 deploy_lambda.py --direct \
  --function-name drs-orchestration-api-handler-test \
  --region us-east-1

# S3 upload (CloudFormation preparation)
python3 deploy_lambda.py --s3-only \
  --bucket aws-drs-orchestration \
  --region us-east-1

# CloudFormation update (production standard)
python3 deploy_lambda.py --cfn \
  --bucket aws-drs-orchestration \
  --stack-name drs-orchestration-test \
  --region us-east-1

# Full deployment (S3 + Direct)
python3 deploy_lambda.py --full \
  --bucket aws-drs-orchestration \
  --function-name drs-orchestration-api-handler-test \
  --region us-east-1
```

**Manual CloudFormation Deployment**
```bash
# Deploy entire stack
aws cloudformation deploy \
  --template-url https://aws-drs-orchestration.s3.us-east-1.amazonaws.com/cfn/master-template.yaml \
  --stack-name drs-orchestration \
  --parameter-overrides \
    ProjectName=drs-orchestration \
    Environment=test \
    SourceBucket=aws-drs-orchestration \
    AdminEmail=your-email@example.com \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1

# Monitor deployment
aws cloudformation wait stack-create-complete \
  --stack-name drs-orchestration \
  --region us-east-1
```

### S3 Repository Sync

**Automated Sync** (Enabled by default)
```bash
# Auto-sync on every git push (via post-push hook)
git push origin main

# Manual sync
make sync-s3

# Sync with frontend build
make sync-s3-build

# Preview changes (dry-run)
make sync-s3-dry-run

# Enable/disable auto-sync
make enable-auto-sync
make disable-auto-sync
```

### Testing
```bash
cd tests/playwright

# Install dependencies
npm install

# Run tests
npx playwright test

# Run tests with UI
npx playwright test --ui

# View test report
npx playwright show-report test-results/html-report
```

### Validation
```bash
# Validate CloudFormation templates
make validate

# Lint templates (cfn-lint)
make lint

# Check template info
make info
```

## Environment Variables

### Frontend (.env.test)
```bash
COGNITO_REGION=us-east-1
COGNITO_USER_POOL_ID=us-east-1_wfyuacMBX
COGNITO_CLIENT_ID=<client-id>
API_ENDPOINT=https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test
CLOUDFRONT_URL=https://d1wfyuosowt0hl.cloudfront.net
```

### Lambda (Environment Variables)
```bash
PROTECTION_GROUPS_TABLE=protection-groups-test
RECOVERY_PLANS_TABLE=recovery-plans-test
EXECUTION_HISTORY_TABLE=execution-history-test
STATE_MACHINE_ARN=arn:aws:states:us-east-1:...
EXECUTION_FINDER_FUNCTION_NAME=drs-orchestration-execution-finder-test
EXECUTION_POLLER_FUNCTION_NAME=drs-orchestration-execution-poller-test
```

## Dependencies

### Frontend
- React 18.3
- AWS CloudScape Design System (@cloudscape-design/components)
- @cloudscape-design/collection-hooks (table filtering/sorting)
- AWS Amplify 6.x (Cognito integration)
- Axios 1.7 (HTTP client)
- TypeScript 5.5
- Vite 5.4 (build tool)
- React Router 6.26 (routing)

### Backend
- boto3 1.26.137 (AWS SDK for Python)
- crhelper 2.0.11 (CloudFormation custom resources)
- Python 3.12 runtime

### Development Tools
- Playwright (E2E testing)
- cfn-lint (CloudFormation validation)
- ESLint (JavaScript/TypeScript linting)
- Prettier (code formatting)

## AWS Services Used

### Core Services
- **Amazon DynamoDB**: Data persistence (3 tables with GSI)
- **AWS Lambda**: Serverless compute (4 functions)
- **AWS Step Functions**: Workflow orchestration (35+ states)
- **Amazon API Gateway**: REST API (30+ resources)
- **Amazon Cognito**: User authentication (JWT tokens)
- **Amazon S3**: Static hosting & artifact storage
- **Amazon CloudFront**: CDN for frontend delivery
- **AWS Systems Manager**: Post-launch automation (SSM documents)
- **AWS CloudFormation**: Infrastructure as Code (6 nested stacks)
- **AWS IAM**: Identity and access management
- **AWS Elastic Disaster Recovery (DRS)**: Core DR service integration

### Optional Services
- **AWS WAF**: API protection (optional)
- **AWS CloudTrail**: Audit logging (optional)
- **AWS Secrets Manager**: Sensitive data storage (optional)

### Monitoring & Logging
- **Amazon CloudWatch Logs**: Lambda function logs
- **Amazon CloudWatch Metrics**: Performance monitoring
- **Amazon CloudWatch Alarms**: Alerting (planned)
- **Amazon EventBridge**: Event-driven automation (polling infrastructure)

## Current Deployment

**Environment**: TEST (us-east-1, account 438465159935)

**Frontend**
- **URL**: https://d1wfyuosowt0hl.cloudfront.net
- **Distribution**: E46O075T9AHF3
- **S3 Bucket**: drs-orchestration-fe-438465159935-test

**Backend**
- **API**: https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test
- **Lambda**: drs-orchestration-api-handler-test (11.09 MB, deployed Nov 28, 2025)
- **Cognito**: us-east-1_wfyuacMBX
- **Test User**: testuser@example.com / IiG2b1o+D$

**Status**
- ✅ All CloudFormation stacks deployed
- ✅ Phase 2 polling infrastructure operational
- ✅ All 3 critical backend bugs fixed
- ✅ CloudScape migration complete (100%)
- ✅ Authentication issues resolved (Session 68)
- ⚠️ DRS drill validation pending (ec2:DetachVolume fix applied)

**Performance Metrics**
- ExecutionFinder: 20s detection (3x faster than target)
- StatusIndex GSI: <21ms queries (4x faster than target)
- ExecutionPoller: Every ~15s adaptive polling
- EventBridge: 100% reliability (30/30 triggers)
- Error Rate: 0% (zero errors in 120 invocations)
