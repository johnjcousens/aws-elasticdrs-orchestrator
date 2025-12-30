# Changelog

All notable changes to the AWS DRS Orchestration project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## December 30, 2025

**Version Language Update** - `6c5898d`
- Updated all "Production Ready v2.0" references to "MVP Drill Only Prototype v2.0" across 13 files
- Changed badge color from green to orange to reflect prototype status
- Updated git tag from `v2.0.0-production-ready` to `v2.0.0-mvp-drill-prototype`
- Synced updated documentation to S3 deployment bucket

**Complete Documentation Consolidation and Alignment** - `240c7ee`
- Streamlined README.md from 1,521 lines to 373 lines (75% reduction)
- Created three comprehensive guides:
  - `docs/guides/API_REFERENCE_GUIDE.md` - Complete REST API documentation
  - `docs/guides/DEVELOPMENT_WORKFLOW_GUIDE.md` - Development environment and deployment
  - `docs/guides/TROUBLESHOOTING_GUIDE.md` - Common issues and debugging
- Consolidated 29 implementation documents into 6 category documents (69% reduction)
- Archived 28 completed implementation plans to `docs/archive/implementation/`
- Fixed broken documentation links and aligned all documents with requirements specifications
- Updated `.kiro/steering/cicd.md` with comprehensive sync script documentation
- Successfully committed and synced all changes to GitLab and S3 deployment bucket

**History Page Date Filtering System** - `4f224c1`
- **Intuitive Date Range Filtering**: Added comprehensive date filtering for execution history with American date format (MM-DD-YYYY)
- **Quick Filter Buttons**: ButtonDropdown with preset ranges (Last Hour, Last 6 Hours, Today, Last 3 Days, Last Week, Last Month)
- **Custom Date Range**: Separate DateInput fields for flexible start and end date selection
- **Visual Feedback**: Clear indication of active date range with easy "Clear Filter" button
- **Proper Date Handling**: Robust Unix timestamp conversion and date parsing with `date-fns` library
- **Search Bar Enhancement**: Widened search bar for better readability and updated placeholder text
- **UI Simplification**: Removed redundant filter dropdowns to reduce interface clutter
- **American Format**: MM-DD-YYYY date format throughout for American audience preference

**History Page Execution Deletion and Console Logging Cleanup** - `08055d3`
- **Enhanced Selective Deletion**: Fixed History page Clear History button to support multi-selection with granular deletion
- **Improved User Experience**: Button now shows selected count ("Clear History (3)") and is disabled when no items selected
- **API Enhancement**: Added `DELETE /executions` endpoint with body support for selective deletion by execution IDs
- **Data Consistency Fix**: Resolved issue where executions appeared in UI but couldn't be found in database during deletion
- **Authentication Fix**: Resolved JWT token authentication issues with selective deletion endpoint
- **Console Cleanup**: Removed excessive debugging logs from authentication and API request interceptors

**Frontend Debugging Console Log Cleanup** - `b716a33`
- Removed frontend debugging console.log statements for cleaner production build

## December 29, 2024

**End of Year 2024 Working Prototype** - `ee4340a`
- Tagged as end-of-year 2024 working prototype milestone
- Core drill functionality operational

**Cross-Account Terminate Instances Support** - `c7dcabc`
- Fixed terminate instances functionality for cross-account scenarios
- Enhanced cross-account IAM role support

**Critical Instance Termination Timing Fix** - `8b10ac3`
- **CRITICAL FIX**: Fixed InstancesTerminated flag timing issue
- Resolved race condition in instance termination tracking

**Terminate Instances API and Button Logic Fixes** - `69172d0`, `071f9c8`, `dcd78c7`
- Fixed terminate-instances API and button visibility logic
- Improved terminate button logic for active vs completed executions
- Enhanced button visibility for in-progress executions

**Terminate Instances API 200 OK Response** - `8eb987b`
- Fixed terminate-instances API to return 200 OK when no instances exist
- Improved API response consistency

**Execution Cancellation Status Handling** - `768b0ce`
- Fixed ExecutionDetailsPage cancellation status handling
- Enhanced UI state management for cancelled executions

**DRS Termination Progress Tracking** - `0c91dae`, `93f1edd`
- Fixed termination progress tracking and cleanup debug logging
- Enhanced DRS termination progress tracking and cancelled execution UI refresh
- Improved real-time status updates

**Dashboard Region Auto-Detection** - `9490bf5`, `718a26c`
- Updated changelog and readme with dashboard region auto-detect feature
- **Dashboard Enhancement**: Auto-detect region with most replicating servers
- Intelligent region selection based on DRS server distribution

**Pause/Resume Execution and UI Improvements** - `779ab48`
- Fixed pause/resume execution functionality
- Enhanced UI feedback for execution state changes

**Drill Functionality Authentication Fix** - `a7e8bd1`
- 🎉 **MILESTONE**: Fixed drill functionality - authentication issue resolved
- Resolved critical authentication blocking drill execution

**Production Drill Functionality Deployment** - `c2f95eb`
- Deployed drill functionality fix to production environment
- Verified end-to-end drill execution capability

## December 28, 2025

**DRS Launch Settings - Full UI and API Support** - `2272e5e`

Complete DRS Launch Settings configuration for Protection Groups via UI and API:

**EC2 Launch Template Settings:**
- Subnet selection (target VPC subnet for recovery instances)
- Security Groups (one or more security groups)
- Instance Profile (IAM instance profile for recovery instance permissions)
- Instance Type (specific EC2 instance type override)

**DRS Launch Configuration Settings:**
- Instance Type Right Sizing (BASIC/IN_AWS/NONE)
- Launch Disposition (STARTED/STOPPED)
- OS Licensing (BYOL/AWS-provided)
- Copy Private IP (preserve source server's private IP)
- Transfer Server Tags (propagate EC2 tags to recovery instance)

**Frontend Changes:**
- New `LaunchConfigSection.tsx` component with dropdowns for all settings
- Updated `LaunchConfig` interface with all DRS fields
- Fixed conditional rendering of ServerDiscoveryPanel (prevents API calls when on Tags tab)
- Added 30-second auto-refresh pause when Protection Group dialog is open
- Fixed broken JSX in LoginPage.tsx

**Backend Changes:**
- `apply_launch_config_to_servers()` now passes all DRS settings: `targetInstanceTypeRightSizingMethod`, `launchDisposition`, `licensing`
- Enhanced version description tracking for audit trails
- `query_drs_servers_by_tags()` returns full server details for tag preview

**Documentation:**
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