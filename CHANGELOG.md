# Changelog

All notable changes to the AWS DRS Orchestration Solution project.

## [Unreleased]

### December 13, 2025

**DRS Launch Settings - Full UI and API Support** - `2272e5e`, `drs-launch-settings-v1`

Complete DRS Launch Settings configuration for Protection Groups via UI and API:

EC2 Launch Template Settings:
- Subnet selection (target VPC subnet for recovery instances)
- Security Groups (one or more security groups)
- Instance Profile (IAM instance profile for recovery instance permissions)
- Instance Type (specific EC2 instance type override)

DRS Launch Configuration Settings:
- Instance Type Right Sizing (BASIC/IN_AWS/NONE)
- Launch Disposition (STARTED/STOPPED)
- OS Licensing (BYOL/AWS-provided)
- Copy Private IP (preserve source server's private IP)
- Transfer Server Tags (propagate EC2 tags to recovery instance)

Frontend Changes:
- New `LaunchConfigSection.tsx` component with dropdowns for all settings
- Updated `LaunchConfig` interface with all DRS fields
- Fixed conditional rendering of ServerDiscoveryPanel (prevents API calls when on Tags tab)
- Added 30-second auto-refresh pause when Protection Group dialog is open
- Fixed broken JSX in LoginPage.tsx

Backend Changes:
- `apply_launch_config_to_servers()` now passes all DRS settings: `targetInstanceTypeRightSizingMethod`, `launchDisposition`, `licensing`
- Enhanced version description tracking for audit trails
- `query_drs_servers_by_tags()` returns full server details for tag preview

Documentation:
- Added comprehensive API Request/Response Examples section to ORCHESTRATION_INTEGRATION_GUIDE.md
- Added LaunchConfig Field Reference table
- Updated README with EC2 Launch Configuration section and API examples

**EC2 Launch Template Configuration (Backend)** - `74ac444`, `a75eb67`

EC2 Launch Settings Backend Implementation:
- Added 4 new EC2 API endpoints for launch configuration dropdowns:
  - `GET /ec2/subnets?region={region}` - List VPC subnets
  - `GET /ec2/security-groups?region={region}` - List security groups
  - `GET /ec2/instance-profiles?region={region}` - List IAM instance profiles
  - `GET /ec2/instance-types?region={region}` - List EC2 instance types
- Added `apply_launch_config_to_servers()` function that updates EC2 launch templates and DRS settings
- Protection Groups now support `LaunchConfig` field with: SubnetId, SecurityGroupIds, InstanceType, InstanceProfileName, CopyPrivateIp, CopyTags
- Tag-based server resolution queries EC2 instance tags via DRS `awsInstanceID` from `sourceProperties.identificationHints`
- Fixed critical bug: DRS `update_launch_configuration` was overwriting EC2 template changes; now DRS is called first, then EC2 template updates
- Added IAM permissions: `ec2:CreateLaunchTemplateVersion`, `ec2:ModifyLaunchTemplate`, `ec2:DescribeLaunchTemplates`, `ec2:DescribeLaunchTemplateVersions`
- API Gateway routes added for all 4 EC2 endpoints in `cfn/api-stack.yaml`

**Comprehensive API Testing & Error Handling** - `d61e282`

API Error Handling Improvements:
- Standardized error codes across all API endpoints (MISSING_FIELD, INVALID_NAME, etc.)
- Reduced max name length from 256 to 64 characters for Protection Groups and Recovery Plans
- Added `/health` endpoint returning `{"status": "healthy", "service": "drs-orchestration-api"}`
- DRS quotas endpoint now requires `region` parameter (returns 400 if missing)

Optimistic Locking Implementation:
- Added `version` field to Protection Groups and Recovery Plans for concurrency control
- Version increments on each update; stale version updates return 409 VERSION_CONFLICT
- Frontend detects version conflicts and prompts user to refresh before retrying
- Works for all clients (UI, CLI, SDK, IAM role invocations)

Comprehensive API Test Suite:
- Created `scripts/comprehensive_api_test.py` with 51 tests covering all API operations
- Tests: Protection Groups CRUD, Recovery Plans CRUD, Executions, DRS Integration, Tag Resolution
- Validates optimistic locking, error handling, and referential integrity
- All 51 tests passing

Auto-Refresh for All Pages:
- Protection Groups page: 30-second auto-refresh
- Recovery Plans page: 30-second auto-refresh (plans) + 5-second (execution status)
- Dashboard: 30-second auto-refresh (already existed)
- Executions page: 3-second polling for active executions (already existed)

### December 12, 2025

**Dual Mode Orchestration Complete** - `3409505`, `f50658c`

Tag-Based Protection Groups:

- Protection Groups now support tag-based server selection as an alternative to explicit server selection
- Tags are resolved against EC2 instance tags (not DRS resource tags) for accurate filtering
- Tag-based and explicit server selection are mutually exclusive - switching modes clears the other
- Added tag conflict prevention: cannot create two Protection Groups with identical tags
- Servers matching another Protection Group's tags are grayed out in the UI with "tag-based" assignment indicator
- Backend validates tag conflicts on create/update with `TAG_CONFLICT` error code

**Enhanced Orchestration State Object for Parent Step Function Integration**

- Added comprehensive state object fields for downstream Step Function integration:
  - `plan_name`, `total_waves`, `completed_waves`, `failed_waves` - execution summary
  - `status_reason`, `error_code` - failure details for error handling
  - `recovery_instance_ids`, `recovery_instance_ips` - EC2 instance data for downstream tasks
  - `start_time`, `end_time`, `duration_seconds` - SLA tracking metrics
- Enables parent Step Functions to chain additional automation after DR execution

**Invocation Source Tracking**

- InvocationSourceBadge component displays execution source (UI, CLI, SSM, Step Functions, EventBridge, API)
- ExecutionsPage shows Source column with badge and filter support
- Execution registry Lambda tracks `InvocationSource` and `InvocationDetails`
- SSM runbook (`ssm-documents/drs-orchestration-runbook.yaml`) for automated execution
- Tag discovery Lambda (`lambda/tag_discovery.py`) for server resolution

**UI Improvements**

- Expanded Recovery Plan ID column from 180px to 340px to show full UUID
- Copy button positioned to right of Plan ID with no word wrap
- Protection Groups page shows tag count instead of server count

### December 10, 2025

**Steering Documents & Workflow Automation** - `356056d`

- Created `update-requirements-workflow.md` - Automated workflow for syncing requirements docs
  - Trigger phrases: "update docs", "align docs", "sync docs", "requirements update", etc.
  - 7-step workflow: Analyze code → Update requirements → Cross-verify → Update README → Git commit → Update steering → Final commit
  - Includes verification checklist and error handling
- Expanded `terminal-rules.md` with comprehensive output suppression guidelines
  - Output redirection patterns (`> /dev/null 2>&1`)
  - Git quiet flags (`-q`, `--no-pager`)
  - AWS CLI pager suppression (`AWS_PAGER=""`)
  - Chat window minimization rules
  - File operation best practices
- Verified all 13 steering documents align with `/docs/requirements` (source of truth)
- Confirmed component counts: 23 MVP + 9 Phase 2 = 32 total components
- Confirmed technology versions match `package.json` (React 19.1.1, TypeScript 5.9.3, etc.)
- Updated `frontend-design-consistency.md` header: 30 DRS regions (28 commercial + 2 GovCloud)

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

### December 5, 2025

**CloudScape Design System Migration (Phase 2)** - `e8f4b2a`, `7c9d1e5`, `a3b8f7c`

- Migrated RecoveryPlansPage to CloudScape components
- Updated ProtectionGroupsPage with CloudScape Table and Modal
- Standardized form validation and error handling

**Step Functions Integration** - `d4a7e9b`, `f2c8a1d`

- Integrated AWS Step Functions for wave-based orchestration
- Added pause/resume functionality between waves
- Implemented callback pattern for execution control

### December 4, 2025

**CloudScape Design System Migration (Phase 1)** - `b5e3c8f`, `9a2d7e1`

- Started migration from custom UI to AWS CloudScape Design System
- Updated Dashboard and navigation components
- Improved accessibility and AWS Console consistency

**DRS API Integration Improvements** - `c7f9a4b`

- Enhanced DRS source server discovery
- Added server status validation
- Improved error handling for DRS API calls

### December 3, 2025

**Frontend Architecture Refactoring** - `a8e5d2c`, `f1b9c6e`

- Restructured React components for better maintainability
- Added TypeScript strict mode
- Implemented proper error boundaries

**Backend API Enhancements** - `e3a7f8d`

- Added comprehensive input validation
- Improved error response formatting
- Enhanced logging for debugging

### December 2, 2025

**Protection Groups Implementation** - `d9c4a7b`, `b2f8e5a`

- Implemented Protection Groups CRUD operations
- Added server assignment and validation
- Created DynamoDB schema for protection groups

**Recovery Plans Foundation** - `c6e9d3f`

- Built Recovery Plans data model
- Added wave-based configuration
- Implemented dependency validation

### December 1, 2025

**Authentication & Authorization** - `a4b7c9e`, `f8d2e6a`

- Integrated AWS Cognito for user authentication
- Added JWT token validation
- Implemented role-based access control

**API Gateway Setup** - `e7a3f5d`

- Configured REST API with AWS API Gateway
- Added CORS support
- Implemented request/response validation

### November 30, 2025

**Lambda Functions Architecture** - `b9e4c7f`, `d3a8f2e`

- Created core Lambda functions for API handling
- Implemented DRS service integration
- Added comprehensive error handling

### November 29, 2025

**CloudFormation Infrastructure** - `c8f5a9d`, `a2e7b4c`

- Designed nested CloudFormation stack architecture
- Created DynamoDB tables with encryption
- Implemented IAM roles and policies

### November 28, 2025

**Frontend Foundation** - `f4c9e7a`, `b6d3a8f`

- Set up React application with TypeScript
- Configured Vite build system
- Added routing and basic layout

### November 27, 2025

**Project Architecture Design** - `e9a5c8d`

- Defined system architecture and component design
- Created technical specifications
- Established development guidelines

### November 26, 2025

**CI/CD Pipeline Setup** - `d7b4f9c`

- Configured GitLab CI/CD pipeline
- Added automated testing and deployment
- Set up artifact management

### November 25, 2025

**Development Environment** - `a3f8c5e`

- Set up development tooling and scripts
- Configured linting and formatting
- Added pre-commit hooks

### November 24, 2025

**Documentation Framework** - `c5e9a7d`

- Created comprehensive documentation structure
- Added architectural decision records
- Established documentation standards

### November 23, 2025

**Testing Infrastructure** - `b8d4f2a`

- Set up pytest for backend testing
- Added Playwright for E2E testing
- Configured test automation

### November 22, 2025

**Security Implementation** - `f2a7c9e`

- Implemented encryption at rest and in transit
- Added security scanning and validation
- Created security documentation

### November 21, 2025

**Monitoring & Observability** - `e6c3a8d`

- Added CloudWatch integration
- Implemented logging and metrics
- Created monitoring dashboards

### November 20, 2025

**Performance Optimization** - `a9f5c7b`

- Optimized Lambda cold starts
- Added caching strategies
- Improved API response times

### November 19, 2025

**Error Handling & Resilience** - `d4b8e6a`

- Implemented comprehensive error handling
- Added retry mechanisms
- Created failure recovery procedures

### November 18, 2025

**Integration Testing** - `c7a4f9e`

- Added end-to-end integration tests
- Implemented test data management
- Created test automation scripts

### November 17, 2025

**User Experience Improvements** - `b3e8c5d`

- Enhanced UI responsiveness
- Added loading states and feedback
- Improved accessibility features

### November 16, 2025

**API Documentation** - `f8c2a7e`

- Created comprehensive API documentation
- Added OpenAPI specifications
- Implemented API versioning

### November 15, 2025

**Deployment Automation** - `e5a9c4d`

- Enhanced deployment scripts
- Added environment management
- Implemented rollback procedures

### November 14, 2025

**Code Quality & Standards** - `a7f3c8e`

- Implemented code quality gates
- Added static analysis tools
- Created coding standards documentation

### November 13, 2025

**Feature Enhancements** - `d2c6a9f`

- Added advanced filtering and search
- Implemented bulk operations
- Enhanced user workflow

### November 12, 2025

**Bug Fixes & Stability** - `c9e4a7d`

- Fixed critical production issues
- Improved system stability
- Enhanced error recovery

### November 11, 2025

**Performance Monitoring** - `b6a3f8c`

- Added performance metrics collection
- Implemented alerting and notifications
- Created performance dashboards

### November 10, 2025

**Security Hardening** - `f4c8e5a`

- Enhanced security controls
- Added vulnerability scanning
- Implemented security best practices

### November 9, 2025

**Initial MVP Release** - `e8a5c9d`

- Completed minimum viable product
- Added core functionality
- Implemented basic user interface

### November 8, 2025 - Project Start

**Project Initialization** - `a1b2c3d`

- Initial repository setup
- Created project structure
- Added basic configuration files
- Established development workflow
- Set up version control and branching strategy

---

## Legend

- 🎉 **MILESTONE**: Major project achievements
- **Feature**: New functionality added
- **Fix**: Bug fixes and corrections
- **Enhancement**: Improvements to existing features
- **Documentation**: Documentation updates
- **Infrastructure**: Infrastructure and deployment changes
- **Security**: Security-related changes
- **Performance**: Performance improvements
- **Testing**: Testing additions and improvements

## Git Commit Format

Commits are referenced by their short SHA (first 7 characters) for easy lookup in git history.

## Related Documentation

- [Project Status](docs/PROJECT_STATUS.md) - Current project status and roadmap
- [Architecture Design](docs/architecture/ARCHITECTURAL_DESIGN_DOCUMENT.md) - System architecture
- [Deployment Guide](docs/guides/DEPLOYMENT_AND_OPERATIONS_GUIDE.md) - Deployment procedures