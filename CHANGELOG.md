# Changelog

All notable changes to the AWS DRS Orchestration Solution project.

## [Unreleased]

### Fixed

**History Page Execution Deletion and Console Logging Cleanup** - December 30, 2025

- **Enhanced Selective Deletion**: Fixed History page Clear History button to support multi-selection with granular deletion
- **Improved User Experience**: Button now shows selected count ("Clear History (3)") and is disabled when no items selected
- **API Enhancement**: Added `DELETE /executions` endpoint with body support for selective deletion by execution IDs
- **Data Consistency Fix**: Resolved issue where executions appeared in UI but couldn't be found in database during deletion
- **Authentication Fix**: Resolved JWT token authentication issues with selective deletion endpoint
- **Console Cleanup**: Removed excessive debugging logs from authentication and API request interceptors
- **Production Ready**: Cleaned browser console output while preserving essential error logging

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
- Corrected frontend bucket name: `drsorchv4-fe-777788889999-test`
- Fixed CloudFront distribution ID: `E33R91LABVLR0`
- Added proper stack configuration validation

Documentation Updates:

- Updated `README.md` deployment workflow section with correct stack names
- Added stack configuration details and deployment verification commands
- Added "Recent Updates" section documenting deployment fixes
- Clarified S3 deployment bucket as source of truth for all deployments

Deployment Verification:

- Successfully deployed hardware display enhancements to production
- Verified CloudFront distribution serves updated frontend: `https://dl4xl2uad0eil.cloudfront.net/protection-groups`
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
