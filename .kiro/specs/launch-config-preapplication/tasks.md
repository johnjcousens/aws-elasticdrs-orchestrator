# Implementation Plan: Launch Configuration Pre-Application

## Overview

This implementation plan breaks down the launch configuration pre-application feature into discrete, incremental coding tasks. Each task builds on previous work, with frequent checkpoints to ensure quality and catch issues early.

The implementation follows a phased approach:
1. **Phase 1**: Core service and data models
2. **Phase 2**: Integration with protection group operations
3. **Phase 3**: Wave execution optimization
4. **Phase 4**: API endpoints and testing

## Tasks

- [x] 1. Create launch config service foundation
  - Create `lambda/shared/launch_config_service.py` with core functions
  - Implement configuration hash calculation
  - Implement status persistence and retrieval
  - Add error handling classes
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 1.1 Write unit tests for launch config service
  - Create `tests/unit/test_launch_config_service_unit.py`
  - Test hash calculation function
  - Test status persistence and retrieval
  - Test error handling
  - _Requirements: 5.1_

- [x] 1.2 Write property test for configuration hash consistency
  - **Property 10: Configuration Hash Consistency**
  - **Validates: Requirements 4.4**
  - For any launch configuration, calculating the hash multiple times should produce the same result
  - _Requirements: 5.2_

- [x] 2. Implement configuration application logic
  - Add `apply_launch_configs_to_group()` function
  - Implement per-server configuration application
  - Add timeout handling
  - Implement retry logic with exponential backoff
  - _Requirements: 1.1, 1.2_

- [x] 2.1 Write unit tests for configuration application
  - Test successful configuration application
  - Test timeout handling
  - Test retry logic
  - Test partial success scenarios
  - _Requirements: 5.1_

- [x] 2.2 Write property test for configuration application completeness
  - **Property 1: Configuration Application Completeness**
  - **Validates: Requirements 1.1, 1.2, 1.4**
  - For any protection group with launch configurations, all server configurations should be applied and status persisted
  - _Requirements: 5.2_

- [x] 3. Implement configuration drift detection
  - Add `detect_config_drift()` function
  - Implement hash comparison logic
  - Add drift detection to wave execution check
  - _Requirements: 4.4_

- [x] 3.1 Write unit tests for drift detection
  - Test drift detection with matching hashes
  - Test drift detection with mismatched hashes
  - Test drift detection with missing stored hash
  - _Requirements: 5.1_

- [x] 3.2 Write property test for drift detection
  - **Property 8: Configuration Drift Detection**
  - **Validates: Requirements 4.4**
  - For any wave execution, if current config hash differs from stored hash, configs must be re-applied
  - _Requirements: 5.2_

- [x] 4. Extend DynamoDB schema for protection groups
  - Add `launchConfigStatus` field to protection group model
  - Implement camelCase attribute naming
  - Add validation for status schema
  - Update existing protection group operations to handle new field
  - _Requirements: 1.4, 2.1, 2.2_

- [x] 4.1 Write unit tests for schema extension
  - Test launchConfigStatus field persistence
  - Test camelCase attribute naming
  - Test status schema validation
  - Test backward compatibility (groups without status)
  - _Requirements: 5.1_

- [x] 4.2 Write property test for status schema validity
  - **Property 4: Configuration Status Schema Validity**
  - **Validates: Requirements 2.1, 2.2, 2.3**
  - For any protection group with configuration status, status must be valid and timestamps must be present
  - _Requirements: 5.2_

- [x] 5. Checkpoint - Ensure all tests pass
  - Run all unit tests: `pytest tests/unit/test_launch_config_service_unit.py -v`
  - Run all property tests: `pytest tests/unit/test_launch_config_service_property.py -v`
  - Verify code coverage >90% for new code
  - Ask the user if questions arise

- [x] 6. Integrate with protection group create operation
  - Modify `create_protection_group()` in data-management-handler
  - Add automatic config application after group creation
  - Handle timeout gracefully (allow group creation to succeed)
  - Store configuration status in DynamoDB
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 6.1 Write unit tests for create integration
  - Test successful group creation with config application
  - Test group creation with config application timeout
  - Test group creation with config application failure
  - Test status persistence after creation
  - _Requirements: 5.1_

- [x] 6.2 Write property test for validation before persistence
  - **Property 2: Configuration Validation Before Persistence**
  - **Validates: Requirements 1.3**
  - For any configuration application, validation must occur before persistence
  - _Requirements: 5.2_

- [x] 7. Integrate with protection group update operation
  - Modify `update_protection_group()` in data-management-handler
  - Add selective config re-application logic
  - Re-apply only if servers or configs changed
  - Update configuration status in DynamoDB
  - _Requirements: 1.1, 1.2, 1.4_

- [x] 7.1 Write unit tests for update integration
  - Test update with server changes (re-apply configs)
  - Test update with config changes (re-apply configs)
  - Test update without changes (preserve status)
  - Test update with force flag (always re-apply)
  - _Requirements: 5.1_

- [x] 7.2 Write property test for status update atomicity
  - **Property 9: Status Update Atomicity**
  - **Validates: Requirements 4.5**
  - For any status update, either all fields update together or none update
  - _Requirements: 5.2_

- [x] 8. Add manual re-apply operation
  - Add `apply_launch_configs()` function to data-management-handler
  - Support three invocation methods (Frontend, API, Direct)
  - Implement force re-apply logic
  - Return detailed status with per-server results
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 8.1 Write unit tests for manual re-apply
  - Test re-apply with force=false (skip if ready)
  - Test re-apply with force=true (always re-apply)
  - Test re-apply with failed servers
  - Test all three invocation methods
  - _Requirements: 5.1, 5.6_

- [x] 8.2 Write property test for re-apply completeness
  - **Property 6: Re-apply Operation Completeness**
  - **Validates: Requirements 3.2, 3.3**
  - For any manual re-apply, all servers must be processed and status must reflect outcome
  - _Requirements: 5.2_

- [x] 9. Add get configuration status operation
  - Add `get_launch_config_status()` function to data-management-handler
  - Support three invocation methods (Frontend, API, Direct)
  - Return complete status with per-server details
  - Handle missing status gracefully
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 9.1 Write unit tests for get status operation
  - Test get status for group with ready status
  - Test get status for group with failed status
  - Test get status for group without status
  - Test all three invocation methods
  - _Requirements: 5.1, 5.6_

- [x] 9.2 Write property test for error visibility
  - **Property 5: Error Visibility**
  - **Validates: Requirements 2.4, 3.4**
  - For any failed configuration application, errors must be visible in status
  - _Requirements: 5.2_

- [x] 10. Checkpoint - Ensure all tests pass
  - Run all unit tests: `pytest tests/unit/ -v`
  - Run all property tests with extended iterations: `pytest tests/unit/test_launch_config_service_property.py -v --hypothesis-show-statistics`
  - Verify integration with data-management-handler
  - Fixed: Added `settings` import to `test_launch_config_service_property.py`
  - Fixed: Reset `launch_config_service` module cache in `test_data_management_get_launch_config_status.py`
  - **PENDING USER VERIFICATION**: Please run tests manually to verify fixes work
  - Ask the user if questions arise

- [x] 11. Optimize wave execution with config status check
  - Modify `start_wave_recovery()` in execution-handler
  - Add config status check before starting wave
  - Implement fast path (status=ready, skip config application)
  - Implement fallback path (status not ready, apply configs)
  - _Requirements: 1.5, 4.1, 4.2, 4.3_

- [x] 11.1 Write unit tests for wave execution optimization
  - Test fast path (configs pre-applied)
  - Test fallback path (configs not pre-applied)
  - Test with missing config status
  - Test with failed config status
  - _Requirements: 5.1_

- [x] 11.2 Write property test for wave execution fast path
  - **Property 3: Wave Execution Fast Path**
  - **Validates: Requirements 1.5, 4.1, 4.2**
  - For any wave with status=ready, recovery should start without DRS config API calls
  - _Requirements: 5.2_

- [x] 11.3 Write property test for wave execution fallback path
  - **Property 7: Wave Execution Fallback Path**
  - **Validates: Requirements 4.3**
  - For any wave with status not ready, configs must be applied before recovery
  - _Requirements: 5.2_

- [x] 12. Add configuration drift detection to wave execution
  - Integrate `detect_config_drift()` into wave execution
  - Re-apply configs if drift detected
  - Log drift detection events
  - Update config status after re-application
  - _Requirements: 4.4_

- [x] 12.1 Write unit tests for drift detection in wave execution
  - Test wave execution with no drift
  - Test wave execution with drift detected
  - Test drift detection with hash mismatch
  - Test status update after drift re-application
  - _Requirements: 5.1_

- [x] 13. Add API Gateway routes for new endpoints
  - Add route: `POST /protection-groups/{groupId}/apply-launch-configs`
  - Add route: `GET /protection-groups/{groupId}/launch-config-status`
  - Update API Gateway infrastructure methods stack
  - Configure Cognito authorization
  - _Requirements: 3.1, 2.1_

- [x] 13.1 Write integration tests for API endpoints
  - Test apply-launch-configs endpoint (Frontend invocation)
  - Test apply-launch-configs endpoint (API invocation)
  - Test get-launch-config-status endpoint (Frontend invocation)
  - Test get-launch-config-status endpoint (API invocation)
  - _Requirements: 5.3, 5.6_

- [x] 14. Checkpoint - Ensure all tests pass
  - Run all unit tests: `pytest tests/unit/ -v`
  - Run all property tests: `pytest tests/unit/test_launch_config_service_property.py -v`
  - Run integration tests: `pytest tests/integration/ -v` (if exists)
  - Verify code coverage >90%
  - Ask the user if questions arise

- [x] 15. Write end-to-end integration tests
  - Create `tests/integration/test_launch_config_e2e_integration.py`
  - Test complete protection group creation with config application
  - Test wave execution with pre-applied configs
  - Test configuration drift detection and recovery
  - Test error scenarios and recovery
  - _Requirements: 5.3_

- [x] 15.1 Write property test for status transition validity
  - **Property 11: Status Transition Validity**
  - **Validates: Requirements 1.4, 3.3, 4.5**
  - For any sequence of operations, status transitions must follow valid paths
  - _Requirements: 5.2_

- [x] 15.2 Write property test for configuration round-trip persistence
  - **Property 12: Configuration Round-Trip Persistence**
  - **Validates: Requirements 1.4**
  - For any status persisted to DynamoDB, retrieving immediately should return equivalent status
  - _Requirements: 5.2_

- [x] 16. Write performance tests
  - Create `tests/performance/test_launch_config_performance.py`
  - Measure wave execution time with pre-applied configs
  - Measure wave execution time with runtime config application
  - Measure config application time during group create/update
  - Verify 80% reduction in wave execution time
  - _Requirements: 5.4_

- [x] 17. Update existing tests for new architecture
  - Update `test_data_management_operations_property.py`
  - Update `test_data_management_new_operations.py`
  - Update `test_execution_handler_start_wave.py`
  - Update `test_execution_handler_operations.py`
  - Update `test_query_handler_get_server_launch_config.py`
  - _Requirements: 5.5_

- [x] 18. Final checkpoint - Complete validation
  - Run all tests: `pytest tests/ -v`
  - Run property tests with extended iterations: `pytest tests/unit/test_launch_config_service_property.py -v --hypothesis-show-statistics --hypothesis-seed=random`
  - Verify code coverage >90%
  - Run linting: `flake8 lambda/shared/launch_config_service.py`
  - Run formatting check: `black --check lambda/shared/launch_config_service.py`
  - Ask the user if questions arise

- [-] 19. Deploy to dev environment
  - Commit all changes with Conventional Commits format
  - Push to remote repository
  - Deploy using: `./scripts/deploy.sh dev`
  - Monitor CloudWatch logs for errors
  - Verify DynamoDB schema extension
  - Test new API endpoints manually

- [~] 20. Verify deployment and performance
  - Test protection group creation with config application
  - Test wave execution with pre-applied configs
  - Measure wave execution time (should be 5-10s vs 30-60s)
  - Verify configuration status in DynamoDB
  - Check CloudWatch metrics for errors
  - Validate 80% performance improvement

## Notes

- All tasks are required and can be completed today
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation and early error detection
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- Performance tests validate optimization claims
- All code must follow PEP 8 standards and project coding conventions
- All commits must use Conventional Commits format with `launch-config` scope
- Commit and push frequently (after each logical unit of work)
