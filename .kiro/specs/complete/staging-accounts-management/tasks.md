# Implementation Plan: Staging Accounts Management

## Overview

This implementation plan breaks down the Staging Accounts Management feature into discrete coding tasks. The feature extends DRS replication capacity by enabling users to configure multiple staging accounts alongside their target account. Each task builds incrementally, with testing integrated throughout to validate functionality early.

The implementation follows this sequence:
1. Backend data models and DynamoDB operations
2. Backend Lambda handlers for staging account management
3. Backend capacity query logic with multi-account support
4. Frontend components for UI and user interactions
5. API integration and end-to-end wiring
6. Property-based tests and comprehensive testing

## Tasks

- [x] 1. Set up backend data models and DynamoDB operations
  - Create Python data classes for StagingAccount and TargetAccount models
  - Implement DynamoDB helper functions for staging account CRUD operations
  - Add `stagingAccounts` attribute handling to existing Target Accounts table operations
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 1.1 Write property test for staging account persistence round trip
  - **Property 1: Staging Account Persistence Round Trip**
  - **Validates: Requirements 1.6, 8.1, 8.2, 8.3**

- [x] 2. Implement data management Lambda handler operations
  - [x] 2.1 Implement `handle_add_staging_account` operation
    - Validate staging account input structure
    - Check for duplicate staging accounts
    - Update Target Accounts table with new staging account
    - Return success response with updated staging accounts list
    - _Requirements: 1.6, 7.1_
  
  - [x] 2.2 Implement `handle_remove_staging_account` operation
    - Validate target account exists
    - Remove staging account from list
    - Update Target Accounts table
    - Return success response with updated staging accounts list
    - _Requirements: 2.2, 7.2_
  
  - [x] 2.3 Write property test for staging account removal completeness
    - **Property 2: Staging Account Removal Completeness**
    - **Validates: Requirements 2.2, 8.4**
  
  - [x] 2.4 Write unit tests for data management operations
    - Test add staging account success case
    - Test add duplicate staging account (error case)
    - Test remove staging account success case
    - Test remove non-existent staging account (error case)
    - _Requirements: 1.6, 2.2_

- [x] 3. Implement staging account validation logic
  - [x] 3.1 Implement `handle_validate_staging_account` operation
    - Assume role in staging account using STS
    - Check DRS initialization status
    - Count total and replicating servers
    - Calculate projected combined capacity
    - Return validation results with all required fields
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 7.3_
  
  - [x] 3.2 Implement error handling for validation failures
    - Handle role assumption failures (AccessDenied, InvalidClientTokenId)
    - Handle DRS uninitialized errors (UninitializedAccountException)
    - Return descriptive error messages for each failure type
    - _Requirements: 3.5, 3.6, 1.5_
  
  - [x] 3.3 Write property test for validation result completeness
    - **Property 6: Validation Result Completeness**
    - **Validates: Requirements 3.4, 1.4**
  
  - [x] 3.4 Write property test for validation error handling
    - **Property 7: Validation Error Handling**
    - **Validates: Requirements 3.5, 3.6, 1.5**
  
  - [x] 3.5 Write unit tests for validation edge cases
    - Test validation with valid staging account
    - Test validation with invalid role ARN
    - Test validation with DRS not initialized
    - Test validation with network errors
    - _Requirements: 3.1, 3.5, 3.6_

- [x] 4. Checkpoint - Ensure backend validation tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement multi-account capacity query logic
  - [x] 5.1 Implement `query_account_capacity` function
    - Assume role in account
    - Query all DRS-enabled regions concurrently
    - Handle uninitialized regions (return zero servers)
    - Aggregate regional results
    - Return account capacity with regional breakdown
    - _Requirements: 9.2, 9.3, 9.4_
  
  - [x] 5.2 Implement `query_all_accounts_parallel` function
    - Query target account and all staging accounts concurrently
    - Handle role assumption failures gracefully (mark as inaccessible)
    - Continue querying remaining accounts on individual failures
    - Return list of account capacity results
    - _Requirements: 9.1, 9.5, 9.6_
  
  - [x] 5.3 Implement `calculate_combined_metrics` function
    - Sum replicating servers across all accessible accounts
    - Calculate maximum capacity (num_accounts × 300)
    - Calculate percentage used
    - Calculate available slots
    - Return combined metrics
    - _Requirements: 4.2, 4.3_
  
  - [x] 5.4 Write property test for combined capacity aggregation
    - **Property 3: Combined Capacity Aggregation**
    - **Validates: Requirements 4.2, 4.3, 9.6**
  
  - [x] 5.5 Write property test for multi-account query parallelism
    - **Property 8: Multi-Account Query Parallelism**
    - **Validates: Requirements 9.1, 9.3**
  
  - [x] 5.6 Write property test for uninitialized region handling
    - **Property 9: Uninitialized Region Handling**
    - **Validates: Requirements 9.4**
  
  - [x] 5.7 Write property test for failed account resilience
    - **Property 10: Failed Account Resilience**
    - **Validates: Requirements 9.5**

- [x] 6. Implement capacity status and warning logic
  - [x] 6.1 Implement `calculate_account_status` function
    - Calculate status based on server count thresholds
    - Return OK, INFO, WARNING, CRITICAL, or HYPER-CRITICAL
    - _Requirements: 5.3, 5.4, 5.5, 5.6_
  
  - [x] 6.2 Implement `calculate_combined_status` function
    - Calculate combined status based on total replicating servers
    - Consider operational capacity (250 per account) and hard capacity (300 per account)
    - Return appropriate status level
    - _Requirements: 4.4_
  
  - [x] 6.3 Implement `generate_warnings` function
    - Generate per-account warnings based on thresholds
    - Generate combined capacity warnings
    - Include actionable guidance in warning messages
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  
  - [x] 6.4 Write property test for per-account status calculation
    - **Property 4: Per-Account Status Calculation**
    - **Validates: Requirements 5.3, 5.4, 5.5, 5.6**
  
  - [x] 6.5 Write property test for warning generation
    - **Property 5: Warning Generation Based on Thresholds**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6**

- [x] 7. Implement recovery capacity calculation
  - [x] 7.1 Implement `calculate_recovery_capacity` function
    - Calculate recovery capacity based on target account only (exclude staging)
    - Calculate percentage used against 4,000 instance limit
    - Determine status (OK, WARNING, CRITICAL)
    - Return recovery capacity metrics
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [x] 7.2 Write property test for recovery capacity status calculation
    - **Property 11: Recovery Capacity Status Calculation**
    - **Validates: Requirements 10.2, 10.3, 10.4, 10.5**

- [x] 8. Implement `handle_get_combined_capacity` operation
  - Retrieve target account configuration from DynamoDB
  - Extract staging accounts list (default to empty list if not present)
  - Query all accounts in parallel
  - Calculate combined metrics
  - Calculate per-account status and warnings
  - Calculate recovery capacity
  - Return complete CombinedCapacityData response
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 8.5, 10.1_

- [x] 8.1 Write property test for account breakdown completeness
  - **Property 12: Account Breakdown Completeness**
  - **Validates: Requirements 5.1, 5.2, 5.7**

- [x] 8.2 Write property test for empty staging accounts default
  - **Property 13: Empty Staging Accounts Default**
  - **Validates: Requirements 8.5**

- [x] 8.3 Write unit tests for combined capacity query
  - Test query with no staging accounts
  - Test query with multiple staging accounts
  - Test query with one staging account inaccessible
  - Test query with all staging accounts inaccessible
  - _Requirements: 4.1, 9.5_

- [x] 9. Checkpoint - Ensure backend capacity query tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Create API Gateway endpoints
  - [x] 10.1 Add POST /api/staging-accounts/validate endpoint
    - Route to Query Lambda with validate_staging_account operation
    - Define request/response schemas
    - _Requirements: 3.1, 7.3_
  
  - [x] 10.2 Add POST /api/accounts/{targetAccountId}/staging-accounts endpoint
    - Route to Data Management Lambda with add_staging_account operation
    - Define request/response schemas
    - _Requirements: 1.6, 7.1_
  
  - [x] 10.3 Add DELETE /api/accounts/{targetAccountId}/staging-accounts/{stagingAccountId} endpoint
    - Route to Data Management Lambda with remove_staging_account operation
    - Define request/response schemas
    - _Requirements: 2.2, 7.2_
  
  - [x] 10.4 Add GET /api/accounts/{targetAccountId}/capacity endpoint
    - Route to Query Lambda with get_combined_capacity operation
    - Define response schema
    - _Requirements: 4.1, 7.4_

- [x] 10.5 Write property test for CLI operation response structure
  - **Property 14: CLI Operation Response Structure**
  - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**

- [x] 11. Implement frontend TypeScript interfaces and types
  - Create interfaces for CombinedCapacityData, AccountCapacity, RegionalCapacity
  - Create interfaces for StagingAccount, TargetAccount, ValidationResult
  - Create type definitions for status levels and account types
  - _Requirements: 4.3, 5.2, 1.4_

- [x] 12. Implement CapacityDashboard component
  - [x] 12.1 Create CapacityDashboard.tsx component structure
    - Set up component props and state
    - Implement fetchCapacity API call
    - Implement auto-refresh with configurable interval
    - _Requirements: 4.1_
  
  - [x] 12.2 Implement combined capacity display
    - Display total replicating servers, max capacity, percentage used
    - Display status indicator with appropriate color
    - Display progress bar with operational and hard limit markers
    - _Requirements: 4.3, 4.4, 4.5_
  
  - [x] 12.3 Implement per-account capacity breakdown
    - Display table with all accounts (target + staging)
    - Show account ID, name, type, servers, capacity, percentage, status
    - Display regional breakdown for each account
    - _Requirements: 5.1, 5.2, 5.7_
  
  - [x] 12.4 Implement recovery capacity display
    - Display recovery capacity metrics
    - Show status indicator
    - Display progress bar
    - _Requirements: 10.1_
  
  - [x] 12.5 Implement warnings display
    - Display warning alerts with appropriate severity
    - Include actionable guidance in warnings
    - Highlight warnings prominently
    - _Requirements: 6.6_
  
  - [x] 12.6 Write unit tests for CapacityDashboard
    - Test rendering with OK status
    - Test rendering with WARNING status
    - Test rendering with multiple accounts
    - Test rendering with warnings
    - Test auto-refresh functionality
    - _Requirements: 4.1, 4.4, 6.6_

- [x] 13. Implement AddStagingAccountModal component
  - [x] 13.1 Create AddStagingAccountModal.tsx component structure
    - Set up modal props and state
    - Create form fields for account ID, name, role ARN, external ID, region
    - Implement form validation
    - _Requirements: 1.2_
  
  - [x] 13.2 Implement validation flow
    - Call validate API endpoint on "Validate Access" button click
    - Display validation results with status indicators
    - Show validation errors with descriptive messages
    - Enable "Add Account" button only after successful validation
    - _Requirements: 1.3, 1.4, 1.5_
  
  - [x] 13.3 Implement add staging account flow
    - Call add staging account API endpoint
    - Handle success and error responses
    - Close modal and refresh capacity dashboard on success
    - _Requirements: 1.6, 1.7_
  
  - [x] 13.4 Write unit tests for AddStagingAccountModal
    - Test form validation (account ID format, ARN format)
    - Test validation flow with success
    - Test validation flow with errors
    - Test add button disabled until validation succeeds
    - Test add flow with success
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.6_

- [x] 14. Implement TargetAccountSettingsModal component
  - [x] 14.1 Create TargetAccountSettingsModal.tsx component structure
    - Set up modal props and state
    - Display target account details
    - Display list of staging accounts with status and server counts
    - _Requirements: 1.1_
  
  - [x] 14.2 Implement add staging account integration
    - Show AddStagingAccountModal when "Add Staging Account" clicked
    - Handle staging account added callback
    - Update staging accounts list
    - _Requirements: 1.2, 1.6_
  
  - [x] 14.3 Implement remove staging account flow
    - Show confirmation dialog on "Remove" button click
    - Display warning if staging account has active servers
    - Call remove staging account API endpoint
    - Update staging accounts list on success
    - Refresh capacity dashboard
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [x] 14.4 Write unit tests for TargetAccountSettingsModal
    - Test rendering with staging accounts list
    - Test add staging account button opens modal
    - Test remove staging account confirmation
    - Test remove staging account with active servers shows warning
    - _Requirements: 1.1, 2.1, 2.4_

- [x] 15. Implement CapacityDetailsModal component
  - Create CapacityDetailsModal.tsx component structure
  - Display detailed per-account metrics
  - Display regional breakdown tables
  - Display capacity planning recommendations
  - _Requirements: 5.1, 5.7_

- [x] 15.1 Write unit tests for CapacityDetailsModal
  - Test rendering with multiple accounts
  - Test regional breakdown display
  - Test capacity planning recommendations
  - _Requirements: 5.1, 5.7_

- [x] 16. Checkpoint - Ensure frontend component tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 17. Implement API client functions
  - [x] 17.1 Create validateStagingAccount API client function
    - Call POST /api/staging-accounts/validate
    - Handle request/response transformation
    - Handle errors
    - _Requirements: 3.1_
  
  - [x] 17.2 Create addStagingAccount API client function
    - Call POST /api/accounts/{id}/staging-accounts
    - Handle request/response transformation
    - Handle errors
    - _Requirements: 1.6_
  
  - [x] 17.3 Create removeStagingAccount API client function
    - Call DELETE /api/accounts/{id}/staging-accounts/{stagingId}
    - Handle request/response transformation
    - Handle errors
    - _Requirements: 2.2_
  
  - [x] 17.4 Create getCombinedCapacity API client function
    - Call GET /api/accounts/{id}/capacity
    - Handle request/response transformation
    - Handle errors
    - _Requirements: 4.1_

- [x] 18. Wire components together and integrate with existing UI
  - [x] 18.1 Integrate CapacityDashboard into main dashboard page
    - Add CapacityDashboard component to dashboard
    - Pass target account ID prop
    - Configure refresh interval
    - _Requirements: 4.1_
  
  - [x] 18.2 Integrate TargetAccountSettingsModal into target accounts page
    - Add "Settings" button to target accounts table
    - Open TargetAccountSettingsModal on button click
    - Pass target account data
    - _Requirements: 1.1_
  
  - [x] 18.3 Write property test for capacity dashboard refresh after modification
    - **Property 15: Capacity Dashboard Refresh After Modification**
    - **Validates: Requirements 1.7, 2.3**
  
  - [x] 18.4 Write integration tests for complete flows
    - Test add staging account end-to-end flow
    - Test remove staging account end-to-end flow
    - Test capacity query with multiple staging accounts
    - Test validation failure scenarios
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2.1, 2.2, 2.3, 4.1_

- [x] 19. Update CloudFormation templates
  - Add IAM permissions for STS AssumeRole to Lambda execution roles
  - Add IAM permissions for DRS DescribeSourceServers in cross-account scenarios
  - Update Lambda environment variables if needed
  - Update API Gateway resource definitions for new endpoints
  - _Requirements: 3.1, 9.2_

- [x] 20. Create CLI scripts for staging account management
  - [x] 20.1 Create add-staging-account.sh script
    - Accept target account ID, staging account ID, and staging account name as arguments
    - Invoke Data Management Lambda with add_staging_account operation
    - Display success/error message
    - _Requirements: 7.1_
  
  - [x] 20.2 Create remove-staging-account.sh script
    - Accept target account ID and staging account ID as arguments
    - Invoke Data Management Lambda with remove_staging_account operation
    - Display success/error message
    - _Requirements: 7.2_
  
  - [x] 20.3 Create validate-staging-account.sh script
    - Accept staging account details as arguments
    - Invoke Query Lambda with validate_staging_account operation
    - Display validation results
    - _Requirements: 7.3_
  
  - [x] 20.4 Create list-staging-accounts.sh script
    - Accept target account ID as argument
    - Invoke Query Lambda with get_target_account operation
    - Display staging accounts list
    - _Requirements: 7.4_

- [x] 20.5 Write CLI script tests
  - Test add staging account script
  - Test remove staging account script
  - Test validate staging account script
  - Test list staging accounts script
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 21. Final checkpoint - Ensure all tests pass
  - Run complete test suite (unit tests, property tests, integration tests)
  - Verify all 15 correctness properties are tested
  - Ensure code coverage meets goals (80% backend, 75% frontend)
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases
- Backend uses Python with pytest and hypothesis for property-based testing
- Frontend uses TypeScript/React with vitest and fast-check for property-based testing
- All code must follow PEP 8 standards (Python) and be formatted with black and flake8
- CloudScape Design System components used for all UI elements
