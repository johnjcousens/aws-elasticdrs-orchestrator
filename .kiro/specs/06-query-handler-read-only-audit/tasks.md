# Query Handler Read-Only Audit - Tasks

## Overview
Refactor query-handler to be strictly read-only by moving sync operations to appropriate handlers (data-management-handler and execution-handler) while leveraging existing shared utilities in `lambda/shared/`.

## Task List

### Phase 1: Verify Existing Shared Utilities

**NOTE**: The codebase already has 18 comprehensive shared utility modules in `lambda/shared/`. This phase verifies they work correctly before moving sync operations.

- [ ] 1. Verify existing shared utilities (Validates: Requirements FR1, FR5)
  - [ ] 1.1 Verify `lambda/shared/drs_utils.py` functions work correctly - Read module and test normalize_drs_response(), batch_describe_ec2_instances(), enrich_server_data()
  - [ ] 1.2 Verify `lambda/shared/cross_account.py` functions work correctly - Test create_drs_client(), create_ec2_client(), get_cross_account_session()
  - [ ] 1.3 Verify `lambda/shared/account_utils.py` functions work correctly - Test validate_account_id(), get_target_accounts(), validate_target_account()
  - [ ] 1.4 Verify `lambda/shared/security_utils.py` functions work correctly - Test sanitize_string(), validate_drs_server_id(), sanitize_dynamodb_input()
  - [ ] 1.5 Verify `lambda/shared/iam_utils.py` functions work correctly - Test extract_principal_from_context(), validate_authorized_role()
  - [ ] 1.6 Verify `lambda/shared/rbac_middleware.py` functions work correctly - Test permission decorators and role validation

### Phase 2: Move Sync Operations

- [ ] 2. Move source server inventory sync to data-management-handler (Implements: Requirements FR2)
  - [ ] 2.1 Copy `handle_sync_source_server_inventory()` from query-handler (lines 5631-6100) to data-management-handler with existing imports
  - [ ] 2.2 Maintain existing imports from `lambda/shared/` - Verify drs_utils, cross_account, account_utils imports work in new location
  - [ ] 2.3 Test inventory sync via direct Lambda invocation - Create test event and invoke data-management-handler directly
  - [ ] 2.4 Update EventBridge rule in `cfn/nested-stacks/eventbridge-rules.yaml` - Change target from query-handler to data-management-handler
  - [ ] 2.5 Deploy CloudFormation stack update using `./scripts/deploy.sh dev`
  - [ ] 2.6 Test inventory sync via EventBridge trigger - Wait for scheduled execution or trigger manually
  - [ ] 2.7 Verify inventory table updates - Query DynamoDB table to confirm batch writes succeeded
  - [ ] 2.8 Verify region status table updates - Query DynamoDB table to confirm region status writes succeeded

- [ ] 3. Move staging account sync to data-management-handler (Implements: Requirements FR3)
  - [ ] 3.1 Copy `handle_sync_staging_accounts()` from query-handler (lines 5417-5630) to data-management-handler
  - [ ] 3.2 Copy `auto_extend_staging_servers()` helper function to data-management-handler or shared utility
  - [ ] 3.3 Maintain existing imports from `lambda/shared/` - Verify staging_account_models, drs_utils, cross_account imports work
  - [ ] 3.4 Test staging sync via direct Lambda invocation - Create test event and invoke data-management-handler directly
  - [ ] 3.5 Update EventBridge rule in `cfn/nested-stacks/eventbridge-rules.yaml` - Change target from query-handler to data-management-handler
  - [ ] 3.6 Deploy CloudFormation stack update using `./scripts/deploy.sh dev`
  - [ ] 3.7 Test staging sync via EventBridge trigger - Wait for scheduled execution or trigger manually
  - [ ] 3.8 Verify DRS server extension operations - Check DRS console for extended servers in target accounts

- [ ] 4. Split wave status polling (read vs write) (Implements: Requirements FR4)
  - [ ] 4.1 Create `update_wave_completion_status()` in execution-handler - Implement DynamoDB update logic for wave completion
  - [ ] 4.2 Test wave completion update via direct Lambda invocation - Create test event with execution data and invoke execution-handler
  - [ ] 4.3 Refactor `poll_wave_status()` in query-handler to remove DynamoDB writes - Keep DRS job queries, remove update_item() calls
  - [ ] 4.4 Test refactored `poll_wave_status()` returns correct data - Verify job status and server launch progress returned without writes
  - [ ] 4.5 Update Step Functions state machine in `cfn/nested-stacks/step-functions.yaml` - Add UpdateWaveStatus state
  - [ ] 4.6 Add `UpdateWaveStatus` state after `WavePoll` state - Configure to invoke execution-handler with wave data
  - [ ] 4.7 Deploy CloudFormation stack update using `./scripts/deploy.sh dev`
  - [ ] 4.8 Test wave polling with DynamoDB updates - Start recovery execution and monitor Step Functions
  - [ ] 4.9 Verify execution history table updates - Query DynamoDB to confirm wave completion status persisted
  - [ ] 4.10 Verify no data loss during wave transitions - Compare execution data before and after refactoring

### Phase 3: Cleanup and Verification

- [ ] 5. Remove sync operations from query-handler (Implements: Requirements FR2.4, FR3.5)
  - [ ] 5.1 Remove `handle_sync_source_server_inventory()` from query-handler - Delete function and unused imports
  - [ ] 5.2 Remove `handle_sync_staging_accounts()` from query-handler - Delete function and unused imports
  - [ ] 5.3 Remove `auto_extend_staging_servers()` from query-handler if moved to shared utility
  - [ ] 5.4 Verify `poll_wave_status()` has no DynamoDB writes - Search for update_item(), put_item(), delete_item() calls
  - [ ] 5.5 Deploy query-handler cleanup using `./scripts/deploy.sh dev --lambda-only`

- [ ] 6. Verify query-handler is read-only (Validates: User Story 1 Acceptance Criteria)
  - [ ] 6.1 Audit query-handler for any remaining DynamoDB writes - Search for batch_writer(), update_item(), put_item(), delete_item()
  - [ ] 6.2 Audit query-handler for any remaining DRS API writes - Search for extend_source_server(), start_recovery(), terminate_recovery_instances()
  - [ ] 6.3 Verify all read operations still work - Test list_executions, poll_wave_status, get_server_status via API
  - [ ] 6.4 Run unit tests for query-handler using `pytest tests/unit/test_query_handler*.py`
  - [ ] 6.5 Run integration tests for query-handler using `pytest tests/integration/test_query_handler*.py`

- [ ] 7. Verify all sync operations work (Validates: Success Criteria)
  - [ ] 7.1 Test inventory sync end-to-end - Trigger EventBridge rule and verify inventory table updates
  - [ ] 7.2 Test staging account sync end-to-end - Trigger EventBridge rule and verify DRS server extensions
  - [ ] 7.3 Test wave polling end-to-end - Start recovery execution and verify wave completion updates
  - [ ] 7.4 Verify no data loss - Compare execution history before and after refactoring
  - [ ] 7.5 Verify no performance degradation - Compare Lambda execution times before and after

- [ ] 8. Monitor Lambda sizes (Validates: Requirements FR5, Success Criteria)
  - [ ] 8.1 Measure query-handler deployment package size using `aws lambda get-function --function-name hrp-drs-tech-adapter-query-handler-dev`
  - [ ] 8.2 Measure data-management-handler deployment package size using `aws lambda get-function --function-name hrp-drs-tech-adapter-data-management-handler-dev`
  - [ ] 8.3 Measure execution-handler deployment package size using `aws lambda get-function --function-name hrp-drs-tech-adapter-execution-handler-dev`
  - [ ] 8.4 Verify all handlers < 200 MB uncompressed - Check CodeSize field in get-function response
  - [ ] 8.5 Document final handler sizes in requirements.md Open Questions section

### Phase 4: Dual Invocation Mode and Security Testing

- [ ] 9. Integrate iam_utils for IAM principal extraction (Implements: User Story 6 Acceptance Criteria)
  - [ ] 9.1 Add IAM principal extraction to query-handler lambda_handler() - Check for requestContext to distinguish invocation modes
  - [ ] 9.2 Use `iam_utils.extract_principal_from_context()` to extract IAM ARN from Lambda context
  - [ ] 9.3 Distinguish between API Gateway (Cognito) and Direct Lambda (IAM) invocations - Set invocation_mode field
  - [ ] 9.4 Test IAM principal extraction for Step Functions invocations - Invoke from Step Functions and verify AssumedRole extraction
  - [ ] 9.5 Test IAM principal extraction for EventBridge invocations - Trigger EventBridge rule and verify Service principal extraction
  - [ ] 9.6 Verify principal_type, principal_arn, session_name fields populated correctly in audit logs

- [ ] 10. Implement parameter masking for sensitive data (Implements: User Story 6 Acceptance Criteria)
  - [ ] 10.1 Add parameter masking function using `iam_utils.mask_sensitive_parameters()` in audit logging code
  - [ ] 10.2 Define sensitive parameter patterns (password, api_key, secret, token, credential) in masking function
  - [ ] 10.3 Mask sensitive parameters before writing to audit logs - Call masking function on event parameters
  - [ ] 10.4 Test parameter masking with various sensitive parameter names - Create test events with password, api_key fields
  - [ ] 10.5 Verify masked parameters show "***MASKED***" in audit logs - Query audit log table and check masked values

- [ ] 11. Add tests for dual invocation modes (Validates: User Story 6 Acceptance Criteria)
  - [ ] 11.1 Write unit test for API Gateway invocation (Cognito JWT) in `tests/unit/test_query_handler_invocation_modes.py`
  - [ ] 11.2 Write unit test for Direct Lambda invocation (IAM role) in `tests/unit/test_query_handler_invocation_modes.py`
  - [ ] 11.3 Write unit test for Step Functions invocation (AssumedRole) in `tests/unit/test_query_handler_invocation_modes.py`
  - [ ] 11.4 Write unit test for EventBridge invocation (Service principal) in `tests/unit/test_query_handler_invocation_modes.py`
  - [ ] 11.5 Verify audit logs capture correct invocation_mode field (API_GATEWAY vs DIRECT_LAMBDA)
  - [ ] 11.6 Verify audit logs capture correct principal information for each mode (email vs IAM ARN)

- [ ] 12. Add tests for audit log failure scenarios (Validates: Design error handling requirements)
  - [ ] 12.1 Write unit test for DynamoDB throttling during audit log write in `tests/unit/test_audit_logging_failures.py`
  - [ ] 12.2 Write unit test for DynamoDB unavailable during audit log write in `tests/unit/test_audit_logging_failures.py`
  - [ ] 12.3 Write unit test for parameter masking failure in `tests/unit/test_audit_logging_failures.py`
  - [ ] 12.4 Write unit test for IAM principal extraction failure in `tests/unit/test_audit_logging_failures.py`
  - [ ] 12.5 Verify retry logic with exponential backoff works correctly - Mock DynamoDB throttling and verify retries
  - [ ] 12.6 Verify CloudWatch Logs fallback works when DynamoDB writes fail - Check CloudWatch Logs for audit entries

- [ ] 13. Add tests for IAM principal extraction (Validates: Design IAM principal extraction patterns)
  - [ ] 13.1 Write unit test for AssumedRole principal extraction in `tests/unit/test_iam_principal_extraction.py`
  - [ ] 13.2 Write unit test for IAM User principal extraction in `tests/unit/test_iam_principal_extraction.py`
  - [ ] 13.3 Write unit test for AWS Service principal extraction in `tests/unit/test_iam_principal_extraction.py`
  - [ ] 13.4 Write unit test for authorized role pattern validation in `tests/unit/test_iam_principal_extraction.py`
  - [ ] 13.5 Verify principal_arn, session_name, account_id extracted correctly from Lambda context
  - [ ] 13.6 Verify unauthorized roles are rejected (403 Forbidden) - Test with non-matching role pattern

- [ ] 14. Add tests for RBAC permission enforcement (Implements: User Story 7 Acceptance Criteria)
  - [ ] 14.1 Write unit test for Admin role permissions (all operations) in `tests/unit/test_rbac_permissions.py`
  - [ ] 14.2 Write unit test for Operator role permissions (operational data) in `tests/unit/test_rbac_permissions.py`
  - [ ] 14.3 Write unit test for Viewer role permissions (read-only operational data) in `tests/unit/test_rbac_permissions.py`
  - [ ] 14.4 Write unit test for Auditor role permissions (audit logs + operational data) in `tests/unit/test_rbac_permissions.py`
  - [ ] 14.5 Write unit test for Planner role permissions (recovery plans) in `tests/unit/test_rbac_permissions.py`
  - [ ] 14.6 Verify Auditor can access audit logs, Viewer cannot - Test audit log query with different roles
  - [ ] 14.7 Verify permission-to-operation mapping enforced correctly - Test each operation with appropriate role
  - [ ] 14.8 Verify unauthorized operations return 403 Forbidden - Test operations with insufficient permissions

- [ ] 15. Add tests for cross-account audit logging (Validates: Design cross-account audit logging patterns)
  - [ ] 15.1 Write unit test for cross-account DRS query with audit logging in `tests/unit/test_cross_account_audit.py`
  - [ ] 15.2 Write unit test for hub-and-spoke audit trail in `tests/unit/test_cross_account_audit.py`
  - [ ] 15.3 Verify source_account and target_account fields populated correctly in audit logs
  - [ ] 15.4 Verify assumed_role_arn and cross_account_session fields populated in audit logs
  - [ ] 15.5 Test audit log aggregation queries (by target account, by user) - Query audit table with filters
  - [ ] 15.6 Verify centralized audit trail in hub account DynamoDB table - Check hub account audit table

### Phase 5: Documentation and Final Testing

- [ ] 16. Update documentation (Validates: NFR3 Code Maintainability)
  - [ ] 16.1 Update handler responsibility documentation in `docs/architecture/HANDLER_RESPONSIBILITIES.md`
  - [ ] 16.2 Document dual invocation mode architecture in `docs/architecture/DUAL_INVOCATION_MODE.md`
  - [ ] 16.3 Document IAM principal extraction patterns in `docs/security/IAM_PRINCIPAL_EXTRACTION.md`
  - [ ] 16.4 Document RBAC integration and permission mapping in `docs/security/RBAC_PERMISSIONS.md`
  - [ ] 16.5 Document audit log schema with IAM principal fields in `docs/security/AUDIT_LOG_SCHEMA.md`
  - [ ] 16.6 Document parameter masking for sensitive data in `docs/security/PARAMETER_MASKING.md`
  - [ ] 16.7 Document error handling for audit logging failures in `docs/security/AUDIT_ERROR_HANDLING.md`
  - [ ] 16.8 Document cross-account audit logging patterns in `docs/security/CROSS_ACCOUNT_AUDIT.md`
  - [ ] 16.9 Update deployment guide in `docs/guides/DEPLOYMENT_GUIDE.md` with new handler responsibilities
  - [ ] 16.10 Update architecture diagrams in `docs/architecture/DIAGRAMS.md` with refactored handler flow

- [ ] 17. Write comprehensive integration tests (Validates: Success Criteria)
  - [ ] 17.1 Write EventBridge sync operation tests in `tests/integration/test_eventbridge_sync.py`
  - [ ] 17.2 Write Step Functions wave polling tests in `tests/integration/test_step_functions_wave_polling.py`
  - [ ] 17.3 Write end-to-end recovery plan tests in `tests/integration/test_recovery_plan_e2e.py`
  - [ ] 17.4 Write cross-account operation tests with audit logging in `tests/integration/test_cross_account_audit_e2e.py`
  - [ ] 17.5 Write RBAC enforcement tests across all operations in `tests/integration/test_rbac_enforcement_e2e.py`
  - [ ] 17.6 Verify test coverage meets requirements using `pytest --cov=lambda --cov-report=term`

## Success Criteria

- ✅ Zero DynamoDB writes in query-handler
- ✅ Zero DRS API writes in query-handler
- ✅ All sync operations work after migration
- ✅ No data loss during wave transitions
- ✅ All tests pass
- ✅ All Lambda functions < 15,000 lines
- ✅ All deployment packages < 200 MB uncompressed
- ✅ CloudFormation template < 800 KB

## Notes

- **Existing Shared Utilities**: The codebase already has 18 comprehensive shared utility modules in `lambda/shared/` - no extraction phase needed
- **Leverage Existing Patterns**: All sync operations already use existing shared utilities - maintain imports during refactoring
- **Deploy new operations before removing old ones** (zero downtime)
- **Test each operation after moving**
- **Monitor CloudFormation stack status during deployments**
- **Keep rollback plan ready in case of issues**
- **Dual Invocation Modes**: Query-handler supports both API Gateway (Cognito) and Direct Lambda (IAM) invocations
- **IAM Principal Extraction**: Use `iam_utils.extract_principal_from_context()` for direct Lambda invocations
- **RBAC Integration**: All query operations enforce role-based permissions using `rbac_middleware.py`
- **Parameter Masking**: Sensitive parameters (password, api_key, secret, token) masked in audit logs
- **Audit Log Failures**: Synchronous audit logging with retry and CloudWatch Logs fallback
- **Cross-Account Audit Trail**: Hub-and-spoke pattern with centralized audit logs in hub account
- **Security First**: Input validation using `security_utils.py` before audit logging
- **Compliance Requirements**: Audit logs encrypted at rest (KMS), point-in-time recovery enabled
