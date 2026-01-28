# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Repository Maintenance
- **Git History Squash**: Consolidated 40 commits into single comprehensive MVP commit
  - Created tag `v1.0-MVP-SharedFunctionConsolidation_BugFixes_DocUpdates`
  - Preserved all historical commits in `archive/GitHistory/` (2.5GB)
  - Exported complete commit history to Desktop archive (769MB)
  - Simplified repository history while maintaining full historical record
  - All 12 historical tags preserved locally for reference
- **Tag Cleanup**: Removed 10 obsolete tags from GitHub (v1.0.0 through v2.1.0)
  - Kept 3 significant milestone tags: v1.0-MVP, v3.0.0, v4.0.0
  - All deleted tags remain in local repository and archives
  - Simplified GitHub releases view to show only major milestones

### Added
- **Per-Server Launch Template Customization Spec**: Comprehensive feature specification for static private IP assignment
  - Requirements document: 15 acceptance criteria covering static IP validation, AWS-approved fields, per-server UI workflows, import/export, conflict detection, and audit trails
  - Design document: Complete architecture with configuration hierarchy (group defaults + per-server overrides), 5 new frontend components, backend validation engine, 15 correctness properties for property-based testing
  - Implementation plan: 14 top-level tasks with 60+ sub-tasks covering backend foundation, API layer, frontend components, and CloudFormation updates
  - Code quality standards: Integrated black (line-length=79), flake8 (max-complexity=10), cfn-lint, and pre-commit hooks throughout all tasks
  - Lambda architecture analysis: Identified data-management-handler as owner of 5 new per-server config endpoints, verified all IAM permissions already exist in UnifiedOrchestrationRole
  - Current state analysis: Documented existing bulk configuration, import/export capabilities, and gaps requiring per-server override support
- **Per-Server Launch Config API Endpoints**: Implemented 5 new REST API endpoints in data-management-handler
  - `GET /protection-groups/{groupId}/servers/{serverId}/launch-config`: Returns server-specific config with effective config preview
  - `PUT /protection-groups/{groupId}/servers/{serverId}/launch-config`: Updates server config with full validation and DRS/EC2 application
  - `DELETE /protection-groups/{groupId}/servers/{serverId}/launch-config`: Removes server config and reverts to group defaults
  - `POST /protection-groups/{groupId}/servers/{serverId}/validate-ip`: Validates static IP format, CIDR range, and availability
  - `POST /protection-groups/{groupId}/servers/bulk-launch-config`: Bulk update multiple server configs with fail-fast validation
  - All endpoints use camelCase for frontend compatibility, include comprehensive validation, and record audit trails
- **Launch Config Validation Module**: Created `lambda/shared/launch_config_validation.py` with reusable validation functions
  - `validate_static_ip()`: Validates IPv4 format, CIDR range, reserved IPs, and availability via AWS API
  - `validate_aws_approved_fields()`: Enforces AWS-approved fields and blocks DRS-managed fields
  - `validate_security_groups()`: Validates security group IDs, format, and VPC membership
  - `validate_instance_type()`: Validates instance type availability in region
  - `validate_iam_profile()`: Validates IAM instance profile existence
  - `validate_subnet()`: Validates subnet existence and returns VPC details
  - All functions return detailed validation results with error codes and messages
- **Config Merge Module**: Created `lambda/shared/config_merge.py` with configuration hierarchy logic
  - `get_effective_launch_config()`: Merges group defaults with per-server overrides
  - Handles `useGroupDefaults` flag to control override behavior
  - Used by both data-management-handler and orchestration-stepfunctions for consistent config application
- **CI/CD Workflow Enforcement**: Added steering rules for mandatory deployment workflow using unified deploy script
  - Enforces use of `./scripts/deploy.sh` for all deployments with validation, security scanning, and testing stages
  - Prevents direct AWS CLI deployment commands to ensure quality gates and audit trails
  - Supports multiple deployment modes: full pipeline, quick (skip security/tests), lambda-only, frontend-only, skip-push
  - Built-in protections: concurrency detection, credential verification, validation gates, rollback recovery
- **AWS Stack Protection Rules**: Added steering rules to prevent accidental modification of production stacks
  - Protects production stacks with `-test` suffix from any modifications
  - Enforces use of `-dev` environment for development work
  - Provides verification checklist and emergency procedures
- **Configuration Export Example**: Added sample JSON manifest showing current export structure with protection groups, recovery plans, and metadata
- **Bug Fix Documentation**: Documented WaveConfigEditor.tsx fix for Protection Groups using individual server selection (sourceServerIds) instead of tag-based selection

### Changed
- **Shared Functions Consolidation**: Eliminated 638 lines of duplicate code across Lambda handlers
  - Created `lambda/shared/account_utils.py` with 4 account management functions
  - Enhanced `lambda/shared/drs_utils.py` with DRS state mapping function
  - Enhanced `lambda/shared/conflict_detection.py` with execution query function
  - Updated execution-handler to use shared response formatting
  - Added security headers (X-Content-Type-Options, X-Frame-Options) to all execution-handler responses
  - All 14 duplicate functions consolidated into shared modules
  - 100% test pass rate maintained (81 tests passing)

### Fixed
- **Test Infrastructure**: Added proper mocks for shared.response_utils in unit and integration tests
- **Code Formatting**: Applied black formatting to all Lambda code (79 character line length)

---

## [1.0.0] - 2026-01-27 - Initial Public Release

### Overview

Enterprise-grade disaster recovery orchestration for AWS Elastic Disaster Recovery (DRS) with wave-based execution, dependency management, and automated health checks.

### Features

#### Core Capabilities
- **Wave-Based Orchestration**: Execute disaster recovery in coordinated waves with dependency management
- **Step Functions Integration**: Long-running workflows with pause/resume capabilities
- **Protection Groups**: Tag-based server grouping with automatic discovery
- **Recovery Plans**: Multi-wave execution plans with manual validation points
- **Real-Time Control**: Resume, cancel, or terminate operations during execution

#### API & Integration
- **REST API**: 44 endpoints across 9 categories with RBAC security
- **Cross-Account Support**: Manage DRS across multiple AWS accounts
- **Direct Lambda Invocation**: Bypass API Gateway for AWS-native automation
- **Tag Synchronization**: Automated EC2 → DRS tag sync with EventBridge scheduling

#### User Interface
- **React Frontend**: Modern UI built with CloudScape Design System 3.0
- **Real-Time Updates**: Live execution status and wave progress
- **Role-Based Access**: 5 granular DRS-specific roles
- **CloudFront Distribution**: Global CDN for optimal performance

#### Infrastructure
- **Fully Serverless**: No infrastructure to manage, scales automatically
- **Cost-Effective**: $12-40/month operational cost
- **Multi-Region**: Supports all 30 AWS DRS regions
- **Encrypted**: All data encrypted at rest and in transit

### Architecture

#### Lambda Functions (6 Handlers)
- `data-management-handler`: Protection groups, recovery plans, configuration (21 endpoints)
- `execution-handler`: Recovery execution control, pause/resume, termination (11 endpoints)
- `query-handler`: Read-only queries, DRS status, EC2 discovery (12 endpoints)
- `orchestration-stepfunctions`: Step Functions orchestration with launch config sync
- `frontend-deployer`: Frontend deployment automation
- `notification-formatter`: SNS notification formatting

#### DynamoDB Tables (4 Tables)
- `protection-groups`: Server groupings with tag-based selection
- `recovery-plans`: Wave configurations with dependencies
- `execution-history`: Complete audit trail
- `target-accounts`: Multi-account configuration

#### CloudFormation Stacks (16 Templates)
- Modular nested stack architecture
- API Gateway split across 6 stacks for maintainability
- Unified orchestration role for simplified IAM management

### Deployment Modes

The solution supports 4 flexible deployment modes:

1. **Default Standalone**: Complete solution with frontend and IAM role
2. **API-Only Standalone**: Backend only for custom frontend or CLI/SDK
3. **External Role + Frontend**: External IAM integration with DRS UI
4. **Full External Integration**: External unified frontend with external IAM

### Technology Stack

- **Frontend**: React 19.1.1, TypeScript 5.9.3, CloudScape Design System 3.0
- **API**: Amazon API Gateway (REST), Amazon Cognito
- **Compute**: AWS Lambda (Python 3.12), AWS Step Functions
- **Database**: Amazon DynamoDB (native camelCase schema)
- **Hosting**: Amazon S3, Amazon CloudFront
- **DR Service**: AWS Elastic Disaster Recovery (DRS)

### Security & RBAC

#### Role-Based Access Control (5 Roles)
- **DRSOrchestrationAdmin**: Full administrative access
- **DRSRecoveryManager**: Recovery operations lead
- **DRSPlanManager**: DR planning focus
- **DRSOperator**: On-call operations
- **DRSReadOnly**: Audit and monitoring

#### Security Features
- Encryption at rest and in transit
- Cognito JWT token-based authentication (45-minute sessions)
- API-level RBAC enforcement
- Complete user action logging

### Documentation

Comprehensive documentation included:
- User guides (deployment, development, execution)
- API reference (44 endpoints)
- Architecture diagrams and specifications
- Troubleshooting guides
- CI/CD workflows

### Known Limitations

- Administrative DRS operations (disconnect/delete server) remain in DRS console
- E2E tests require live DRS environment for full validation
- Frontend requires modern browser with JavaScript enabled

---

## Future Releases

See [GitHub Issues](https://github.com/johnjcousens/aws-elasticdrs-orchestrator/issues) for planned features and enhancements.

---

**License**: MIT License - see LICENSE file for details

**Built for**: Enterprise disaster recovery on AWS
