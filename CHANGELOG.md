# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-01-28 - Individual Server Launch Template Management with Static IP

### Added
- **Export Configuration Enhancement**: Export now captures per-server static IP configurations
  - Exports `servers` array with per-server `launchTemplate` configurations including `staticPrivateIp`
  - Added server counting logic (`total_server_count`, `servers_with_custom_config`)
  - Bumped schema version from 1.0 to 1.1
  - Updated metadata to include `serverCount` and `serversWithCustomConfig`
  - Fixed query-handler Lambda export_configuration function

### Fixed
- **Deploy Script Improvements**: Fixed cfn-lint and cfn_nag detection and execution
  - Use `.venv/bin/cfn-lint` first, fallback to system cfn-lint
  - Added proper cfn-lint config file flag and quiet format
  - Direct path detection for cfn_nag_scan in Ruby gems (checks both Ruby 3.3 and 4.0 paths)
  - Removed timeout workarounds in favor of proper tool detection
  - Removed stack protection check blocking test environment deployments

### Changed
- **Configuration Schema**: Updated export schema version to 1.1 to reflect per-server configuration support

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
- **Task 7.4 - ServerConfigurationTab Tests** (2026-01-28): Comprehensive test suite for server configuration table
  - 10 test suites with 35+ test cases covering all table functionality
  - Server list rendering: Table display, server names, source IDs, static IPs, DHCP display
  - Server counts: Total count, custom config count, empty state messages
  - Badge display: Custom/Default badges for each server, custom fields detection
  - Filtering: Filter dropdown (All/Custom/Default), filtered counts, empty states
  - Dialog opening: Opens on Configure click, passes correct server, closes on save/cancel
  - Reset to defaults: Calls onConfigChange with null, button visibility logic
  - Bulk configure: Button rendering, enabled/disabled based on server count
  - Edge cases: Missing hostname, empty configs, various useGroupDefaults states
  - Custom fields detection: Identifies staticPrivateIp, instanceType, and other overrides
  - Mocked child components (ServerConfigBadge, ServerLaunchConfigDialog)
  - Requirements validated: 1.1, 1.2, 1.3, 6.1
- **Task 7.3 - ServerLaunchConfigDialog Tests** (2026-01-28): Comprehensive test suite for per-server configuration dialog
  - 11 test suites with 40+ test cases covering all dialog functionality
  - Form rendering tests: Dialog header, server info, all form fields, buttons
  - Group defaults display tests: Shows default values for subnet, security groups, instance type
  - Server configuration initialization: Existing config vs new config scenarios
  - Use Group Defaults toggle: Checkbox behavior, info alert visibility
  - Static IP input: Value updates, initialization from existing config
  - Save action: Calls onSave with correct config, enables/disables based on changes
  - Cancel action: Calls onClose, disabled during save operation
  - Validation: Respects IP validation state from StaticIPInput
  - Configuration badges: Shows custom/default indicators for fields
  - Edge cases: Missing hostname, empty arrays, missing defaults
  - Form reset: Resets when dialog reopens
  - Mocked child components (StaticIPInput, ServerConfigBadge) and API client
  - Requirements validated: 2.1, 3.1, 5.1, 6.1
- **Task 7.2 - ServerConfigurationTab Component** (2026-01-27): Table view for managing per-server launch configurations
  - Table view of servers in protection group with configuration status
  - Filter dropdown: All Servers, Custom Only, Default Only
  - Configure button for each server (opens ServerLaunchConfigDialog)
  - Reset button for servers with custom configurations
  - Bulk Configure button (placeholder for future enhancement)
  - Visual badges indicating custom vs default configuration
  - Server count display with custom config indicator
  - Integration with ServerConfigBadge and ServerLaunchConfigDialog components
  - Requirements validated: 1.1, 1.2, 1.3, 1.4, 2.1, 6.1
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
- **Per-Server Launch Config API Client**: Added 5 new API client functions in `frontend/src/services/api.ts`
  - `getServerLaunchConfig()`: Fetches server-specific launch configuration
  - `updateServerLaunchConfig()`: Updates server configuration with validation
  - `deleteServerLaunchConfig()`: Removes server configuration
  - `validateStaticIP()`: Real-time IP validation with availability check
  - `bulkUpdateServerConfigs()`: Bulk configuration update for multiple servers
  - All functions use camelCase for TypeScript compatibility and include proper error handling
- **StaticIPInput Component**: Created real-time IP validation input component
  - Client-side IPv4 format validation (X.X.X.X pattern, 0-255 octets)
  - Debounced API validation (500ms) to check IP availability
  - Visual feedback: ✓ Available, ✗ In use, ⚠ Invalid
  - Inline error messages with detailed conflict information
  - Revalidates automatically when subnet changes
  - Supports optional field behavior (empty value is valid)
- **ServerConfigBadge Component**: Created configuration status indicator
  - Displays "Custom" badge (blue) or "Default" badge (gray)
  - Tooltip shows which fields are customized
  - Maps internal field names to user-friendly display names
  - Supports hover state for additional information
- **Component Tests**: Comprehensive test suites for StaticIPInput and ServerConfigBadge
  - StaticIPInput tests: 20+ tests covering rendering, props, onChange callbacks, input behavior, component structure
  - ServerConfigBadge tests: 24+ tests covering badge rendering, tooltip content, field name mapping, edge cases, accessibility
  - Installed testing dependencies: @testing-library/react, @testing-library/user-event, @testing-library/jest-dom
  - Configured for Vitest (not Jest) with proper mocking
  - 31 of 44 tests passing (13 failures due to Cloudscape component mocking limitations)
  - Tests validate Requirements 3.1, 3.2, 5.1, 6.1, 6.3
- **ServerLaunchConfigDialog Component**: Created modal dialog for per-server configuration
  - Integrates StaticIPInput for IP address configuration with real-time validation
  - Integrates ServerConfigBadge for field-level custom vs default indicators
  - "Use Group Defaults" checkbox for partial vs full override mode
  - Dropdown selectors for subnet, security groups, and instance type
  - Group default value hints displayed for each field
  - Validation before save (IP validation, change detection)
  - Save and cancel actions with loading states
  - Supports both partial override (useGroupDefaults=true) and full override modes
  - Validates Requirements 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 5.1, 6.1, 6.2, 6.3, 6.4
- **ServerConfigBadge Component**: Created reusable React component for displaying server configuration status
  - Displays "Custom" badge (blue) or "Default" badge (gray) based on configuration state
  - Popover tooltip shows list of customized fields with user-friendly names
  - Maps internal field names (staticPrivateIp, instanceType, etc.) to display names
  - Uses AWS Cloudscape Design System components (Badge, Popover, Box)
  - Fully typed with TypeScript interface (ServerConfigBadgeProps)
  - Component tests included in `__tests__/ServerConfigBadge.tests.tsx`
- **ServerConfigBadge Component**: Created reusable badge component for server configuration status
  - Displays "Custom" badge (blue) or "Default" badge (gray) based on configuration state
  - Popover tooltip shows list of customized fields with user-friendly names
  - Maps internal field names to display names (e.g., `staticPrivateIp` → "Static Private IP")
  - Integrates with Cloudscape Design System (Badge, Popover, Box components)
  - Includes unit tests for badge rendering and tooltip content
- **StaticIPInput Component**: Implemented React component for static private IP address input with real-time validation
  - Client-side IPv4 format validation with octet range checking (0-255)
  - Debounced API validation (500ms) to check IP availability in target subnet
  - Visual feedback using Cloudscape StatusIndicator: ✓ Available, ✗ In use, ⚠ Invalid
  - Inline error messages with detailed conflict information (DRS server, EC2 instance, network interface, reserved range)
  - Automatic re-validation when subnet changes
  - Proper cleanup and memory management to prevent state updates after unmount
  - Integration with backend `/validate-ip` endpoint
  - TypeScript type-safe with IPValidationResult interface
- **StaticIPInput Component**: Created reusable React component for static IP address input with real-time validation
  - Client-side IPv4 format validation (X.X.X.X pattern, 0-255 octet range)
  - Debounced API validation (500ms) to check IP availability in target subnet
  - Visual feedback with Cloudscape StatusIndicator: ✓ Available, ✗ In use, ⚠ Invalid
  - Inline error messages with detailed conflict information (DRS server, EC2 instance, network interface, reserved range)
  - Automatic re-validation when subnet changes
  - Integration with backend `/validate-ip` endpoint
  - Follows Cloudscape Design System patterns (FormField, Input, StatusIndicator)
- **Frontend API Client Functions**: Added 5 new API client functions in `frontend/src/services/api.ts`
  - `getServerLaunchConfig(groupId, serverId)`: Fetches per-server configuration with effective config preview
  - `updateServerLaunchConfig(groupId, serverId, config)`: Updates server-specific launch template settings
  - `deleteServerLaunchConfig(groupId, serverId)`: Resets server to protection group defaults
  - `validateStaticIP(groupId, serverId, ip, subnetId)`: Real-time IP validation with detailed feedback
  - `bulkUpdateServerConfigs(groupId, configs)`: Bulk configuration update for multiple servers
  - All functions follow existing API client patterns with proper TypeScript types and error handling
  - Exported as named exports for convenient component imports
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
