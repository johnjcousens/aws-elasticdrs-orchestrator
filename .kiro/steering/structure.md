# Project Structure

## Repository Organization

```
AWS-DRS-Orchestration/
├── cfn/                          # CloudFormation templates (IaC)
│   ├── master-template.yaml      # Root orchestrator (336 lines)
│   ├── database-stack.yaml       # DynamoDB tables (130 lines)
│   ├── lambda-stack.yaml         # Lambda functions + IAM (408 lines)
│   ├── api-stack.yaml            # Cognito + API Gateway + Step Functions (696 lines)
│   ├── security-stack.yaml       # WAF + CloudTrail + Secrets Manager (648 lines)
│   └── frontend-stack.yaml       # S3 + CloudFront + custom resources (361 lines)
│
├── frontend/                     # React SPA (2,847 lines TypeScript)
│   ├── src/
│   │   ├── components/           # 18+ reusable components
│   │   │   ├── ProtectionGroupDialog.tsx    # Create/Edit Protection Groups
│   │   │   ├── RecoveryPlanDialog.tsx       # Create/Edit Recovery Plans
│   │   │   ├── ServerSelector.tsx           # Visual server selection
│   │   │   ├── RegionSelector.tsx           # AWS region dropdown
│   │   │   ├── StatusBadge.tsx              # Status indicators
│   │   │   ├── WaveProgress.tsx             # Wave execution timeline
│   │   │   ├── DateTimeDisplay.tsx          # Timestamp formatting
│   │   │   ├── ConfirmDialog.tsx            # Confirmation dialogs
│   │   │   └── ...
│   │   ├── pages/                # 5 page components
│   │   │   ├── LoginPage.tsx                # Cognito authentication
│   │   │   ├── Dashboard.tsx                # Overview metrics (placeholder)
│   │   │   ├── ProtectionGroupsPage.tsx    # Protection Groups CRUD
│   │   │   ├── RecoveryPlansPage.tsx       # Recovery Plans CRUD
│   │   │   └── ExecutionsPage.tsx          # Execution monitoring
│   │   ├── services/             # API client (api.ts)
│   │   ├── contexts/             # AuthContext for authentication
│   │   ├── theme/                # CloudScape theme configuration
│   │   └── types/                # TypeScript interfaces
│   ├── public/                   # Static assets
│   ├── dist/                     # Build output (gitignored)
│   ├── package.json              # Dependencies
│   ├── vite.config.ts            # Vite configuration
│   ├── build.sh                  # Build script with AWS config injection
│   └── dev.sh                    # Development server script
│
├── lambda/                       # Lambda function code
│   ├── index.py                  # Main API handler (912 lines Python)
│   ├── orchestration.py          # DRS recovery orchestration (556 lines)
│   ├── execution_finder.py       # Discover PENDING executions
│   ├── execution_poller.py       # Poll DRS job status
│   ├── requirements.txt          # Python dependencies
│   ├── deploy_lambda.py          # Automated deployment script
│   ├── package/                  # Python dependencies (1,833 files)
│   ├── api-handler.zip           # Pre-built Lambda package (11.09 MB)
│   ├── orchestration.zip         # Pre-built orchestration package
│   └── frontend-builder.zip      # Pre-built frontend builder package
│
├── tests/                        # Test suites
│   └── playwright/               # E2E tests
│       ├── smoke-tests.spec.ts   # Smoke tests
│       ├── playwright.config.ts  # Test configuration
│       ├── auth-helper.ts        # Authentication helper
│       ├── page-objects/         # Page object models
│       └── test-results/         # Test artifacts (gitignored)
│
├── docs/                         # Documentation
│   ├── requirements/             # Requirements & Specifications
│   │   ├── PRODUCT_REQUIREMENTS_DOCUMENT.md      # PRD (2,995 lines)
│   │   ├── SOFTWARE_REQUIREMENTS_SPECIFICATION.md # SRS (functional requirements)
│   │   └── UX_UI_DESIGN_SPECIFICATIONS.md        # UI/UX specs
│   ├── architecture/             # Architecture & Design
│   │   ├── ARCHITECTURAL_DESIGN_DOCUMENT.md      # ADD (1,727 lines)
│   │   └── AWS-DRS-Orchestration-Architecture.drawio # Architecture diagram
│   ├── guides/                   # Deployment & Operations
│   │   ├── DEPLOYMENT_AND_OPERATIONS_GUIDE.md    # Deployment guide
│   │   ├── TESTING_AND_QUALITY_ASSURANCE.md      # Testing guide
│   │   ├── MVP_PHASE1_DRS_INTEGRATION.md         # Phase 1 implementation
│   │   ├── AWS_DRS_API_REFERENCE.md              # DRS API docs
│   │   ├── DRS_SRM_API_MAPPING.md                # VMware SRM mapping
│   │   └── DR_SOLUTIONS_API_COMPARISON.md        # API comparison
│   ├── competitive-analysis/     # Market Analysis
│   │   ├── DR_SOLUTIONS_COMPARISON.md            # Feature comparison
│   │   ├── DR_SOLUTIONS_SALES_BATTLECARD.md      # Sales guidance
│   │   └── disaster_recovery_solutions___competitive_analysis.md
│   ├── archive/                  # Historical documentation
│   ├── PROJECT_STATUS.md         # Session history & current status
│   ├── SESSION_63_HANDOFF_TO_KIRO.md # Latest handoff document
│   ├── LAMBDA_DEPLOYMENT_GUIDE.md # Lambda deployment automation
│   ├── MASTER_IMPLEMENTATION_ROADMAP.md # Feature consolidation plan
│   ├── STEP_FUNCTIONS_DESIGN_PLAN.md # Phase 3 architecture
│   ├── DRILL_LIFECYCLE_MANAGEMENT_PLAN.md # Drill termination feature
│   └── AWS_DRS_ORCHESTRATION_TCO_ANALYSIS_FIXED.md # Cost analysis
│
├── scripts/                      # Utility scripts
│   ├── create-test-user.sh       # Create Cognito test user
│   ├── package-frontend-builder.sh # Package frontend builder Lambda
│   ├── run-tests.sh              # Run test suite
│   ├── validate-templates.sh     # Validate CloudFormation templates
│   └── sync-to-deployment-bucket.sh # Sync repository to S3
│
├── ssm-documents/                # SSM automation documents
│   └── post-launch-health-check.yaml # Health check automation
│
├── .kiro/                        # Kiro configuration
│   ├── steering/                 # Steering documents
│   │   ├── product.md            # Product overview
│   │   ├── tech.md               # Technology stack
│   │   └── structure.md          # Project structure
│   └── specs/                    # Feature specifications
│       └── execution-engine-testing/ # Execution engine testing spec
│
├── .env.test                     # Test environment configuration
├── .env.test.template            # Environment template
├── Makefile                      # Build automation
├── README.md                     # Project overview (1,081 lines)
└── .gitignore                    # Git ignore rules
```

## Key Directories

### `/cfn` - Infrastructure as Code
All CloudFormation templates using nested stack architecture. Each stack is modular and under 750 lines for maintainability.

**Modular Design Benefits**:
- Single-command deployment via master template
- Independent stack updates without full redeployment
- Clear separation of concerns (database, compute, API, security, frontend)
- Professional AWS patterns with proper dependencies

**Quality Standards**:
- Multi-partition ARN support (AWS Standard, GovCloud, China)
- Data protection with deletion policies
- cfn-lint validation (zero errors)
- AWS validate-template compliance

### `/frontend` - React Application
Single-page application with TypeScript. Components follow AWS CloudScape Design System patterns. API calls centralized in `services/api.ts`.

**Key Features**:
- 23 React components (5 pages + 18 shared)
- ~3,000 lines of TypeScript code
- AWS CloudScape Design System (migrated from Material-UI Dec 2025)
- Automatic server discovery with real-time search
- VMware SRM-like visual server selection
- 30-second auto-refresh for server status
- Responsive design (desktop, tablet, mobile)
- WCAG 2.1 AA accessibility compliance

**Component Architecture**:
- **Pages**: Route-level components with data fetching
- **Dialogs**: Modal forms for CRUD operations
- **Selectors**: Complex input components with validation
- **Display**: Read-only presentation components
- **Utilities**: Shared helpers and formatters

### `/lambda` - Backend Logic
Python Lambda functions. Main handler (`index.py`) routes requests and implements business logic. Pre-built .zip files ready for deployment.

**Lambda Functions**:
1. **api-handler** (912 lines): Main API logic
   - CRUD operations for Protection Groups, Recovery Plans
   - DRS server discovery with assignment tracking
   - Execution management and history queries
   - Request routing and validation

2. **orchestration** (556 lines): DRS recovery orchestration
   - Wave-based execution workflow
   - DRS API integration (StartRecovery, DescribeJobs)
   - Job status monitoring and health checks
   - Error handling and retry logic

3. **execution-finder**: Discover PENDING executions
   - EventBridge scheduled (every 60 seconds)
   - Queries StatusIndex GSI for active executions
   - Triggers ExecutionPoller for each active execution
   - Performance: 20s detection (3x faster than target)

4. **execution-poller**: Poll DRS job status
   - Adaptive polling (every ~15s)
   - Updates execution records with job status
   - Automatic cleanup when execution completes
   - Zero error rate in production

5. **frontend-builder**: Automated frontend deployment
   - React build with Vite
   - S3 sync with CloudFront invalidation
   - AWS config injection

6. **s3-cleanup**: Custom resource for stack deletion
   - Empties S3 buckets before deletion
   - Prevents CloudFormation deletion failures

**Deployment Automation**:
- `deploy_lambda.py`: Automated deployment script
- Multiple deployment modes (direct, S3, CloudFormation, full)
- Automatic packaging with dependencies
- See `docs/LAMBDA_DEPLOYMENT_GUIDE.md` for details

### `/tests` - Test Suites
Playwright E2E tests with page object pattern. Tests run against deployed CloudFront distribution.

**Test Coverage**:
- Smoke tests for critical user flows
- Page object models for maintainability
- Authentication helper for Cognito integration
- Test results with screenshots and traces

### `/docs` - Comprehensive Documentation
Product requirements, architecture design, deployment guides, and session history. All documents are markdown format.

**Documentation Structure**:
- **requirements/**: PRD, SRS, UX/UI specs (comprehensive requirements)
- **architecture/**: ADD, architecture diagrams (system design)
- **guides/**: Deployment, testing, API references (operational docs)
- **competitive-analysis/**: Market analysis, sales battlecards
- **archive/**: Historical session notes and debugging guides

**Key Documents**:
- `PRODUCT_REQUIREMENTS_DOCUMENT.md`: 2,995 lines - Product vision, features, cost analysis
- `SOFTWARE_REQUIREMENTS_SPECIFICATION.md`: Functional requirements, API specs, data models
- `UX_UI_DESIGN_SPECIFICATIONS.md`: UI design, component library, interaction patterns
- `ARCHITECTURAL_DESIGN_DOCUMENT.md`: 1,727 lines - System architecture, technical design
- `PROJECT_STATUS.md`: Session history, current status, implementation tracking
- `SESSION_63_HANDOFF_TO_KIRO.md`: Latest handoff document with 24-hour work summary

## File Naming Conventions

- **CloudFormation**: `kebab-case-stack.yaml`
- **TypeScript/React**: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- **Python**: `snake_case.py`
- **Documentation**: `SCREAMING_SNAKE_CASE.md` for major docs, `kebab-case.md` for guides
- **Scripts**: `kebab-case.sh`

## Code Organization Patterns

### Frontend Components

**Pages** (Route-level components)
- `LoginPage.tsx`: Cognito authentication with username/password
- `Dashboard.tsx`: Overview metrics and quick actions (placeholder in MVP)
- `ProtectionGroupsPage.tsx`: Protection Groups CRUD with server discovery
- `RecoveryPlansPage.tsx`: Recovery Plans CRUD with wave configuration
- `ExecutionsPage.tsx`: Execution monitoring and history

**Dialogs** (Modal forms)
- `ProtectionGroupDialog.tsx`: Create/Edit Protection Groups with server selection
- `RecoveryPlanDialog.tsx`: Create/Edit Recovery Plans with wave configuration
- `ConfirmDialog.tsx`: Confirmation dialogs for destructive actions

**Selectors** (Complex input components)
- `ServerSelector.tsx`: Visual server selection with assignment status
- `RegionSelector.tsx`: AWS region dropdown (13 regions)
- `TagFilterEditor.tsx`: Tag-based server filtering

**Display** (Read-only components)
- `StatusBadge.tsx`: Status indicators with color coding
- `WaveProgress.tsx`: Wave execution timeline with CloudScape Wizard/Stepper
- `DateTimeDisplay.tsx`: Timestamp formatting with relative time

### Backend Lambda

**API Handler** (`index.py`)
- `lambda_handler()`: Routes requests by HTTP method and path
- `handle_protection_groups()`: Protection Groups CRUD operations
- `handle_recovery_plans()`: Recovery Plans CRUD operations
- `handle_executions()`: Execution management and history
- `handle_drs_source_servers()`: DRS server discovery with assignment tracking

**Data Transformers**
- `transform_pg_to_camelcase()`: DynamoDB PascalCase → Frontend camelCase
- `transform_rp_to_camelcase()`: Recovery Plan transformation
- `transform_execution_to_camelcase()`: Execution history transformation

**Validators**
- `validate_unique_pg_name()`: Case-insensitive unique name enforcement
- `get_assigned_servers()`: Server assignment tracking across Protection Groups
- `validate_wave_dependencies()`: Circular dependency detection

**DRS Integration** (`orchestration.py`)
- `start_recovery()`: Initiate DRS recovery jobs
- `monitor_jobs()`: Poll DRS job status until completion
- `perform_health_checks()`: Validate EC2 instance health
- `update_execution_status()`: Update DynamoDB with execution progress

**Polling Infrastructure**
- `execution_finder.py`: Discover PENDING executions via StatusIndex GSI
- `execution_poller.py`: Poll DRS job status and update execution records

### CloudFormation Stacks

**Master Template** (`master-template.yaml`)
- Orchestrates all nested stacks
- Propagates parameters to child stacks
- Aggregates outputs from nested stacks
- Manages stack dependencies

**Database Stack** (`database-stack.yaml`)
- Creates 3 DynamoDB tables with encryption & PITR
- StatusIndex GSI for execution queries
- On-demand capacity mode
- Backup retention policies

**Lambda Stack** (`lambda-stack.yaml`)
- Creates 4 Lambda functions with IAM roles
- CloudWatch Log Groups with retention
- DRS permissions for recovery operations
- Multi-partition ARN support

**API Stack** (`api-stack.yaml`)
- Cognito User Pool with email verification
- API Gateway REST API (30+ resources)
- Step Functions state machine (35+ states)
- EventBridge rules for polling infrastructure

**Security Stack** (`security-stack.yaml`)
- WAF for API protection (optional)
- CloudTrail for audit logging (optional)
- Secrets Manager for sensitive data (optional)

**Frontend Stack** (`frontend-stack.yaml`)
- S3 bucket with encryption
- CloudFront distribution with HTTPS
- Custom resources for frontend build
- Automated React build & deployment

## Data Flow

### User-Initiated Recovery Execution

1. **User Action** → Frontend (React)
   - User clicks "Execute Recovery Plan" button
   - RecoveryPlanDialog opens with execution options

2. **API Call** → API Gateway (with Cognito JWT auth)
   - POST /executions with PlanId, ExecutionType (DRILL/RECOVERY)
   - API Gateway validates JWT token via Cognito authorizer

3. **Lambda Invocation** → API Handler Lambda
   - `handle_executions()` creates execution record
   - Status: PENDING, stores in DynamoDB execution-history table

4. **EventBridge Trigger** → ExecutionFinder Lambda
   - Scheduled every 60 seconds
   - Queries StatusIndex GSI for PENDING executions
   - Invokes ExecutionPoller for each active execution

5. **Polling Loop** → ExecutionPoller Lambda
   - Retrieves Recovery Plan from DynamoDB
   - Calls DRS StartRecovery API for each wave
   - Polls DRS DescribeJobs API every 30 seconds
   - Updates execution status: PENDING → POLLING → LAUNCHING → COMPLETED

6. **Database Updates** → DynamoDB
   - ExecutionPoller updates execution-history table
   - Wave-level status tracking
   - Job IDs and server status

7. **Response** → Frontend updates UI
   - ExecutionsPage polls GET /executions/{id} every 5 seconds
   - WaveProgress component shows real-time status
   - CloudScape Wizard/Stepper displays wave timeline

### Protection Group Creation Flow

1. **User Action** → Frontend
   - User clicks "Create Protection Group"
   - ProtectionGroupDialog opens

2. **Server Discovery** → API Call
   - GET /drs/source-servers?region={region}
   - Returns all DRS servers with assignment status

3. **Server Selection** → Frontend
   - ServerSelector displays servers with badges
   - Available (green) vs Assigned (red)
   - Real-time search and filtering

4. **Create Request** → API Call
   - POST /protection-groups with name, region, serverIds
   - API Handler validates unique name and server availability

5. **Database Write** → DynamoDB
   - Creates Protection Group record
   - Stores server assignments

6. **Response** → Frontend
   - ProtectionGroupsPage refreshes table
   - New Protection Group appears in list

## Deployment Artifacts

### Lambda Packages
- **Location**: `/lambda` directory
- **api-handler.zip**: 11.09 MB (includes 1,833 dependency files)
- **orchestration.zip**: 5.5 KB (DRS recovery orchestration)
- **frontend-builder.zip**: 132 KB (React build automation)
- **Deployment**: Automated via `deploy_lambda.py` script

### Frontend Build
- **Location**: `/frontend/dist` (generated by Vite)
- **Size**: ~2 MB (minified, gzipped)
- **Deployment**: S3 sync + CloudFront invalidation
- **Config Injection**: AWS config embedded at build time

### CloudFormation Templates
- **Location**: `s3://aws-drs-orchestration/cfn/`
- **Versioning**: S3 versioning enabled
- **Git Tagging**: All objects tagged with git commit hash
- **Auto-Sync**: Git post-push hook syncs to S3 automatically

### Test Results
- **Location**: `/tests/playwright/test-results`
- **Artifacts**: Screenshots, traces, HTML reports
- **Retention**: Gitignored, generated on-demand

## S3 Repository Structure

```
s3://aws-drs-orchestration/
├── cfn/                          # CloudFormation templates
│   ├── master-template.yaml
│   ├── database-stack.yaml
│   ├── lambda-stack.yaml
│   ├── api-stack.yaml
│   ├── security-stack.yaml
│   └── frontend-stack.yaml
├── lambda/                       # Lambda packages
│   ├── api-handler.zip
│   ├── orchestration.zip
│   └── frontend-builder.zip
└── frontend/                     # Frontend build artifacts
    └── dist/
```

**Features**:
- ✅ S3 versioning enabled (every file version preserved)
- ✅ Git commit tagging (all objects tagged with source commit)
- ✅ Automated sync (git post-push hook)
- ✅ Query by commit (find all files from specific deployment)

## Environment-Specific Resources

Resources are named with environment suffix for multi-environment support:

**DynamoDB Tables**:
- `protection-groups-{env}`
- `recovery-plans-{env}`
- `execution-history-{env}`

**Lambda Functions**:
- `drs-orchestration-api-handler-{env}`
- `drs-orchestration-orchestration-{env}`
- `drs-orchestration-execution-finder-{env}`
- `drs-orchestration-execution-poller-{env}`
- `drs-orchestration-frontend-builder-{env}`

**S3 Buckets**:
- `drs-orchestration-fe-{account}-{env}`

**CloudFormation Stacks**:
- `drs-orchestration-{env}` (master)
- `drs-orchestration-{env}-database`
- `drs-orchestration-{env}-lambda`
- `drs-orchestration-{env}-api`
- `drs-orchestration-{env}-security`
- `drs-orchestration-{env}-frontend`

### Current Environments

**test** (Fully operational)
- **Region**: us-east-1
- **Account**: 438465159935
- **Frontend**: https://d1wfyuosowt0hl.cloudfront.net
- **API**: https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test
- **Status**: ✅ All stacks deployed, ⚠️ DRS validation pending

**dev** (Not deployed)
- Planned for development testing

**prod** (Not deployed)
- Planned for production deployment

## Git Repository

**Repository**: `git@ssh.code.aws.dev:personal_projects/alias_j/jocousen/AWS-DRS-Orchestration.git`

**Branches**:
- `main`: Primary development branch
- Feature branches as needed

**Tags**:
- `Best-Known-Config` (Commit: bfa1e9b): Validated production-ready configuration
- `v1.0.0-backend-integration-prototype` (Commit: 14d1263): Backend integration prototype
- `v1.0.2-drs-integration-working` (Commit: 40cac85): Full DRS integration operational

**Latest Commit**: 30321bb - Lambda deployed with all 3 critical bug fixes (Nov 28, 2025)

**Rollback Command**: `git checkout Best-Known-Config && git push origin main --force`
