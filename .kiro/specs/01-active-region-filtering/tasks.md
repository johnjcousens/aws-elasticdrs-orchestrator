# Implementation Plan: Active Region Filtering

## Overview

This implementation plan breaks down the active region filtering feature into discrete, incremental tasks. The plan follows a phased approach to minimize risk and ensure backward compatibility at each step.

**Key Principles**:
- Each task builds on previous tasks
- Backward compatibility maintained throughout
- Testing integrated at each phase
- CloudFormation changes isolated to minimize risk

## Tasks

- [ ] 1. Create shared active region filter module
  - Create `lambda/shared/active_region_filter.py` with region filtering logic
  - Implement `get_active_regions()` function with caching and fallback
  - Implement `update_region_status()` function for DynamoDB updates
  - Implement `invalidate_region_cache()` function for cache management
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 6.1, 6.2, 10.2, 10.3, 10.4_

- [ ] 1.1 Write property test for active region filtering consistency
  - **Property 1: Active Region Filtering Consistency**
  - **Validates: Requirements 1.2, 2.2, 3.2, 4.2, 9.2**

- [ ] 1.2 Write property test for fallback to all regions
  - **Property 2: Fallback to All Regions**
  - **Validates: Requirements 1.3, 1.4, 2.3, 3.3, 6.1, 6.2, 6.4, 8.1**

- [ ] 1.3 Write property test for cache TTL behavior
  - **Property 8: Cache TTL Behavior**
  - **Validates: Requirements 10.4**

- [ ] 1.4 Write property test for pagination handling
  - **Property 7: Pagination Handling**
  - **Validates: Requirements 10.3**

- [ ] 2. Create shared inventory query module
  - Create `lambda/shared/inventory_query.py` with inventory database queries
  - Implement `query_inventory_by_regions()` function with freshness check
  - Implement `is_inventory_fresh()` function to check data age
  - Add fallback to DRS API when inventory is stale
  - _Requirements: 12.2, 12.3, 12.4, 12.8_

- [ ] 2.1 Write property test for inventory database freshness check
  - **Property 4: Inventory Database Freshness Check**
  - **Validates: Requirements 12.3, 12.4, 12.8**

- [ ] 2.2 Write property test for inventory data completeness
  - **Property 9: Inventory Data Completeness**
  - **Validates: Requirements 4.3, 12.9**

- [ ] 3. Checkpoint - Verify shared modules
  - Ensure all tests pass for shared modules
  - Verify modules can be imported without errors
  - Ask the user if questions arise

- [ ] 4. Update tag sync to use active region filtering
  - Modify `handle_drs_tag_sync()` in `lambda/data-management-handler/index.py`
  - Call `get_active_regions()` before scanning regions
  - Add fallback to `DRS_REGIONS` if region status table is empty
  - Add logging for regions scanned vs skipped
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 4.1 Write property test for tag sync region filtering
  - **Property 1: Active Region Filtering Consistency** (tag sync specific)
  - **Validates: Requirements 2.2**

- [ ] 5. Update inventory sync to use active region filtering and update region status
  - Modify `handle_sync_source_server_inventory()` in `lambda/query-handler/index.py`
  - Call `get_active_regions()` before scanning regions
  - Call `update_region_status()` for each region scanned
  - Call `invalidate_region_cache()` after inventory sync completes
  - Add error handling to record failures in region status table
  - _Requirements: 4.1, 4.2, 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 5.1 Write property test for region status table updates
  - **Property 3: Region Status Table Updates**
  - **Validates: Requirements 5.1, 5.3, 5.4, 5.5**

- [ ] 5.2 Write property test for cache invalidation
  - **Property 6: Cache Invalidation**
  - **Validates: Requirements 10.5**

- [ ] 6. Checkpoint - Verify tag sync and inventory sync optimizations
  - Run tag sync and verify only active regions are scanned
  - Run inventory sync and verify region status table is updated
  - Verify cache is invalidated after inventory sync
  - Check CloudWatch logs for performance improvements
  - Ask the user if questions arise


- [ ] 7. Copy staging account sync functions to data-management-handler
  - Copy `handle_sync_staging_accounts()` from query-handler to data-management-handler
  - Copy `auto_extend_staging_servers()` from query-handler to data-management-handler
  - Copy `extend_source_server()` from query-handler to data-management-handler
  - Copy `get_extended_source_servers()` from query-handler to data-management-handler
  - Copy `get_staging_account_servers()` from query-handler to data-management-handler
  - Update all copied functions to accept `active_regions` parameter
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ] 8. Update copied staging account sync functions to use region filtering
  - Modify `handle_sync_staging_accounts()` to call `get_active_regions()`
  - Pass `active_regions` to `auto_extend_staging_servers()`
  - Update `get_staging_account_servers()` to use inventory database first
  - Add fallback to DRS API if inventory is stale
  - Update `get_extended_source_servers()` to only scan active regions
  - _Requirements: 3.1, 3.2, 9.1, 9.2, 11.12_

- [ ] 8.1 Write property test for staging sync region filtering
  - **Property 11: Moved Functions Use Region Filtering**
  - **Validates: Requirements 11.12**

- [ ] 8.2 Write property test for API call reduction
  - **Property 5: API Call Reduction**
  - **Validates: Requirements 9.4, 12.5**

- [ ] 8.3 Write property test for cross-account IAM assumptions
  - **Property 12: Cross-Account IAM Assumptions Limited to Active Regions**
  - **Validates: Requirements 9.3**

- [ ] 9. Update data-management-handler direct invocation routing
  - Add `sync_staging_accounts` operation to direct invocation handler
  - Ensure operation routes to local `handle_sync_staging_accounts()` function
  - Maintain backward compatibility with existing operation names
  - _Requirements: 11.10_

- [ ] 9.1 Write unit test for direct invocation routing
  - Test that `sync_staging_accounts` operation calls correct function
  - **Validates: Requirements 11.10**

- [ ] 10. Update CloudFormation EventBridge stack
  - Modify `cfn/eventbridge-stack.yaml`
  - Change `StagingAccountSyncScheduleRule` target from `QueryHandlerFunctionArn` to `ApiHandlerFunctionArn`
  - Update `StagingAccountSyncSchedulePermission` to grant permissions to `ApiHandlerFunctionArn`
  - Update comments to reflect new handler routing
  - _Requirements: 11.6, 11.7, 11.14_

- [ ] 10.1 Write unit test for CloudFormation template validation
  - Validate EventBridge rule targets correct Lambda function
  - **Validates: Requirements 11.6, 11.7**

- [ ] 11. Checkpoint - Verify staging account sync refactoring
  - Deploy CloudFormation changes using `./scripts/deploy.sh dev`
  - Verify EventBridge rule targets data-management-handler
  - Trigger staging account sync and verify it executes correctly
  - Verify only active regions are scanned
  - Check CloudWatch logs for successful execution
  - Ask the user if questions arise

- [ ] 12. Remove old staging account sync functions from query-handler
  - Remove `handle_sync_staging_accounts()` from query-handler
  - Remove `auto_extend_staging_servers()` from query-handler
  - Remove `extend_source_server()` from query-handler
  - Remove `get_extended_source_servers()` from query-handler
  - Remove `get_staging_account_servers()` from query-handler
  - Verify query-handler contains only read-only operations
  - _Requirements: 11.13_

- [ ] 12.1 Write unit test to verify query-handler has no write operations
  - Test that query-handler does not contain staging account sync functions
  - **Validates: Requirements 11.13**

- [ ] 13. Add CloudWatch metrics for monitoring
  - Add custom metrics to `get_active_regions()` for active region count
  - Add custom metrics for regions skipped
  - Add custom metrics for API call reduction percentage
  - Add custom metrics for inventory database usage
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 14. Update inventory database during fallback queries and preserve failback topology
  - Modify fallback logic in `query_inventory_by_regions()` to update inventory database
  - Ensure DRS API queries populate inventory for future use
  - **CRITICAL**: Preserve original replication topology (originalSourceRegion, originalAccountId, originalReplicationConfigTemplateId)
  - When server exists in inventory, preserve existing topology fields during updates
  - When server is new, capture current region/account as original topology
  - Add `get_failback_topology()` function to retrieve original topology for failback operations
  - Update inventory sync to capture and preserve topology information
  - _Requirements: 12.10, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9, 13.10_

- [ ] 14.1 Write property test for inventory database updates during fallback and topology preservation
  - **Property 10: Inventory Database Updates During Fallback**
  - **Property 13: Failback Topology Preservation** - Verify original topology is preserved across inventory updates
  - **Validates: Requirements 12.10, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9**

- [ ] 15. Add integration tests for end-to-end workflows
  - Test tag sync with region filtering end-to-end
  - Test staging account sync after refactoring end-to-end
  - Test inventory sync updates region status table
  - Test fallback behavior when region status table is empty
  - Test API Gateway routing after refactoring
  - Test direct Lambda invocation routing
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.10_

- [ ] 16. Add performance validation tests
  - Measure API call reduction (target: 80-90%)
  - Measure response time improvement (target: 70-80%)
  - Measure inventory database query performance (target: < 500ms)
  - Measure cache effectiveness (target: > 90% hit rate)
  - _Requirements: 13.12_

- [ ] 17. Final checkpoint - Comprehensive validation
  - Run all unit tests: `pytest tests/unit/ -v`
  - Run all property tests: `pytest -k property --hypothesis-show-statistics`
  - Run all integration tests: `pytest tests/integration/ -v`
  - Run validation: `./scripts/deploy.sh dev --validate-only`
  - Verify all CloudWatch metrics are being published
  - Verify performance improvements meet targets
  - Review CloudWatch logs for errors
  - Ask the user if questions arise

## Notes

- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at reasonable breaks
- Property tests validate universal correctness properties across randomized inputs
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- All tasks follow PEP 8 standards with max line length of 79 characters
- All code must pass validation pipeline: flake8, black, bandit, cfn-lint, cfn_nag, detect-secrets
- Deployment must use `./scripts/deploy.sh dev` (never direct AWS commands)
