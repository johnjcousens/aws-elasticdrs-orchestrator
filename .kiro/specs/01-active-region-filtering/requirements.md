# Requirements Document

## Introduction

The AWS DRS Orchestration Platform currently scans all 28 DRS-enabled regions for various EventBridge-triggered operations including tag synchronization, staging account sync, and source server inventory sync. This approach is inefficient because most customers only use DRS in 2-5 regions, resulting in unnecessary API calls, increased latency, and potential rate limiting issues.

This feature introduces active region filtering to optimize region scanning by querying the existing DRSRegionStatusTable before performing multi-region operations, significantly reducing API calls and improving performance.

**Note:** This feature also addresses an architectural issue where staging account sync operations are currently located in query-handler despite performing write operations. These operations should be moved to data-management-handler to maintain proper separation of concerns (query-handler should be read-only).

## Glossary

- **DRS**: AWS Elastic Disaster Recovery service
- **Region**: AWS geographic region where DRS is available
- **Active Region**: AWS region with DRS initialized and containing source servers (serverCount > 0)
- **Region Status Table**: DynamoDB table tracking DRS region status and server counts
- **Tag Sync**: Operation that synchronizes EC2 tags to DRS source servers (data-management-handler)
- **Staging Account Sync**: Operation that discovers and syncs DRS staging accounts (currently in query-handler, should be in data-management-handler)
- **Source Server Inventory Sync**: Operation that syncs DRS server data to DynamoDB (query-handler - read-only)
- **EventBridge**: AWS service that triggers scheduled Lambda operations
- **API Call**: Request to AWS DRS API (DescribeSourceServers, etc.)
- **Scan Operation**: Multi-region query operation that checks DRS status across regions

## Requirements

### Requirement 1: Query Region Status Before Scanning

**User Story:** As an operations engineer, I want the platform to check which regions have active DRS servers before scanning, so that unnecessary API calls are avoided.

#### Acceptance Criteria

1. WHEN a multi-region scan operation starts, THE System SHALL query the DRSRegionStatusTable to retrieve active regions
2. WHEN the region status table contains entries with serverCount > 0, THE System SHALL filter to only those active regions
3. WHEN the region status table is empty or unavailable, THE System SHALL fall back to scanning all 28 DRS regions
4. WHEN querying the region status table, THE System SHALL handle DynamoDB errors gracefully and fall back to full region scan
5. THE System SHALL log the number of active regions found and the filtering decision

### Requirement 2: Optimize Tag Synchronization Operations

**User Story:** As a platform administrator, I want tag synchronization to only scan active regions, so that the hourly sync completes faster and uses fewer API calls.

#### Acceptance Criteria

1. WHEN the tag sync operation starts, THE System SHALL query active regions from the region status table
2. WHEN active regions are found, THE System SHALL only scan those regions for DRS source servers
3. WHEN no active regions are found in the table, THE System SHALL scan all 28 regions as fallback
4. THE System SHALL log the number of regions scanned and the number of API calls made
5. WHEN tag sync completes, THE System SHALL report the time saved compared to full region scan

### Requirement 3: Optimize Staging Account Sync Operations

**User Story:** As a disaster recovery coordinator, I want staging account discovery to only check active regions, so that the 5-minute sync interval doesn't cause API throttling.

**Note:** Staging account sync operations should be moved from query-handler to data-management-handler as part of this feature, since they perform write operations (extending DRS servers) and query-handler should be read-only.

#### Acceptance Criteria

1. WHEN staging account sync starts, THE System SHALL query active regions from the region status table
2. WHEN active regions are found, THE System SHALL only query those regions for staging accounts
3. WHEN the region status table is unavailable, THE System SHALL scan all 28 regions
4. THE System SHALL complete staging account sync within 30 seconds for typical deployments (2-5 active regions)
5. THE System SHALL be located in data-management-handler (not query-handler) to maintain proper separation of concerns

### Requirement 4: Optimize Source Server Inventory Sync

**User Story:** As a platform operator, I want source server inventory sync to focus on active regions, so that the 15-minute sync completes quickly and provides fresh data.

#### Acceptance Criteria

1. WHEN source server inventory sync starts, THE System SHALL query active regions from the region status table
2. WHEN active regions are found, THE System SHALL only scan those regions for source servers
3. WHEN scanning active regions, THE System SHALL retrieve full server details including replication state
4. THE System SHALL update the DynamoDB inventory table with current server data
5. WHEN inventory sync completes, THE System SHALL log the number of servers synced per region

### Requirement 5: Maintain Region Status Table Accuracy

**User Story:** As a system administrator, I want the region status table to be automatically updated, so that active region filtering remains accurate as servers are added or removed.

#### Acceptance Criteria

1. WHEN source server inventory sync runs, THE System SHALL update the region status table with current server counts
2. WHEN a region has zero servers, THE System SHALL update the region status table with serverCount = 0
3. WHEN a region has DRS servers, THE System SHALL update the region status table with the current count
4. THE System SHALL update the lastChecked timestamp for each region scanned
5. WHEN DRS API calls fail for a region, THE System SHALL record the error in the region status table

### Requirement 6: Provide Fallback for Empty Region Status Table

**User Story:** As a platform developer, I want operations to work correctly even when the region status table is empty, so that new deployments and edge cases are handled gracefully.

#### Acceptance Criteria

1. WHEN the region status table is empty, THE System SHALL scan all 28 DRS regions
2. WHEN the region status table query fails, THE System SHALL log the error and scan all 28 regions
3. WHEN falling back to full region scan, THE System SHALL log a warning message
4. THE System SHALL populate the region status table during the fallback scan
5. WHEN the region status table becomes populated, THE System SHALL use active region filtering on subsequent operations

### Requirement 7: Performance Improvement Metrics

**User Story:** As a platform architect, I want to measure the performance improvement from active region filtering, so that I can validate the optimization effectiveness.

#### Acceptance Criteria

1. THE System SHALL log the number of regions scanned for each operation
2. THE System SHALL log the total execution time for multi-region operations
3. WHEN using active region filtering, THE System SHALL log the number of regions skipped
4. THE System SHALL calculate and log the percentage reduction in API calls
5. THE System SHALL track performance metrics in CloudWatch for monitoring

### Requirement 8: Backward Compatibility

**User Story:** As a deployment engineer, I want the active region filtering feature to work with existing infrastructure, so that no manual migration or data seeding is required.

#### Acceptance Criteria

1. THE System SHALL work correctly when the region status table is empty (new deployments)
2. THE System SHALL not require manual data seeding or migration scripts
3. THE System SHALL automatically populate the region status table during normal operations
4. THE System SHALL maintain compatibility with existing EventBridge schedules
5. THE System SHALL not break existing API endpoints or Lambda invocations

### Requirement 9: Extended Source Server Operations

**User Story:** As a disaster recovery engineer, I want extended source server operations to use active region filtering, so that cross-account queries are faster.

#### Acceptance Criteria

1. WHEN querying extended source servers across accounts, THE System SHALL use active region filtering
2. WHEN the region status table contains active regions, THE System SHALL only query those regions
3. THE System SHALL handle cross-account IAM role assumptions for active regions only
4. THE System SHALL reduce cross-account API calls by filtering to active regions
5. THE System SHALL complete extended source server queries within 60 seconds for typical deployments

### Requirement 10: Region Status Table Query Performance

**User Story:** As a performance engineer, I want region status table queries to be fast, so that the filtering optimization doesn't add latency.

#### Acceptance Criteria

1. THE System SHALL complete region status table queries within 100 milliseconds
2. THE System SHALL use DynamoDB scan operation to retrieve all region statuses
3. WHEN the region status table contains more than 28 entries, THE System SHALL handle pagination
4. THE System SHALL cache region status results for 60 seconds to avoid repeated queries
5. THE System SHALL invalidate the cache when source server inventory sync completes

### Requirement 11: Architectural Refactoring - Move Staging Account Sync

**User Story:** As a platform architect, I want staging account sync operations in data-management-handler, so that query-handler remains read-only and maintains proper separation of concerns.

**Current State Analysis:**

The following functions are currently in query-handler but perform write operations (DRS CreateExtendedSourceServer API calls):

1. **handle_sync_staging_accounts()** - EventBridge-triggered auto-extend operation
   - Scans all 28 DRS regions to find staging account servers
   - Calls auto_extend_staging_servers() which performs write operations
   - Should be in data-management-handler

2. **auto_extend_staging_servers()** - Core auto-extend logic
   - Queries target accounts from DynamoDB
   - Calls extend_source_server() which performs DRS write operations
   - Should be in data-management-handler

3. **extend_source_server()** - DRS write operation
   - Calls DRS CreateExtendedSourceServer API (write operation)
   - Should be in data-management-handler

4. **get_extended_source_servers()** - Helper function
   - Queries DRS across all 28 regions to find extended servers
   - Read-only operation but used by auto-extend logic
   - Should move with auto-extend functions for cohesion

5. **get_staging_account_servers()** - Helper function
   - Queries DRS across all 28 regions to find staging servers
   - Read-only operation but used by auto-extend logic
   - Should move with auto-extend functions for cohesion

**Functions that should STAY in query-handler (read-only):**

1. **handle_discover_staging_accounts()** - Discovery operation
   - Queries DRS to discover staging accounts from extended servers
   - Read-only operation, returns data for UI display
   - Correctly placed in query-handler

2. **handle_validate_staging_account()** - Validation operation
   - Validates staging account access and DRS status
   - Read-only operation, returns validation results
   - Correctly placed in query-handler

3. **get_staging_accounts_direct()** - Query operation
   - Returns staging accounts for a target account
   - Read-only operation
   - Correctly placed in query-handler

4. **query_staging_accounts_from_target()** - Capacity query
   - Queries staging account capacity
   - Read-only operation
   - Correctly placed in query-handler

5. **handle_get_source_server_inventory()** - Inventory query
   - Queries source server inventory from DynamoDB
   - Read-only operation
   - Correctly placed in query-handler

**Functions already in data-management-handler (correct placement):**

1. **handle_add_staging_account()** - Add staging account to configuration
2. **handle_remove_staging_account()** - Remove staging account from configuration
3. **handle_sync_single_account()** - On-demand sync for single account (currently calls query-handler, needs refactoring)

#### Acceptance Criteria

1. THE System SHALL move handle_sync_staging_accounts() from query-handler to data-management-handler
2. THE System SHALL move auto_extend_staging_servers() from query-handler to data-management-handler
3. THE System SHALL move extend_source_server() from query-handler to data-management-handler
4. THE System SHALL move get_extended_source_servers() from query-handler to data-management-handler
5. THE System SHALL move get_staging_account_servers() from query-handler to data-management-handler
6. THE System SHALL update EventBridge StagingAccountSyncScheduleRule to invoke ApiHandlerFunctionArn (data-management-handler) instead of QueryHandlerFunctionArn
7. THE System SHALL update EventBridge StagingAccountSyncSchedulePermission to grant permissions to ApiHandlerFunctionArn
8. THE System SHALL update API Gateway AccountsTargetStagingAccountsSyncPostMethod to continue using ApiHandlerFunctionArn (already correct)
9. THE System SHALL update handle_sync_single_account() in data-management-handler to call local functions instead of query-handler
10. THE System SHALL update direct Lambda invocation routing to call data-management-handler for sync_staging_accounts operation
11. THE System SHALL maintain backward compatibility with existing API Gateway routes
12. THE System SHALL ensure all moved functions apply active region filtering
13. THE System SHALL verify query-handler contains only read-only operations after the refactoring
14. THE System SHALL update CloudFormation template comments to reflect the new handler routing

### Requirement 12: Use Inventory Database for Faster Queries

**User Story:** As a performance engineer, I want operations to query the source server inventory database instead of DRS/EC2 APIs, so that responses are faster and API rate limits are avoided.

**Context:** The platform maintains a `SOURCE_SERVER_INVENTORY_TABLE` (hrp-drs-tech-adapter-source-server-inventory-dev) that is synced every 15 minutes from DRS and EC2 APIs. This table contains comprehensive server information including hardware specs, network configuration, tags, and replication state.

#### Acceptance Criteria

1. WHEN determining active regions, THE System SHALL query the region status table first
2. WHEN active regions are identified, THE System SHALL query the source server inventory database for server details
3. WHEN the inventory database contains current data (lastUpdated within 15 minutes), THE System SHALL use inventory data instead of DRS API calls
4. WHEN the inventory database is empty or stale, THE System SHALL fall back to direct DRS API queries
5. THE System SHALL reduce DRS API calls by 90% for operations that can use inventory data
6. THE System SHALL complete inventory-based queries within 500 milliseconds
7. THE System SHALL log when inventory database is used vs direct API calls
8. THE System SHALL handle inventory database unavailability gracefully with API fallback
9. THE System SHALL ensure inventory data includes all required fields (sourceServerID, region, replicationState, tags)
10. THE System SHALL update the inventory database during fallback API queries to keep data fresh

### Requirement 13: Preserve Replication Topology for Failback

**User Story:** As a disaster recovery engineer, I want the inventory database to preserve original replication topology information, so that when I failback from DR to production, I can reinstall the DRS agent pointing to the correct original region and account.

**Context:** During a disaster recovery event, servers are recovered to a DR region. When failing back to the original production environment, the DRS agent must be reinstalled on the recovered servers. The agent installation requires knowing:
- Original source region where the server was replicated from
- Original staging account or target account where replication was configured
- Original replication configuration (subnet, security groups, etc.)

Without this information, manual lookup is required, which is error-prone and time-consuming during critical failback operations.

#### Acceptance Criteria

1. WHEN syncing source server inventory, THE System SHALL store the original source region for each server
2. WHEN syncing source server inventory, THE System SHALL store the original account ID (staging or target account)
3. WHEN syncing source server inventory, THE System SHALL store the original replication configuration details
4. WHEN a server is recovered to a DR region, THE System SHALL preserve the original topology information in the inventory database
5. WHEN querying the inventory database for failback, THE System SHALL return the original source region and account information
6. THE System SHALL include original topology fields in the inventory database schema:
   - originalSourceRegion: AWS region where server was originally replicated from
   - originalAccountId: AWS account ID where replication was configured
   - originalReplicationConfigurationTemplateId: DRS replication configuration template ID
7. WHEN the inventory database is queried during failback operations, THE System SHALL provide the original topology data to guide DRS agent reinstallation
8. THE System SHALL handle cases where original topology information is not available (legacy servers) by logging a warning
9. WHEN updating inventory during fallback API queries (Requirement 12.10), THE System SHALL preserve existing original topology information
10. THE System SHALL document the failback workflow that uses inventory database topology information

### Requirement 14: Comprehensive Testing for Refactoring

**User Story:** As a quality assurance engineer, I want extensive testing for the staging account sync refactoring, so that existing functionality is not broken during the architectural changes.

#### Acceptance Criteria

1. THE System SHALL include unit tests for all moved functions in data-management-handler
2. THE System SHALL include integration tests that verify staging account auto-extend works after refactoring
3. THE System SHALL include tests that verify EventBridge triggers invoke the correct handler
4. THE System SHALL include tests that verify API Gateway routes work correctly after refactoring
5. THE System SHALL include tests that verify active region filtering works in all moved functions
6. THE System SHALL include tests that verify cross-account IAM role assumption works in moved functions
7. THE System SHALL include tests that verify DRS CreateExtendedSourceServer API calls succeed
8. THE System SHALL include tests that verify error handling and fallback behavior
9. THE System SHALL include tests that verify concurrent sync operations don't conflict
10. THE System SHALL include end-to-end tests that verify the complete staging account sync workflow
11. THE System SHALL include tests that verify backward compatibility with existing data structures
12. THE System SHALL include tests that verify performance improvements from active region filtering
