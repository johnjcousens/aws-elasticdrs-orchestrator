# Requirements Document

## Introduction

This document specifies requirements for refactoring the sync_source_server_inventory function in lambda/query-handler/index.py. This refactoring MUST be implemented AFTER the active-region-filtering spec is complete.

**Post-Active-Region-Filtering State:**
After active-region-filtering is complete, the sync_source_server_inventory function will:
- Use `get_active_regions()` for region filtering (active-region-filtering task 5)
- Call `update_region_status()` for each region (active-region-filtering task 5)
- Call `invalidate_region_cache()` after completion (active-region-filtering task 5)
- No longer handle staging account sync operations (moved to data-management-handler in tasks 7-12)

**Remaining Responsibilities to Refactor:**
Even after active-region-filtering, the function will still be a monolithic 300+ line function handling:
1. Account collection from DynamoDB
2. Cross-account credential management
3. Multi-region DRS queries with parallel execution
4. EC2 metadata enrichment
5. Cross-account EC2 queries
6. DynamoDB batch writing

This refactoring will decompose these remaining responsibilities into focused, testable, and maintainable components while preserving all existing functionality and maintaining backward compatibility.

## Glossary

- **Sync_Function**: The sync_source_server_inventory function being refactored
- **Target_Account**: AWS account containing DRS source servers to be inventoried
- **Staging_Account**: AWS account used for DRS staging operations
- **DRS_Client**: AWS SDK client for Elastic Disaster Recovery service
- **EC2_Client**: AWS SDK client for Elastic Compute Cloud service
- **Source_Server**: A server protected by AWS DRS
- **Region_Status**: Status information about DRS availability in a specific region
- **Enriched_Server**: Source server data augmented with EC2 instance metadata
- **Inventory_Table**: DynamoDB table storing source server inventory
- **Region_Status_Table**: DynamoDB table storing region availability status
- **Cross_Account_Query**: API query executed using assumed role credentials in another account

## Requirements

### Requirement 1: Function Decomposition

**User Story:** As a developer, I want the sync_source_server_inventory function decomposed into single-responsibility functions, so that each component is independently testable and maintainable.

#### Acceptance Criteria

1. THE Sync_Function SHALL be decomposed into at least 6 separate functions with single responsibilities
2. WHEN the refactoring is complete, THEN each extracted function SHALL have a clear, single purpose documented in its docstring
3. WHEN the refactoring is complete, THEN no extracted function SHALL exceed 100 lines of code
4. THE Sync_Function SHALL become a high-level orchestrator that delegates to extracted functions
5. WHEN the refactoring is complete, THEN the orchestrator function SHALL not exceed 50 lines of code
6. THE refactored code SHALL continue to use `get_active_regions()`, `update_region_status()`, and `invalidate_region_cache()` from the shared active_region_filter module

### Requirement 2: Account Collection Extraction

**User Story:** As a developer, I want account collection logic extracted into a dedicated function, so that I can test and reuse account gathering independently.

#### Acceptance Criteria

1. THE System SHALL provide a collect_accounts_to_query function that returns Target_Account lists
2. WHEN collect_accounts_to_query is called, THEN it SHALL query DynamoDB for target accounts only
3. WHEN collect_accounts_to_query encounters a DynamoDB error, THEN it SHALL raise an exception with descriptive error message
4. THE collect_accounts_to_query function SHALL return a list of account dictionaries with accountId and accountName fields
5. THE collect_accounts_to_query function SHALL NOT query for staging accounts (staging account sync has been moved to data-management-handler)

### Requirement 3: Credential Management Extraction

**User Story:** As a developer, I want credential management logic extracted into a dedicated function, so that I can test role assumption independently and reuse it in other contexts.

#### Acceptance Criteria

1. THE System SHALL provide a get_account_credentials function that assumes roles for cross-account access
2. WHEN get_account_credentials is called with a Target_Account, THEN it SHALL attempt to assume the specified role
3. WHEN role assumption succeeds, THEN get_account_credentials SHALL return credentials dictionary with AccessKeyId, SecretAccessKey, and SessionToken
4. WHEN role assumption fails, THEN get_account_credentials SHALL return None
5. WHEN get_account_credentials returns None, THEN the caller SHALL handle the missing credentials gracefully

### Requirement 4: Multi-Region DRS Query Extraction

**User Story:** As a developer, I want multi-region DRS query logic extracted into a dedicated function, so that I can test parallel region queries independently.

#### Acceptance Criteria

1. THE System SHALL provide a query_drs_all_regions function that queries DRS across active AWS regions in parallel
2. WHEN query_drs_all_regions is called, THEN it SHALL query DRS only in regions returned by `get_active_regions()`
3. WHEN query_drs_all_regions completes, THEN it SHALL return a tuple containing server list and region status dictionary
4. WHEN a region query fails, THEN query_drs_all_regions SHALL capture the error in region status without failing the entire operation
5. THE query_drs_all_regions function SHALL use ThreadPoolExecutor for parallel execution
6. WHEN query_drs_all_regions completes, THEN it SHALL call `update_region_status()` for each region queried

### Requirement 5: Single-Region DRS Query Extraction

**User Story:** As a developer, I want single-region DRS query logic extracted into a dedicated function, so that I can test individual region queries and error handling independently.

#### Acceptance Criteria

1. THE System SHALL provide a query_drs_single_region function that queries DRS in one region
2. WHEN query_drs_single_region is called, THEN it SHALL create a DRS_Client for the specified region
3. WHEN query_drs_single_region succeeds, THEN it SHALL return a dictionary with status "success" and server list
4. WHEN query_drs_single_region encounters an error, THEN it SHALL return a dictionary with status "error" and error details
5. THE query_drs_single_region function SHALL handle 8 distinct error types: AccessDeniedException, UnrecognizedClientException, InvalidRequestException, ThrottlingException, ServiceQuotaExceededException, InternalServerException, ClientError, and generic Exception
6. WHEN query_drs_single_region encounters ThrottlingException, THEN it SHALL include retry guidance in error details
7. WHEN query_drs_single_region encounters ServiceQuotaExceededException, THEN it SHALL include quota increase guidance in error details

### Requirement 6: Region Status Tracking Extraction

**User Story:** As a developer, I want region status tracking logic extracted into a dedicated function, so that I can test status persistence independently.

#### Acceptance Criteria

1. THE refactored code SHALL use the `update_region_status()` function from the shared active_region_filter module
2. WHEN the orchestrator function completes, THEN it SHALL call `invalidate_region_cache()` to refresh the cache
3. THE refactored code SHALL NOT implement its own region status tracking (this is handled by active_region_filter module)
4. WHEN region queries complete, THEN region status SHALL be updated via `update_region_status()` for each region
5. THE refactored code SHALL handle region status updates within the query_drs_all_regions function

### Requirement 7: EC2 Metadata Enrichment Extraction

**User Story:** As a developer, I want EC2 metadata enrichment logic extracted into a dedicated function, so that I can test enrichment independently and reuse it in other contexts.

#### Acceptance Criteria

1. THE System SHALL provide an enrich_with_ec2_metadata function that augments server data with EC2 instance details
2. WHEN enrich_with_ec2_metadata is called, THEN it SHALL query EC2 for network interface details
3. WHEN enrich_with_ec2_metadata is called, THEN it SHALL query EC2 for instance tags
4. WHEN enrich_with_ec2_metadata is called, THEN it SHALL query EC2 for instance profile information
5. WHEN EC2 queries fail, THEN enrich_with_ec2_metadata SHALL preserve original server data without enrichment
6. THE enrich_with_ec2_metadata function SHALL handle cross-account EC2 queries using source account credentials

### Requirement 8: EC2 Instance Query Extraction

**User Story:** As a developer, I want EC2 instance query logic extracted into a dedicated function, so that I can test EC2 API interactions independently.

#### Acceptance Criteria

1. THE System SHALL provide a query_ec2_instances function that retrieves instance details from EC2
2. WHEN query_ec2_instances is called, THEN it SHALL create an EC2_Client for the specified region
3. WHEN query_ec2_instances is called with instance IDs, THEN it SHALL query EC2 describe_instances API
4. WHEN query_ec2_instances succeeds, THEN it SHALL return a dictionary mapping instance IDs to instance details
5. WHEN query_ec2_instances encounters an error, THEN it SHALL return an empty dictionary

### Requirement 9: DynamoDB Batch Writing Extraction

**User Story:** As a developer, I want DynamoDB batch writing logic extracted into a dedicated function, so that I can test inventory persistence independently.

#### Acceptance Criteria

1. THE System SHALL provide a write_inventory_to_dynamodb function that persists enriched server inventory
2. WHEN write_inventory_to_dynamodb is called, THEN it SHALL write servers to Inventory_Table in batches of 25
3. WHEN write_inventory_to_dynamodb completes, THEN it SHALL return a tuple containing success count and failure count
4. WHEN write_inventory_to_dynamodb encounters batch write errors, THEN it SHALL retry failed items
5. WHEN write_inventory_to_dynamodb encounters persistent failures, THEN it SHALL log errors and continue processing remaining items

### Requirement 10: Backward Compatibility

**User Story:** As a system operator, I want the refactored function to maintain backward compatibility, so that existing integrations continue working without modification.

#### Acceptance Criteria

1. WHEN the refactoring is complete, THEN the handle_sync_source_server_inventory function SHALL maintain the same function signature
2. WHEN the refactoring is complete, THEN the response format SHALL remain identical to the current implementation
3. WHEN the refactoring is complete, THEN all existing API contracts SHALL be preserved
4. WHEN the refactoring is complete, THEN all existing tests SHALL pass without modification
5. WHEN the refactoring is complete, THEN the function SHALL produce identical output for identical input

### Requirement 11: Error Handling Preservation

**User Story:** As a system operator, I want all existing error handling behavior preserved, so that error scenarios continue to be handled correctly.

#### Acceptance Criteria

1. WHEN the refactoring is complete, THEN all 8 DRS error types SHALL continue to be handled correctly
2. WHEN the refactoring is complete, THEN error messages SHALL remain descriptive and actionable
3. WHEN the refactoring is complete, THEN partial failures SHALL not prevent successful processing of other regions or accounts
4. WHEN the refactoring is complete, THEN all errors SHALL be logged with appropriate severity levels
5. WHEN the refactoring is complete, THEN error responses SHALL include sufficient context for debugging

### Requirement 12: Code Quality Standards

**User Story:** As a developer, I want the refactored code to follow PEP 8 standards, so that code quality and consistency are maintained.

#### Acceptance Criteria

1. THE refactored code SHALL comply with PEP 8 line length limit of 120 characters
2. THE refactored code SHALL use 4-space indentation
3. THE refactored code SHALL use double quotes for strings
4. THE refactored code SHALL include comprehensive docstrings for all functions
5. THE refactored code SHALL include type hints for all function parameters and return values

### Requirement 13: Testing Requirements

**User Story:** As a developer, I want comprehensive tests for all extracted functions, so that I can verify correctness and prevent regressions.

#### Acceptance Criteria

1. WHEN the refactoring is complete, THEN each extracted function SHALL have dedicated unit tests
2. WHEN the refactoring is complete, THEN unit tests SHALL achieve at least 90% code coverage for extracted functions
3. WHEN the refactoring is complete, THEN integration tests SHALL verify the orchestrator function works correctly
4. WHEN the refactoring is complete, THEN tests SHALL verify error handling for all error scenarios
5. WHEN the refactoring is complete, THEN tests SHALL verify backward compatibility with existing behavior
6. WHEN the refactoring is complete, THEN property-based tests SHALL verify invariants hold across randomized inputs
7. WHEN the refactoring is complete, THEN comparison tests SHALL verify refactored output matches original output for identical inputs

### Requirement 14: Shared Utility Integration

**User Story:** As a developer, I want the refactored functions to use shared utilities, so that code duplication is eliminated and consistency is maintained across handlers.

#### Acceptance Criteria

1. THE System SHALL provide a `lambda/shared/dynamodb_tables.py` module with centralized table getters
2. WHEN `collect_accounts_to_query()` is implemented, THEN it SHALL use `dynamodb_tables.get_target_accounts_table()`
3. WHEN `get_account_credentials()` is implemented, THEN it SHALL use `cross_account.get_cross_account_session()`
4. WHEN `query_drs_single_region()` is implemented, THEN it SHALL use `cross_account.create_drs_client()`
5. WHEN `query_ec2_instances()` is implemented, THEN it SHALL use `cross_account.create_ec2_client()`
6. WHEN `write_inventory_to_dynamodb()` is implemented, THEN it SHALL use shared table getter for inventory table
7. THE refactored code SHALL eliminate duplicate table getter functions from query-handler

### Requirement 14: Shared Utility Integration

**User Story:** As a developer, I want the refactored functions to use shared utilities, so that code duplication is eliminated and consistency is maintained across handlers.

#### Acceptance Criteria

1. THE System SHALL provide a `lambda/shared/dynamodb_tables.py` module with centralized table getters
2. WHEN `collect_accounts_to_query()` is implemented, THEN it SHALL use `dynamodb_tables.get_target_accounts_table()`
3. WHEN `get_account_credentials()` is implemented, THEN it SHALL use `cross_account.get_cross_account_session()`
4. WHEN `query_drs_single_region()` is implemented, THEN it SHALL use `cross_account.create_drs_client()`
5. WHEN `query_ec2_instances()` is implemented, THEN it SHALL use `cross_account.create_ec2_client()`
6. WHEN `write_inventory_to_dynamodb()` is implemented, THEN it SHALL use shared table getter for inventory table
7. THE refactored code SHALL eliminate duplicate table getter functions from query-handler

### Requirement 15: Incremental Refactoring Strategy

**User Story:** As a developer, I want the refactoring to be done incrementally with validation at each step, so that I can catch issues early and minimize risk.

#### Acceptance Criteria

1. THE refactoring SHALL be implemented in phases with validation checkpoints between phases
2. WHEN each function is extracted, THEN it SHALL be tested independently before integration
3. WHEN each phase completes, THEN all existing tests SHALL pass without modification
4. WHEN each phase completes, THEN manual testing SHALL verify inventory sync produces identical results
5. THE refactoring SHALL maintain a working state at all times (no broken intermediate states)
6. WHEN issues are discovered, THEN the refactoring SHALL be rolled back to the last known good state

### Requirement 16: Behavioral Equivalence Validation

**User Story:** As a system operator, I want proof that the refactored function produces identical output to the original, so that I can trust the refactoring doesn't introduce bugs.

#### Acceptance Criteria

1. THE System SHALL provide comparison tests that run both original and refactored implementations side-by-side
2. WHEN comparison tests run, THEN they SHALL verify identical output for at least 10 different input scenarios
3. WHEN comparison tests run, THEN they SHALL verify identical error handling for all 8 DRS error types
4. WHEN comparison tests run, THEN they SHALL verify identical region status updates
5. WHEN comparison tests run, THEN they SHALL verify identical DynamoDB writes (same items, same order)
6. THE comparison tests SHALL run against real AWS services in dev environment (not just mocks)
7. WHEN any behavioral difference is detected, THEN the refactoring SHALL be corrected before proceeding

### Requirement 17: Rollback Safety

**User Story:** As a developer, I want the ability to quickly rollback the refactoring if issues are discovered in production, so that service availability is maintained.

#### Acceptance Criteria

1. THE refactoring SHALL preserve the original function implementation as `handle_sync_source_server_inventory_legacy()`
2. THE System SHALL provide a feature flag to switch between original and refactored implementations
3. WHEN the feature flag is set to "legacy", THEN the original implementation SHALL be used
4. WHEN the feature flag is set to "refactored", THEN the new implementation SHALL be used
5. THE feature flag SHALL be configurable via environment variable without code deployment
6. WHEN issues are discovered, THEN operators SHALL be able to rollback by changing the environment variable
7. THE legacy implementation SHALL be maintained for at least 30 days after refactoring deployment
