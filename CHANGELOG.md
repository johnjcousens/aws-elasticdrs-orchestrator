# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.1] - January 6, 2026

### Fixed
- **Frontend API Config Loading Bug**: Fixed critical issue where `awsConfig` was cached at module load time instead of reading from `window.AWS_CONFIG` dynamically, causing API calls to fail with undefined endpoints
- **CloudFront Error Caching**: Reduced error response TTL from 300s to 10s to prevent prolonged caching of 403/404 errors during deployments
- **aws-config.json Values**: Corrected Cognito User Pool ID, Client ID, and API Gateway endpoint values

### Changed
- **Requirements Documents**: Updated to v2.2 with corrected technical specifications
- **API Configuration**: Refactored `api.ts` to use getter functions (`getApiEndpoint()`, `getAwsConfig()`) that read config dynamically at call time rather than module initialization

### Technical Details
- Root cause: ES module initialization order caused `window.AWS_CONFIG` to be undefined when `api.ts` was first imported
- Solution: Lazy evaluation pattern ensures config is read when API calls are made, not when module loads

## [1.3.0] - January 6, 2026

### Added
- **GitHub Actions CI/CD Pipeline**: Complete migration from AWS CodePipeline to GitHub Actions
  - OIDC-based authentication (no long-lived credentials)
  - 6-stage pipeline: Validate, Security Scan, Build, Test, Deploy Infrastructure, Deploy Frontend
  - S3-based CloudFormation validation for large templates (>51,200 bytes)
  - Automatic CloudFront cache invalidation on frontend deployment
  - SNS pipeline notifications enabled by default

### Fixed
- **CORS 403 Error on API Gateway**: Resolved OPTIONS preflight failures on `/accounts/targets` endpoint
  - Removed restrictive resource policy from API Gateway REST API
  - Created new API deployment to apply CORS configuration changes
  - All 68+ API methods now have proper CORS OPTIONS handlers
- **Cognito Rate Limiting**: Fixed infinite re-render loop in AuthContext causing `TooManyRequestsException`
  - Stabilized `useEffect` dependencies to prevent continuous token refresh
  - Added proper memoization for auth state management
- **Frontend Array.isArray Checks**: Added defensive checks across 9 frontend files to prevent `.map()` errors on non-array API responses
  - AccountContext.tsx, AccountSelector.tsx, ProtectionGroupsPage.tsx
  - RecoveryPlansPage.tsx, ExecutionsPage.tsx, Dashboard.tsx
  - ServerSelector.tsx, WaveConfigEditor.tsx, api.ts
- **CI/CD Large Template Validation**: Fixed CloudFormation validation for templates exceeding 51,200 bytes
  - Templates now uploaded to S3 before validation
  - Supports api-gateway-stack.yaml (200KB+) validation

### Changed
- **Lambda Directory Structure**: Reorganized Lambda functions into consistent directory structure
  - Each function now in its own directory with `index.py` entry point
  - Updated CloudFormation handlers to use `index.lambda_handler`
  - Removed unused Lambda reference implementations
- **API Gateway Stack**: Added all missing API methods with CORS support
  - 68+ methods across 12 resource categories
  - Complete OPTIONS method coverage for CORS preflight
- **Frontend Build**: Removed FrontendBuildResource custom resource (now handled by CI/CD)

### Technical Details
- **29 commits consolidated** into this release
- **API Gateway ID**: `bev96ut7y8` (aws-elasticdrs-orchestrator-dev)
- **CloudFront Distribution**: `E32V6SWDNQ34DC`
- **Deployment Duration**: ~20 minutes for full CI/CD pipeline

### Migration Notes
- GitHub Actions workflow at `.github/workflows/deploy.yml`
- OIDC stack deployed separately via `cfn/github-oidc-stack.yaml`
- Required GitHub secrets: `AWS_ROLE_ARN`, `DEPLOYMENT_BUCKET`, `STACK_NAME`, `ADMIN_EMAIL`

## [1.2.2] - January 2, 2026

### Enhanced
- **Complete Python Coding Standards Implementation**: Comprehensive code quality improvements across entire codebase
  - **187 PEP 8 Violations Fixed**: Resolved all flake8 violations including line length, whitespace, imports, and naming conventions
  - **Black Formatting Applied**: All 10 Lambda functions formatted with Black using strict 79-character line length
  - **Enhanced Code Readability**: Standardized string quotes, improved variable naming, and consistent formatting
  - **Function Complexity Management**: Added `# noqa: C901` annotations for complex but necessary functions (cross-account logic, conflict detection)
  - **Import Organization**: Cleaned up unused imports and organized import statements following PEP 8 guidelines
  - **Documentation Strings**: Enhanced docstrings and inline comments for better code maintainability
  - **Zero Functional Changes**: All improvements maintain existing functionality and API compatibility
  - **Production Deployment**: Successfully deployed updated Lambda functions to dev environment

### Technical Implementation
- **Lambda Function Updates**: All 5 Lambda functions updated with coding standards improvements
  - `aws-drs-orchestrator-api-handler-dev`: Updated January 2, 2026 at 17:17:02 UTC
  - **Black Formatting**: Applied strict 79-character line length formatting to all Lambda files
  - **Syntax Error Fix**: Resolved missing indentation in `lambda/poller/execution_finder.py` line 232
  - Enhanced error handling and logging consistency
  - Improved code structure and maintainability
- **Deployment Verification**: Confirmed API Gateway responding correctly and CloudWatch logs showing proper execution
- **Test Environment Configuration**: Created `.env.deployment.test` for safe future deployments
- **S3 Deployment Sync**: All updated code artifacts synced to deployment bucket

### Code Quality Metrics
- **Baseline Violations**: Reduced from 187 to 0 PEP 8 violations
- **Black Formatting**: All 10 Lambda files now comply with 79-character line length
- **Files Improved**: 15+ Python files across lambda/, scripts/, and tests/ directories
- **Maintainability**: Enhanced code readability and consistency for future development
- **Standards Compliance**: Full adherence to Python PEP 8 coding standards with strict line length enforcement

### Deployment
- **Safe Deployment Method**: Used `--update-lambda-code` flag for code-only updates without CloudFormation changes
- **Zero Downtime**: Lambda function updates applied without service interruption
- **Verification Complete**: API endpoints responding correctly with enhanced code quality
- **Rollback Ready**: Previous version preserved in git history for emergency rollback if needed

## [1.2.1] - January 1, 2026

### Security
- **Enhanced EventBridge Security Validation**: Multi-layer security validation for automated tag synchronization
  - **Source IP Validation**: Verify EventBridge requests originate from legitimate sources
  - **Request Structure Validation**: Prevent direct Lambda invocation attempts
  - **Authentication Header Validation**: Reject requests with unexpected Authorization headers
  - **EventBridge Rule Name Validation**: Verify rule names match expected patterns
  - **Comprehensive Security Audit Logging**: Complete audit trail for all EventBridge requests
  - **Zero Trust Model**: EventBridge authentication bypass validated through multiple security layers

### Fixed
- **EventBridge Authentication Bypass**: Resolved 401 Unauthorized errors for scheduled tag synchronization
  - Moved EventBridge detection before authentication checks in Lambda handler
  - Scoped authentication bypass to only `/drs/tag-sync` endpoint
  - Maintained security through comprehensive validation layers
  - Enabled automated hourly tag synchronization without manual intervention

### Enhanced
- **Security Monitoring**: Enhanced CloudWatch logging for EventBridge security events
- **Attack Prevention**: Multiple validation layers prevent authentication bypass abuse
- **Compliance**: Complete audit trail for security reviews and monitoring
- **Operational Reliability**: Automated tag sync now works consistently without manual intervention

## [1.2.0] - January 1, 2026

### Added
- **Scheduled Tag Synchronization**: Automated tag sync from EC2 instances to DRS source servers
  - EventBridge-triggered synchronization with configurable schedules (15min to 24hr intervals)
  - Manual trigger capability for immediate synchronization
  - Comprehensive error handling and progress tracking
  - Batch processing with 10-server chunks to avoid API limits
  - Supports all 28 commercial AWS DRS regions
  - New Settings modal with TagSyncConfigPanel for schedule configuration
  - Real-time sync progress indicators and status updates

### Fixed
- **EventBridge Schedule Expression Validation**: Fixed "Parameter ScheduleExpression is not valid" error
  - Corrected singular/plural form handling for rate expressions
  - `rate(1 hour)` vs `rate(2 hours)` now properly validated
  - Prevents validation failures when selecting "1 hour" interval

### Enhanced
- **API Endpoints**: Added PUT `/settings/tag-sync-schedule` and POST `/tag-sync/trigger`
- **Infrastructure**: Enhanced EventBridge integration with automated scheduling
- **Lambda Permissions**: Added comprehensive EC2 tag operation permissions
- **Frontend**: New TagSyncConfigPanel component with intuitive schedule selection
- **Error Handling**: Robust error recovery and partial failure handling for tag operations

### Technical Implementation
- Tag sync processes handle pagination for large EC2 instance sets
- EventBridge source detection differentiates automated vs manual triggers
- Protection Groups using tag-based server selection now properly resolve servers
- Addresses core issue where empty DRS server tags prevented server resolution

## [1.1.1] - December 31, 2025

### Fixed
- **Security Vulnerabilities**: Comprehensive fixes for multiple CWE vulnerabilities
  - **SQL Injection (CWE-89)**: Fixed DynamoDB operations with proper ConditionExpression usage
  - **XSS Vulnerabilities (CWE-20,79,80)**: Sanitized user inputs in React components
  - **OS Command Injection (CWE-78,77,88)**: Added regex sanitization across multiple files
  - **Log Injection (CWE-117)**: Removed newline characters from user-controlled logging data
- **TypeScript Syntax Error**: Fixed extra closing brace in RecoveryPlansPage.tsx JSX map function
- **Error Handling**: Improved structured error responses and validation across Lambda functions
- **Input Validation**: Enhanced UUID format checking and type conversion for user-controlled data

### Security
- **Database Security**: Added condition expressions to DynamoDB operations to prevent injection attacks
- **Frontend Security**: Comprehensive input sanitization to prevent XSS and command injection
- **Performance Optimizations**: Fixed memory leaks and implemented proper singleton patterns
- **Code Quality**: Addressed readability issues and improved maintainability

### Deployment
- **Production Security Fixes**: All vulnerability fixes deployed to production environment
- **Frontend Rebuild**: Complete frontend rebuild and deployment with security enhancements
- **Lambda Updates**: All Lambda functions updated with security improvements
- **CloudFront Cache**: Invalidated to ensure latest secure frontend is served

## [1.1.0] - December 31, 2025

### Added
- **Comprehensive RBAC System**: Implemented role-based access control with 5 DRS-specific roles
  - `DRSOrchestrationAdmin`: Full administrative access including configuration management
  - `DRSRecoveryManager`: Recovery operations and configuration management
  - `DRSPlanManager`: Plan management without configuration access
  - `DRSOperator`: Execute operations only
  - `DRSReadOnly`: View-only access for monitoring and compliance
- **14 Granular Permissions**: Fine-grained permissions covering all business functionality
- **Backend API Endpoint**: `/user/permissions` endpoint for role and permission retrieval
- **JWT Token Integration**: Proper Amplify v6 compatibility with `fetchAuthSession()` API
- **Conditional UI Components**: Export/Import tabs only visible to authorized users
- **RBAC Middleware**: Server-side permission validation for all API endpoints
- **Permission-Aware Components**: React components that adapt based on user permissions

### Changed
- **Settings Modal**: Export and Import tabs now conditionally displayed based on user permissions
- **Authentication Flow**: Updated to use Amplify v6 API for JWT token extraction
- **API Gateway**: Enhanced CORS configuration for `/user/permissions` endpoint
- **Frontend Architecture**: Added PermissionsContext for centralized permission management

### Fixed
- **JWT Token Extraction**: Fixed frontend compatibility with Amplify v6 authentication
- **CORS Issues**: Resolved OPTIONS method handling for user permissions endpoint
- **Permission Validation**: Server-side validation ensures UI permissions match backend authorization

### Security
- **Principle of Least Privilege**: Users only see functionality they're authorized to use
- **Server-Side Validation**: All permissions validated on backend regardless of frontend state
- **Audit Trail**: User roles and permissions logged for compliance tracking

## [RBAC-PROTOTYPE-v1.0] - December 31, 2025

### 🎉 **MILESTONE: RBAC Prototype with Password Reset Capability v1.0** - `TBD`

**Tag**: `RBAC-Prototype-with-Password-Reset-capability-v1.0`

This milestone introduces comprehensive Role-Based Access Control (RBAC) with 6 granular roles and password reset functionality for new users, establishing enterprise-grade security and user management for the AWS DRS Orchestration platform.

### Major Features

**Comprehensive RBAC System with API-First Enforcement**

The solution now implements a complete role-based access control system with 6 distinct roles, each providing granular permissions for disaster recovery operations. RBAC enforcement occurs at the API level, ensuring that all access methods (UI, CLI, SDK, direct API calls) respect the same security boundaries.

**Six RBAC Roles with Granular Permissions:**

1. **DRS-Administrator**
   - **Full Access**: Complete administrative control over all DRS orchestration functions
   - **Permissions**: All protection groups, recovery plans, executions, DRS operations, configuration management, and user management
   - **Use Case**: System administrators and DR team leads requiring unrestricted access

2. **DRS-Infrastructure-Admin** 
   - **Infrastructure Management**: Can manage DRS infrastructure, protection groups, and recovery plans
   - **Permissions**: Create/modify protection groups and recovery plans, execute recovery plans, read executions, manage DRS configuration, export/import settings
   - **Restrictions**: Cannot delete execution history or manage user roles
   - **Use Case**: Infrastructure teams responsible for DR setup and configuration

3. **DRS-Recovery-Plan-Manager**
   - **Recovery Plan Focus**: Can create, modify, and execute recovery plans with full execution control
   - **Permissions**: Read protection groups, full recovery plan management, execute/pause/resume/cancel executions, terminate instances
   - **Restrictions**: Cannot create/modify protection groups or manage system configuration
   - **Use Case**: DR managers responsible for recovery plan design and execution

4. **DRS-Operator**
   - **Execution Focus**: Can execute recovery plans and perform DR operations
   - **Permissions**: Read protection groups and recovery plans, execute/pause/resume/cancel recovery plans, terminate instances
   - **Restrictions**: Cannot create or modify protection groups or recovery plans
   - **Use Case**: Operations teams responsible for executing pre-defined recovery procedures

5. **DRS-Recovery-Plan-Viewer**
   - **Planning Review**: Can view recovery plans but not execute them
   - **Permissions**: Read-only access to protection groups, recovery plans, and execution history
   - **Restrictions**: Cannot execute recovery plans or perform any DR operations
   - **Use Case**: Stakeholders who need visibility into DR plans for compliance or planning

6. **DRS-Read-Only**
   - **View-Only Access**: Complete read-only access to DRS configuration and status
   - **Permissions**: View all protection groups, recovery plans, executions, DRS status, and quotas
   - **Restrictions**: Cannot perform any write operations or execute recovery plans
   - **Use Case**: Auditors, compliance officers, and stakeholders requiring visibility without operational access

**API-First Security Enforcement**

- **Unified Security Model**: All access methods (UI, CLI, SDK, API) enforce identical role-based permissions
- **No Bypass Possible**: UI restrictions reflect actual API-level RBAC enforcement - users cannot circumvent UI limitations
- **Cognito Integration**: Roles managed through AWS Cognito Groups with JWT token validation
- **Granular Endpoint Protection**: 40+ API endpoints mapped to specific permissions with automatic enforcement
- **Real-Time Validation**: Every API call validates user permissions before execution

**Password Reset Functionality for New Users**

- **Forced Password Change**: New users must change their temporary password on first login
- **Secure Workflow**: Cognito-managed password reset with email verification
- **Admin User Creation**: Administrators can create users with temporary passwords
- **Self-Service Reset**: Users can initiate password reset through standard Cognito flows
- **Password Policy Enforcement**: Configurable password complexity requirements

**Automatic Account Initialization**

- **Seamless First-Time Setup**: Solution automatically detects when no target accounts exist and initializes the current account (where solution is deployed) as the first default account
- **Zero-Configuration Start**: Eliminates complex wizard setup - users can immediately begin creating protection groups and recovery plans
- **Smart Account Detection**: Uses `ensure_default_account()` function that triggers during first API call to any core functionality
- **Default Account Assignment**: First account added automatically becomes the default account for streamlined user experience
- **Cross-Account Ready**: Foundation supports adding additional cross-account configurations after initial setup

### Technical Implementation

**Automatic Account Initialization System**

- **Smart Detection**: `ensure_default_account()` function automatically detects when no target accounts exist
- **Seamless Integration**: Triggers during first API call to protection groups, recovery plans, or DRS operations
- **Current Account Setup**: Automatically adds the account where solution is deployed as first default account
- **Zero-Configuration**: Eliminates complex setup wizards - users can immediately start using the platform
- **Cross-Account Foundation**: Provides foundation for adding additional cross-account configurations later

**RBAC Middleware System**

- **Centralized Authorization**: `rbac_middleware.py` provides comprehensive role and permission management
- **Permission Matrix**: 25+ granular permissions mapped to 6 roles with clear capability definitions
- **Decorator Pattern**: Function decorators for easy permission enforcement (`@require_permission`, `@require_role`)
- **Dynamic Validation**: Runtime permission checking with detailed error messages
- **User Context**: Complete user profile extraction from Cognito JWT tokens

**API Security Integration**

- **Endpoint Mapping**: All 40+ API endpoints mapped to required permissions in `ENDPOINT_PERMISSIONS`
- **Automatic Enforcement**: Middleware automatically validates permissions for each request
- **Error Handling**: Standardized 403 Forbidden responses with specific permission requirements
- **User Information**: User context automatically injected into Lambda functions for audit trails

**Frontend Role Awareness**

- **Dynamic UI**: Interface elements show/hide based on user permissions
- **Role-Based Navigation**: Menu items and actions filtered by user capabilities
- **Permission Feedback**: Clear indication when actions are restricted due to insufficient permissions
- **Consistent Experience**: UI restrictions match API-level enforcement exactly

### Security Enhancements

**Enterprise-Grade Access Control**

- **Principle of Least Privilege**: Each role provides minimum necessary permissions for job function
- **Separation of Duties**: Clear separation between infrastructure management, plan management, and execution
- **Audit Trail**: All actions logged with user context and role information
- **Token Security**: JWT token validation with automatic expiration and refresh

**Compliance Ready**

- **Role Documentation**: Complete role definitions with permission matrices for compliance audits
- **Access Reviews**: Clear role assignments enable regular access reviews
- **Audit Logging**: All user actions logged with role context for compliance reporting
- **Permission Transparency**: Users can view their own roles and permissions through API

### User Experience Improvements

**Intuitive Role Management**

- **Clear Role Names**: Self-explanatory role names that match organizational functions
- **Permission Visibility**: Users can see their current roles and capabilities
- **Helpful Error Messages**: When access is denied, users receive clear explanation of required permissions
- **Guided Onboarding**: New users guided through password reset and role understanding

**Seamless Integration**

- **No Workflow Disruption**: RBAC implementation maintains existing user workflows
- **Backward Compatibility**: Existing functionality preserved while adding security layers
- **Performance Optimized**: Permission checking adds minimal latency to API calls
- **Scalable Design**: Role system designed to support additional roles and permissions as needed

### Files Modified

**Core RBAC Implementation**
- `lambda/rbac_middleware.py` - Complete RBAC system with 6 roles and 25+ permissions
- `lambda/index.py` - Integration of RBAC middleware into all API endpoints
- `cfn/api-stack-rbac.yaml` - API Gateway configuration with RBAC-enabled endpoints

**Frontend Integration**
- `frontend/src/contexts/AuthContext.tsx` - Role-aware authentication context
- `frontend/src/services/api.ts` - API client with role-based error handling
- Multiple component files - Role-based UI element visibility

**Infrastructure**
- `cfn/api-stack-rbac.yaml` - Complete API Gateway setup with all endpoints and CORS
- `scripts/sync-to-deployment-bucket.sh` - Deployment script with RBAC stack support

### Deployment

The RBAC Prototype is deployed using the RBAC-enabled CloudFormation stack (`cfn/api-stack-rbac.yaml`) which includes all API endpoints with proper CORS configuration and Cognito integration.

**Deployment Command:**
```bash
./scripts/sync-to-deployment-bucket.sh --deploy-cfn
```

### Testing Completed

- ✅ All 6 roles tested with appropriate permission enforcement
- ✅ API-first security validated - UI restrictions match API enforcement
- ✅ Password reset functionality verified for new users
- ✅ Cross-role permission validation completed
- ✅ Frontend role-based UI elements tested
- ✅ CORS configuration validated for all endpoints

### Breaking Changes

None - RBAC implementation is additive and maintains backward compatibility with existing functionality.

## [MVP-DRILL-PROTOTYPE] - December 30, 2025

### 🎉 **MILESTONE: MVP Drill Prototype Complete** - `a34c5b7`

**Tag**: `MVP-DRILL-PROTOTYPE`

This milestone represents the completion of the MVP Drill Prototype for the AWS DRS Orchestration Solution, providing a comprehensive disaster recovery orchestration platform with complete multi-account support, enhanced tag-based server selection, and production-ready drill capabilities.

### Documentation Standards

**CHANGELOG.md Best Practices Implementation** - `a34c5b7`

- Updated CHANGELOG.md to follow "Keep a Changelog" standard format
- Added reference to Keep a Changelog format (https://keepachangelog.com/en/1.0.0/)
- Added Semantic Versioning adherence statement
- Maintains existing comprehensive structure and detailed commit tracking
- Follows GitLab community standards for changelog documentation
- Establishes foundation for proper milestone documentation standards

**Documentation Updates** - `88a9df6`

- Updated README.md with MVP-DRILL-PROTOTYPE tag references
- Updated release badge to show "MVP Drill Prototype Complete" (green)
- Added comprehensive milestone description to CHANGELOG.md
- Updated Repository Snapshots table with new tag entry
- Synchronized documentation across README and CHANGELOG for consistency

### Major Capabilities Delivered

**Complete Disaster Recovery Orchestration Platform**

- **Protection Groups**: Organize DRS source servers with explicit and tag-based selection
- **Recovery Plans**: Multi-wave execution with dependency management and pause/resume
- **Execution Engine**: Step Functions orchestration with real-time monitoring
- **DRS Integration**: Complete AWS Elastic Disaster Recovery service integration
- **Instance Management**: Terminate recovery instances after drill completion
- **Multi-Account Support**: Cross-account orchestration and management

**Architecture & Scale**

- **5 Lambda Functions** (Python 3.12)
- **7 CloudFormation Templates** (nested stack architecture)
- **3 DynamoDB Tables** with encryption
- **React 19.1.1 + CloudScape Design System** frontend
- **API Gateway** with Cognito authentication
- **Step Functions** with waitForTaskToken pattern
- **Supports all 30 AWS DRS regions** (28 commercial + 2 GovCloud)
- **Handles up to 300 replicating servers** per account
- **Serverless architecture** with pay-per-use cost model

**Technical Capabilities**

- Wave-based recovery execution with explicit dependencies
- Pause/resume functionality between waves for validation
- Real-time DRS job monitoring and status tracking
- Comprehensive execution history and audit trails
- DRS service limits validation and quota monitoring
- Tag-based server discovery across all DRS regions
- Configuration export/import for backup and restore
- Cross-account IAM role assumption for enterprise scale

**Security & Compliance**

- Cognito JWT authentication with 45-minute sessions
- IAM least-privilege policies with comprehensive DRS permissions
- Encryption at rest (DynamoDB) and in transit (HTTPS)
- Cross-account IAM role assumption for multi-account support
- Comprehensive audit trails in execution history

**Production Ready**

- GitLab CI/CD pipeline with automated testing
- S3-based deployment with CloudFormation IaC
- Production-ready with comprehensive error handling
- Monitoring and observability with CloudWatch integration
- Complete API documentation with examples
- Comprehensive deployment and operations guides

### Fixed

**CHANGELOG.md Content Restoration** - December 30, 2025 - `8b1eaf5`

- **Complete History Restored**: Restored full CHANGELOG.md from commit 19d6e80 (1,172 lines)
- **Fixed Truncation Issue**: Resolved truncation from commit 2a4a3cd that accidentally removed 1,048 lines
- **Preserved Project History**: Maintained complete project history from November 8, 2025 to present
- **Historical Context**: All milestones, features, and changes now accessible for reference

**Technical Details:**
- Changelog reorganization accidentally truncated most content during date-based restructuring
- Restored from previous commit that contained complete project history
- Ensures continuity of project documentation and historical reference

### Enhanced

**Repository Cleanup and Organization** - December 30, 2025 - `57a09c6`

- **Development Artifacts Cleanup**: Removed build artifacts, test reports, and temporary files
- **Smart Reference Checking**: Added `safe-cleanup.sh` script with documentation reference validation
- **Preserved Essential Files**: Kept all source code, essential scripts, and AI assistant memory
- **Documentation Integrity**: Preserved `FUTURE_ENHANCEMENTS_CONSOLIDATION_PLAN.md` (referenced in docs-index.md)
- **S3 Sync Integration**: Cleaned deployment bucket to match organized repository state

**Files Removed:**
- Build artifacts: Lambda packages (*.zip), Python cache (__pycache__), node_modules
- Test artifacts: playwright reports, coverage files, test results
- Non-essential scripts: monitoring utilities, testing scripts, debug files
- Archive directories: root-level archive/, temp/, docs/archive/
- Unreferenced documentation: DRS_MODULAR_ORCHESTRATION_DESIGN.md, GAP_ANALYSIS.md, ARCHIVE_ANALYSIS.md
- IDE files: .vscode/settings.json, .DS_Store files

**Files Added:**
- `scripts/safe-cleanup.sh`: Intelligent cleanup script with reference checking and safety features

**Repository Benefits:**
- Significant disk space freed up locally and in S3 deployment bucket
- Cleaner development environment with only essential files
- Maintained complete project functionality and documentation integrity
- All removed files safely backed up in GitLab commit history

**History Page Date Filtering System** - December 30, 2025

- **Intuitive Date Range Filtering**: Added comprehensive date filtering for execution history with American date format (MM-DD-YYYY)
- **Quick Filter Buttons**: ButtonDropdown with preset ranges (Last Hour, Last 6 Hours, Today, Last 3 Days, Last Week, Last Month)
- **Custom Date Range**: Separate DateInput fields for flexible start and end date selection
- **Visual Feedback**: Clear indication of active date range with easy "Clear Filter" button
- **Proper Date Handling**: Robust Unix timestamp conversion and date parsing with `date-fns` library
- **Search Bar Enhancement**: Widened search bar for better readability and updated placeholder text
- **UI Simplification**: Removed redundant filter dropdowns to reduce interface clutter
- **American Format**: MM-DD-YYYY date format throughout for American audience preference

**Technical Implementation:**
- Uses `date-fns` functions: `parse()`, `format()`, `isWithinInterval()`, `startOfDay()`, `endOfDay()`
- Handles Unix timestamp conversion (seconds to milliseconds) for JavaScript Date objects
- Filters apply only to History tab (completed executions) with proper status filtering
- Maintains existing search functionality alongside new date filtering
- Clean code with unused imports removed (`DateRangePickerProps`, `parseISO`)

**Files Modified:**
- `frontend/src/pages/ExecutionsPage.tsx` - Complete date filtering system implementation

### Fixed

**History Page Execution Deletion and Console Logging Cleanup** - December 30, 2025

- **Enhanced Selective Deletion**: Fixed History page Clear History button to support multi-selection with granular deletion
- **Improved User Experience**: Button now shows selected count ("Clear History (3)") and is disabled when no items selected
- **API Enhancement**: Added `DELETE /executions` endpoint with body support for selective deletion by execution IDs
- **Data Consistency Fix**: Resolved issue where executions appeared in UI but couldn't be found in database during deletion
- **Authentication Fix**: Resolved JWT token authentication issues with selective deletion endpoint
- **Console Cleanup**: Removed excessive debugging logs from authentication and API request interceptors
- **MVP Drill Only Prototype**: Core drill functionality with comprehensive documentation

**Technical Details:**
- Enhanced `delete_executions_by_ids()` Lambda function to handle array of execution IDs
- Fixed DynamoDB composite key handling for ExecutionHistoryTable (`ExecutionId` + `PlanId`)
- Updated frontend table with `selectionType="multi"` for checkbox selection
- Improved confirmation dialog to show selected execution count
- Removed verbose JWT token validation and API debugging logs from production build

**Files Modified:**
- `frontend/src/pages/ExecutionsPage.tsx` - Multi-selection table and improved Clear History button
- `frontend/src/services/api.ts` - Cleaned authentication debugging logs and enhanced deleteExecutions method
- `frontend/src/contexts/AuthContext.tsx` - Removed auth session debugging logs
- `lambda/index.py` - Enhanced selective deletion with proper error handling
- `cfn/api-stack.yaml` - Added DELETE /executions endpoint with CORS support

**History Page Search Enhancement** - December 30, 2025

- **Improved Search Placeholder**: Changed vague "Find executions" to descriptive "Search by plan name, execution ID, or status"
- **Better User Guidance**: Users now understand exactly what fields are searchable
- **Enhanced Discoverability**: Clear indication of search capabilities reduces user confusion

**History Page Filter Fixes** - December 30, 2025

- **Invocation Source Filter**: Fixed dropdown filter that wasn't working due to undefined value handling
- **Selection Mode Filter**: Fixed similar issue with undefined selectionMode values
- **Robust Filtering**: Added proper default value handling for optional fields in ExecutionListItem
- **Consistent Behavior**: All dropdown filters now work reliably across different execution types

**DRS Execution Wave Status Reporting Bug Fix** - December 30, 2025

- **Critical Bug Fixed**: Wave 3 was incorrectly marked as "Successfully completed" when DRS recovery actually failed
- **Root Cause**: Polling logic fell back to DRS job status ('COMPLETED') even when servers never reached 'LAUNCHED' status
- **Solution**: Added explicit detection for scenario where DRS job completes but instances fail to launch
- **Status Accuracy**: Modified `poll_wave_status()` to mark wave as 'FAILED' when `drs_status == 'COMPLETED'` but `not all_launched`
- **User Clarity**: Execution history now accurately reflects actual recovery outcomes

**Files Modified:**
- `lambda/poller/execution_poller.py` - Enhanced wave status detection logic

### Removed

**Frontend Debug Logging Cleanup** - December 29, 2025

- Removed all debugging console.log statements from frontend application
- Cleaned up development-time logging that was appearing in browser console
- Removed Amplify configuration logging, button visibility debug messages, and API request debugging
- Preserved legitimate error logging and production error handling
- Improved production performance by eliminating unnecessary console output

**Files cleaned:**
- `frontend/src/contexts/AuthContext.tsx` - Removed auth flow debugging
- `frontend/src/services/api.ts` - Removed API request/response debugging  
- `frontend/src/aws-config.ts` - Removed configuration loading messages
- `frontend/vite-plugin-inject-config.ts` - Removed build-time logging

### Fixed

**CRITICAL: Cross-Account Terminate Instances Support** - December 29, 2025

- Fixed terminate instances functionality to work with cross-account executions
- Terminate function now uses the same account context as the original execution
- Calls `determine_target_account_context()` to get proper account/role information from Recovery Plan
- Uses `create_drs_client()` with cross-account credentials instead of current account only
- Prevents silent failures when trying to terminate instances in different AWS accounts
- Maintains backward compatibility for single-account deployments

**Technical Details:**
- Updated `terminate_recovery_instances()` function to retrieve Recovery Plan and determine account context
- Integrated existing cross-account infrastructure (`determine_target_account_context`, `create_drs_client`)
- Creates DRS clients with proper assumed role credentials for target accounts
- Ensures terminate works consistently with the execution logic that created the instances

**CRITICAL: InstancesTerminated Flag Timing Issue** - December 29, 2025

- Fixed critical bug where `InstancesTerminated` flag was set when termination was **initiated**, not **completed**
- Lambda function now only sets `InstancesTerminated=True` when DRS termination jobs are actually **completed**
- Added monitoring logic in `get_termination_job_status` to detect job completion and update flag correctly
- Removed frontend workaround logic that was calling API to check instance existence
- Fixed terminate button showing after instances were already terminated
- Simplified frontend terminate button logic to rely on backend `InstancesTerminated` flag
- Enhanced Lambda logging for termination job monitoring and completion detection

**Technical Details:**
- Modified `terminate_recovery_instances` function to store job info without setting completion flag
- Enhanced `get_termination_job_status` function to update `InstancesTerminated=True` when all jobs complete
- Removed `instancesExistCheck` workaround from frontend ExecutionDetailsPage
- Fixed DynamoDB query to use composite key (ExecutionId + PlanId) correctly

**Terminate-Instances Button Visibility Logic** - December 29, 2025

- Fixed terminate button showing for executions with active/in-progress waves
- Button now only appears when waves have actually completed launch and have recovery instances
- Prevents showing terminate button for executions where Wave 1 is still converting/launching
- Improved user experience by hiding inappropriate actions

**Terminate-Instances API Error Handling** - December 29, 2025

- Changed terminate-instances API response from 400 Bad Request to 200 OK when no recovery instances exist
- Provides better user experience for executions cancelled before any instances were launched
- Returns structured response with clear messaging: "No recovery instances to terminate"
- Maintains API consistency and prevents confusing error messages in browser console

**ExecutionDetailsPage Cancellation Status Handling** - December 29, 2025

- Added 'cancelling' status to polling list to keep UI updates active during cancellation
- Updated canCancel logic to prevent duplicate cancel requests while cancellation is in progress
- Added executionStatus and executionEndTime props to WaveProgress component for proper status display

**Terminate-Instances Progress Bar Fix** - December 29, 2025

- Fixed termination progress bar staying at 0% throughout the process
- Enhanced Lambda backend logic to handle DRS clearing `participatingServers` array on job completion
- Added fallback progress calculation using job status when server list is empty
- Progress now starts at 10% and properly tracks to 100% completion
- Improved user experience with accurate visual feedback during instance termination

**Terminate-Instances Button Logic Enhancement** - December 29, 2025

- Fixed button showing inappropriately when instances already terminated
- Added comprehensive validation to ensure recovery instances actually exist before showing button
- Enhanced detection of completed jobs with launched instances by checking job events
- Fixed edge case where Wave 1 shows `status=started` but job actually completed with launched instances
- Added special handling for cancelled executions with job IDs
- Improved console logging for debugging button visibility logic

### Code Cleanup

**ExecutionDetailsPage Debug Cleanup** - December 29, 2025

- Removed debug console.log statements from terminate button visibility logic
- Cleaned up termination status polling console output
- Simplified debugging code for production deployment

**DRS Termination Job Progress Tracking** - December 21, 2025

- Fixed termination status tracking when `participatingServers` array is empty
- Now checks job `status` field directly - if all jobs show `COMPLETED`, progress is set to 100%
- Removed check for non-existent `TERMINATE_COMPLETED` launchStatus value

### Enhanced

**Dashboard Auto-Detect Busiest DRS Region** - `718a26c` - December 20, 2025

- Dashboard DRS Capacity panel now automatically detects and displays the region with the most replicating servers
- Checks 8 common regions in parallel on initial load (us-east-1, us-east-2, us-west-2, eu-west-1, eu-central-1, ap-northeast-1, ap-southeast-1, ap-southeast-2)
- Selects the busiest region as the default view instead of always defaulting to us-east-1
- Resets detection when account changes to ensure accurate region selection per account

**Complete EC2 Instance Type Support Enhancement** - `5b0e6db` - December 17, 2025

- **Complete Instance Type Coverage**: Enhanced EC2 Launch Configuration to display ALL 968+ EC2 instance types available in each region
- **Modern Instance Families**: Full access to m6a, m7i, c7g, r7i, and all current-generation instance types
- **Regional Accuracy**: Instance types dynamically loaded per selected AWS region
- **Browser Cache Resolution**: Resolved caching issues that previously limited selection to subset of common instances
- **User Experience**: Users can now select optimal instance types for their specific disaster recovery workloads
- **AWS Console Parity**: Consistent with AWS DRS Console instance type selection experience
- **Future-Proof**: Automatically includes new instance types as AWS releases them

**Complete EC2 Instance Type Support for DRS Launch Settings** - `3c46624` - December 17, 2025

- Enhanced `get_ec2_instance_types` function to return ALL available EC2 instance types in each region (968+ types)
- Removed filtering that limited selection to only "common" instance families
- Added support for all modern instance families including m6a, m7i, c7i, r7i series
- Maintained usability by excluding only bare metal instances (.metal)
- Improved organization with sorting by family and vCPU count
- Resolved browser caching issue that was preventing updated API responses
- Users now have complete flexibility in selecting instance types for DRS launch configurations
- Future-proof: automatically includes new instance types as AWS releases them

### Documentation

**UX/UI Design Specifications Multi-Account Prototype 1.0 Complete** - `e03bb44` - December 17, 2025

- Added Multi-Account component specifications (AccountSelector, AccountRequiredWrapper, AccountManagementPanel)
- Added Multi-Account user flows (setup, auto-selection, enforcement, switching, preferences)
- Updated page specifications with account enforcement behavior for Dashboard, Protection Groups, Recovery Plans, and Executions pages
- Enhanced top navigation specification to include AccountSelector integration
- Updated component library count from 33 to 36 components
- Documented complete Multi-Account system behavior and visual requirements
- Completes requirements documentation updates for Multi-Account Prototype 1.0 milestone

**README Multi-Account Prototype 1.0 Update** - `f94301b` - December 17, 2025

- Updated Repository Snapshots section with `v1.0.0-multi-account-prototype` tag
- Added Recent Updates entry highlighting Multi-Account Prototype 1.0 release
- Referenced complete v1.7.0 changelog for detailed release information
- Maintained existing documentation structure and formatting consistency

## [1.7.0] - December 17, 2025

### 🎉 **MILESTONE: Multi-Account Prototype 1.0** - `905a682`

**Tag**: `v1.0.0-multi-account-prototype`

This milestone release introduces comprehensive multi-account support and fixes critical tag-based server selection functionality, establishing the foundation for enterprise-scale disaster recovery orchestration.

### Major Features

**Multi-Account Management & Enforcement**

- **Account Context System**: Complete account management with enforcement logic and persistent state
- **Auto-Selection**: Single accounts automatically selected as default for seamless user experience
- **Account Selector**: Top navigation dropdown for intuitive account switching with full page context updates
- **Setup Wizard**: Guided first-time account configuration for new users
- **Default Preferences**: Persistent default account selection integrated into existing 3-tab settings panel
- **Page-Level Enforcement**: Features blocked until target account selected (multi-account scenarios only)
- **Settings Integration**: Default account preference seamlessly integrated without disrupting existing 3-tab structure

**Enhanced Tag-Based Server Selection**

- **DRS Source Server Tags**: Fixed critical issue - now queries actual DRS source server tags (not EC2 instance tags)
- **Complete Hardware Details**: CPU cores, RAM, disks, FQDN, OS info, network interfaces displayed in tag preview
- **Regional Support**: Full support for all 30 DRS-supported regions with us-west-2 testing validation
- **Preview Enhancement**: Tag preview shows identical detailed information as manual server selection
- **Clean UX**: Removed confusing non-functional checkboxes from tag preview for cleaner interface

### Technical Improvements

**Backend (Lambda)**

- **Enhanced API**: `query_drs_servers_by_tags` completely rewritten to use DRS `list_tags_for_resource` API
- **Hardware Discovery**: Added comprehensive server hardware information collection from DRS source properties
- **Field Consistency**: Fixed `sourceServerId` → `sourceServerID` naming alignment across frontend and backend
- **Regional Flexibility**: Support for any DRS-supported region configuration with proper error handling

**Frontend (React + CloudScape)**

- **Account Context**: Centralized account state management with localStorage persistence and auto-selection logic
- **Component Integration**: Account selector integrated into top navigation following AWS Console patterns
- **Settings Enhancement**: Default account preference added to existing AccountManagementPanel (maintains 3-tab structure)
- **Page Wrappers**: AccountRequiredWrapper component for consistent enforcement across all protected pages
- **Type Safety**: Enhanced TypeScript interfaces for server data structures and API responses

**Infrastructure**

- **S3 Deployment**: All artifacts synced to deployment bucket for reproducible deployments
- **CloudFormation Ready**: Master template deployment with all latest enhancements included
- **Build Optimization**: Frontend build with code splitting and performance optimization

### Bug Fixes

- Fixed tag-based server selection querying wrong tag source (EC2 instance tags vs DRS source server tags)
- Fixed missing hardware details in tag preview matching manual selection display
- Fixed field name inconsistency (`sourceServerId` vs `sourceServerID`) in API responses
- Fixed account selection persistence across browser sessions
- Fixed navigation context switching between accounts with proper state management

### UX Improvements

- Clean tag preview interface without confusing non-functional checkboxes
- Intuitive account selector positioned in familiar top navigation location
- Automatic default account selection for single-account scenarios (no user action required)
- Consistent server information display across all selection methods (manual and tag-based)
- Seamless account switching with full page context updates and state preservation

### Files Changed

**Core Components (23 files changed, 1,421 insertions, 515 deletions)**

- `frontend/src/contexts/AccountContext.tsx` - Account management state and enforcement logic
- `frontend/src/components/AccountSelector.tsx` - Navigation account dropdown component
- `frontend/src/components/AccountRequiredWrapper.tsx` - Page-level enforcement wrapper
- `frontend/src/components/AccountManagementPanel.tsx` - Settings integration with default preference
- `lambda/index.py` - Enhanced tag query function and hardware discovery
- `frontend/src/components/ProtectionGroupDialog.tsx` - Tag preview improvements
- `frontend/src/components/ServerListItem.tsx` - Checkbox visibility control
- `frontend/src/services/api.ts` - API type definitions and service methods
- `frontend/src/types/index.ts` - Enhanced server interfaces and type definitions

**Page Integration**

- `frontend/src/pages/Dashboard.tsx` - Account enforcement integration
- `frontend/src/pages/ProtectionGroupsPage.tsx` - Account enforcement integration
- `frontend/src/pages/RecoveryPlansPage.tsx` - Account enforcement integration
- `frontend/src/pages/ExecutionsPage.tsx` - Account enforcement integration
- `frontend/src/components/cloudscape/AppLayout.tsx` - Navigation integration

### Deployment

All components synced to S3 deployment bucket and ready for production deployment using the master CloudFormation template at: `s3://aws-drs-orchestration/cfn/master-template.yaml`

### Testing

- Verified tag-based selection with us-west-2 DRS servers (6 servers with various tags)
- Confirmed hardware details match manual selection display exactly
- Tested account switching and enforcement across all protected pages
- Validated single-account auto-selection behavior
- Confirmed S3 deployment artifact integrity and completeness

### Breaking Changes

None - All changes are backward compatible and enhance existing functionality without disrupting current workflows.

### Fixed

**Dashboard Multi-Account Support Fixes** - December 16, 2025

- Fixed DRS accounts API endpoint routing issue in Lambda function
- Added enhanced debug logging for DRS accounts endpoint
- Fixed `getDRSAccounts()` in drsQuotaService to call correct API endpoint (`/drs/accounts` instead of `/accounts/targets`)
- Moved AccountSelector to top right corner of Dashboard page header
- Restored RegionSelector to DRS Capacity section with backward compatibility
- Updated Dashboard to use region-based DRS quota fetching
- Fixed "Unable to fetch target accounts" error on dashboard
- Fixed DRS capacity showing correct replicating server count for selected region

## [1.6.2] - December 15, 2025

**DRS Tag Synchronization Feature** - `8f8f26e`

Complete implementation of DRS tag synchronization across all 28 commercial AWS regions:

Backend Implementation:

- Added `lambda/drs_tag_sync.py` (165 lines) - Complete tag synchronization Lambda function
- Cross-region DRS source server discovery and EC2 instance tag synchronization
- Smart tag filtering: excludes AWS-managed tags (aws:*, AWS:*) and common system tags
- Comprehensive error handling with detailed failure reporting per server
- Support for all 28 commercial DRS regions with automatic region validation
- Batch processing with progress tracking and detailed sync results
- Added `/drs/tag-sync` API endpoint in API Gateway with CORS support
- Integrated tag sync handler in main Lambda function (`lambda/index.py`)

API Features:

- `POST /drs/tag-sync` endpoint with region parameter support
- Returns detailed sync results: success count, failure count, error details per server
- Validates region parameter and returns appropriate error codes
- Comprehensive error handling for DRS and EC2 API failures

Technical Implementation:

- Uses DRS `describe_source_servers` to discover all source servers in region
- Extracts EC2 instance ID from `sourceProperties.identificationHints.awsInstanceID`
- Queries EC2 `describe_instances` to get current instance tags
- Applies filtered tags to DRS source server using `tag_resource`
- Handles pagination for large server inventories
- Implements retry logic for transient API failures

**Enhanced Hardware Display in Protection Groups** - `8f8f26e`

Comprehensive hardware information display in server discovery panel:

Frontend Enhancements:

- Updated `ServerListItem.tsx` with clean hardware display layout
- Format: "FQDN | CPU: X cores | RAM: X GiB | IP: X.X.X.X"
- FQDN column expanded to 2x width, no label prefix for cleaner appearance
- Hardware info extracted from DRS source server properties
- Responsive layout with proper column sizing

Backend Implementation:

- Enhanced hardware extraction in `lambda/index.py` (lines 4380-4550)
- Extracts CPU cores from `sourceProperties.cpus[0].cores`
- Calculates RAM in GiB from `sourceProperties.ramBytes` with proper conversion
- Calculates total disk space in GiB from `sourceProperties.disks` array
- Handles missing or malformed hardware data gracefully
- Returns hardware info in server discovery API responses

**Deployment Infrastructure Fixes** - `8f8f26e`

Critical deployment script corrections for proper stack targeting:

Script Updates:

- Fixed `scripts/sync-to-deployment-bucket.sh` to target correct CloudFormation stack `drs-orch-v4`
- Updated Lambda function name patterns to match actual deployment: `drsorchv4-*-test`
- Corrected frontend bucket name: `drsorchv4-fe-***REMOVED***-test`
- Fixed CloudFront distribution ID: `***REMOVED***`
- Added proper stack configuration validation

Documentation Updates:

- Updated `README.md` deployment workflow section with correct stack names
- Added stack configuration details and deployment verification commands
- Added "Recent Updates" section documenting deployment fixes
- Clarified S3 deployment bucket as source of truth for all deployments

Deployment Verification:

- Successfully deployed hardware display enhancements to production
- Verified CloudFront distribution serves updated frontend: `https://***REMOVED***.cloudfront.net/protection-groups`
- Confirmed Lambda functions updated with latest code
- All deployment artifacts synced to S3 deployment bucket

**Git Repository Management** - `8f8f26e`

Comprehensive commit and tagging for feature release:

Commit Details:

- 12 files changed: 688 insertions, 258 deletions
- Comprehensive 100+ line commit message documenting all changes
- Detailed technical implementation notes and file-by-file changes
- Cross-references to related documentation and deployment procedures

Tag Creation:

- Created annotated tag: `tag-sync-prototype-28-regions`
- Detailed tag description with feature summary and technical highlights
- References commit hash `8f8f26e` for easy lookup
- Prepared for future release and deployment tracking

Files Modified:

- `lambda/index.py` - Hardware extraction and tag sync integration
- `lambda/drs_tag_sync.py` - Complete tag synchronization implementation
- `frontend/src/components/ServerListItem.tsx` - Hardware display UI
- `scripts/sync-to-deployment-bucket.sh` - Deployment script fixes
- `README.md` - Documentation updates and deployment procedures
- `cfn/api-stack.yaml` - API Gateway tag sync endpoint
- Multiple supporting files for complete feature implementation

## [1.6.1] - December 14, 2025

**Execution History Plan Name Preservation**

- Store `PlanName` directly in execution record at creation time
- Execution history now displays plan name even if the Recovery Plan is later deleted
- Updated enrichment logic to use stored `PlanName` first, fallback to lookup for legacy records
- Shows "Deleted Plan" for legacy executions where the plan no longer exists
- Backfilled existing execution records with historical plan names

## [1.6.0] - December 13, 2025

**Configuration Export/Import Feature** - `9a34e74`, `eb3ba49`, `c888b56`, `be7b4e0`, `9acab27`, `e3e7469`, `03db924`

Complete backup and restore capability for Protection Groups and Recovery Plans:

Backend (Lambda):

- Added `GET /config/export` endpoint - exports all Protection Groups and Recovery Plans to JSON
- Added `POST /config/import` endpoint - imports configuration with validation and dry-run support
- Export includes metadata (schemaVersion, exportedAt, sourceRegion)
- Import is completely non-destructive and additive-only (skips existing resources by name)
- Server validation for explicit-server Protection Groups (verifies servers exist in DRS)
- Tag validation for tag-based Protection Groups (verifies tags resolve to servers)
- Cascade failure handling for Recovery Plans when referenced Protection Groups fail
- Detailed error reporting with specific failure reasons per resource
- **LaunchConfig preservation**: Export includes all LaunchConfig settings (subnet, security groups, instance type, DRS settings)
- **LaunchConfig application on import**: Automatically applies LaunchConfig to DRS source servers when importing Protection Groups
- **Cross-environment portability**: Export uses `ProtectionGroupName` instead of `ProtectionGroupId` in Recovery Plan waves
- **Name resolution on import**: Resolves `ProtectionGroupName` to `ProtectionGroupId` during import
- Changed WaveId from 0-based to 1-based indexing (wave-1, wave-2, wave-3)
- Orphaned PG references in waves are gracefully handled (removed from export if PG doesn't exist)

Frontend:

- Added Settings modal accessible via gear icon in top navigation
- Export tab: One-click download of configuration as JSON file
- Import tab: File picker with preview, dry-run validation, and detailed results
- ImportResultsDialog shows created/skipped/failed counts with expandable details
- Created ApiContext for centralized API state management

Infrastructure (CloudFormation):

- Added `/config/export` and `/config/import` API Gateway resources
- Added CORS OPTIONS methods for both endpoints
- Updated API deployment dependencies

Documentation:

- Added `docs/implementation/CONFIG_EXPORT_IMPORT_SPEC.md` with full specification
- Added minimum import example to ORCHESTRATION_INTEGRATION_GUIDE.md
- Documented required vs optional fields for import JSON
- Added `ServerSelectionTags` explanation for tag-based server discovery
- Updated README Future Enhancements table (item #5 complete)

Files Added:

- `frontend/src/components/SettingsModal.tsx`
- `frontend/src/components/ConfigExportPanel.tsx`
- `frontend/src/components/ConfigImportPanel.tsx`
- `frontend/src/components/ImportResultsDialog.tsx`
- `frontend/src/contexts/ApiContext.tsx`
- `docs/implementation/CONFIG_EXPORT_IMPORT_SPEC.md`

**Documentation Alignment & Unified Specification**

- Removed all MVP/Phase 2 distinctions from requirements and steering documents
- Updated component count to 33 (was "23 MVP + 9 Phase 2")
- Updated page count to 9 (added ServerDetailsPage, QuotasPage)
- Integrated future features into main feature sections as unified specification
- Verified wireframes in UX_UI_DESIGN_SPECIFICATIONS.md match actual TSX implementations
- Cross-verified alignment across all three requirements documents (PRD, SRS, UX Specs)
- Updated .amazonq/rules and .kiro/steering files for consistency
- Clarified DRS regions: 30 total (28 commercial + 2 GovCloud)

**Recovery Instance Source Tracking** - `51c0031`

New API endpoint and enhanced UI for tracking existing recovery instances before starting drills:

API Changes:

- Added `GET /recovery-plans/{planId}/check-existing-instances` endpoint
- Returns existing recovery instances with source execution and plan tracking
- Enriched response with EC2 details: Name tag, private IP, instance type, launch time
- Fixed execution history lookup to correctly search `Waves[].ServerStatuses[].SourceServerId`

Frontend Changes:

- Enhanced warning dialog shows detailed instance information before drill
- Displays: instance name, private IP, instance type, launch time
- Updated warning message: clarifies drill will TERMINATE existing instances (not create additional)
- Shows source plan name that created the instances

Code Cleanup:

- Removed unused `get_protection_group_servers_legacy` function (~110 lines)
- Deleted `cfn/api-stack.yaml.bak` backup file

**DRS Launch Settings - Full UI and API Support** - `2272e5e`

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
- SSM runbook for automated execution (example templates available separately)
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

---

## Archived Entries

For changelog entries from November 2025 and earlier, see [CHANGELOG_ARCHIVE.md](CHANGELOG_ARCHIVE.md).

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
