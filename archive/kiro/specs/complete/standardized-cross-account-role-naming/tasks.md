analyze# Implementation Plan: Standardized Cross-Account Role Naming

## Overview

This implementation plan breaks down the standardized cross-account role naming feature into discrete, incremental coding tasks. Each task builds on previous steps and includes validation through code execution. The plan follows a bottom-up approach: shared utilities → Lambda functions → CloudFormation templates → integration.

## Tasks

- [x] 1. Create shared account utilities module
  - [x] 1.1 Create `lambda/shared/account_utils.py` with core utility functions
  - [x] 1.2 Implement `STANDARD_ROLE_NAME` constant
  - [x] 1.3 Implement `construct_role_arn(account_id: str) -> str` function
  - [x] 1.4 Implement `validate_account_id(account_id: str) -> bool` function
  - [x] 1.5 Implement `extract_account_id_from_arn(role_arn: str) -> Optional[str]` function
  - [x] 1.6 Implement `get_role_arn(account_id: str, explicit_arn: Optional[str]) -> str` function
  - [x] 1.7 Add comprehensive docstrings for all functions

- [x] 2. Write property tests for account utilities
  - [x] 2.1 Write property test for ARN construction pattern (Property 1)
  - [x] 2.2 Write property test for account ID extraction inverse (Property 7)
  - [x] 2.3 Configure hypothesis with 100+ iterations
  - [x] 2.4 Test with randomly generated 12-digit account IDs

- [x] 3. Write unit tests for account utilities
  - [x] 3.1 Test `construct_role_arn()` with valid account IDs
  - [x] 3.2 Test `construct_role_arn()` with invalid account IDs (too short, too long, non-numeric)
  - [x] 3.3 Test `validate_account_id()` with edge cases
  - [x] 3.4 Test `extract_account_id_from_arn()` with valid and invalid ARNs
  - [x] 3.5 Test `get_role_arn()` with and without explicit ARN

- [x] 4. Update data management handler for target accounts
  - [x] 4.1 Import account utilities in `lambda/data-management-handler/index.py`
  - [x] 4.2 Update `handle_add_target_account()` to make `roleArn` optional
  - [x] 4.3 Add logic to construct ARN when not provided
  - [x] 4.4 Add logging for constructed vs provided ARN
  - [x] 4.5 Ensure constructed ARN is stored in DynamoDB
  - [x] 4.6 Ensure API response includes roleArn field

- [x] 5. Write property tests for target account addition
  - [x] 5.1 Write property test for explicit ARN precedence (Property 2)
  - [x] 5.2 Write property test for account addition round-trip (Property 3)
  - [x] 5.3 Write property test for API response includes role ARN (Property 4)
  - [x] 5.4 Write property test for optional roleArn field acceptance (Property 5)
  - [x] 5.5 Test with randomly generated account data (with and without roleArn)

- [x] 6. Write unit tests for target account addition
  - [x] 6.1 Test adding account without roleArn (constructs ARN)
  - [x] 6.2 Test adding account with explicit roleArn (uses provided ARN)
  - [x] 6.3 Test API response includes roleArn field
  - [x] 6.4 Test DynamoDB storage of constructed ARN
  - [x] 6.5 Test error handling for invalid account IDs

- [x] 7. Update data management handler for staging accounts
  - [x] 7.1 Update `handle_add_staging_account()` to make `roleArn` optional
  - [x] 7.2 Add logic to construct ARN when not provided
  - [x] 7.3 Add logging for constructed vs provided ARN
  - [x] 7.4 Ensure constructed ARN is stored in DynamoDB
  - [x] 7.5 Ensure API response includes roleArn field

- [x] 8. Write property tests for staging account addition
  - [x] 8.1 Write property test for explicit ARN precedence (Property 2 - staging)
  - [x] 8.2 Write property test for account addition round-trip (Property 3 - staging)
  - [x] 8.3 Write property test for API response includes role ARN (Property 4 - staging)
  - [x] 8.4 Write property test for optional roleArn field acceptance (Property 5 - staging)
  - [x] 8.5 Test with randomly generated staging account data

- [x] 9. Write unit tests for staging account addition
  - [x] 9.1 Test adding staging account without roleArn
  - [x] 9.2 Test adding staging account with explicit roleArn
  - [x] 9.3 Test API response includes roleArn field
  - [x] 9.4 Test DynamoDB storage of constructed ARN
  - [x] 9.5 Test error handling for invalid account IDs

- [x] 10. Update query handler for cross-account operations
  - [x] 10.1 Import account utilities in `lambda/query-handler/index.py`
  - [x] 10.2 Update `query_target_account_capacity()` to construct ARN if not present
  - [x] 10.3 Add fallback logic for ARN construction
  - [x] 10.4 Add logging for constructed ARN usage
  - [x] 10.5 Ensure all cross-account queries use roleArn

- [x] 11. Write unit tests for query handler
  - [x] 11.1 Test capacity query with account that has explicit roleArn
  - [x] 11.2 Test capacity query with account that needs constructed roleArn
  - [x] 11.3 Test error handling for missing accounts
  - [x] 11.4 Mock DRS API calls for testing

- [x] 12. Update orchestration step functions handler
  - [x] 12.1 Import account utilities in `lambda/orchestration-stepfunctions/index.py`
  - [x] 12.2 Update `assume_target_account_role()` to construct ARN if not present
  - [x] 12.3 Add fallback logic for ARN construction
  - [x] 12.4 Add logging for constructed ARN usage
  - [x] 12.5 Ensure all cross-account operations use roleArn

- [x] 13. Write unit tests for orchestration handler
  - [x] 13.1 Test role assumption with explicit roleArn
  - [x] 13.2 Test role assumption with constructed roleArn
  - [x] 13.3 Test error handling for role assumption failures
  - [x] 13.4 Mock STS AssumeRole calls for testing

- [x] 14. Checkpoint - Ensure all Lambda tests pass
  - [x] 14.1 Run all unit tests: `pytest tests/unit/ -v`
  - [x] 14.2 Run all property tests: `pytest tests/property/ -v --hypothesis-show-statistics`
  - [x] 14.3 Verify test coverage >90%
  - [x] 14.4 Fix any failing tests before proceeding

- [x] 15. Update cross-account role CloudFormation template
  - [x] 15.1 Edit `cfn/cross-account-role-stack.yaml`
  - [x] 15.2 Remove `Environment` parameter from Parameters section
  - [x] 15.3 Change `RoleName` to hardcoded `DRSOrchestrationRole`
  - [x] 15.4 Update role Description to indicate standardized naming
  - [x] 15.5 Verify Outputs section includes RoleArn
  - [x] 15.6 Keep all IAM permissions unchanged

- [x] 16. Validate cross-account role template
  - [x] 16.1 Run cfn-lint: `cfn-lint cfn/cross-account-role-stack.yaml`
  - [x] 16.2 Run cfn_nag: `cfn_nag_scan --input-path cfn/cross-account-role-stack.yaml`
  - [x] 16.3 Verify no Environment parameter exists
  - [x] 16.4 Verify hardcoded role name
  - [x] 16.5 Validate template syntax with AWS CLI

- [x] 17. Update master CloudFormation template
  - [x] 17.1 Edit `cfn/master-template.yaml`
  - [x] 17.2 Update OrchestrationRole's AssumeRole policy Resource pattern
  - [x] 17.3 Add comment documenting standardized role name pattern
  - [x] 17.4 Update template description to reference standardized naming

- [x] 18. Validate master template
  - [x] 18.1 Run cfn-lint: `cfn-lint cfn/master-template.yaml`
  - [x] 18.2 Run cfn_nag: `cfn_nag_scan --input-path cfn/master-template.yaml`
  - [x] 18.3 Verify AssumeRole resource pattern
  - [x] 18.4 Validate template syntax with AWS CLI

- [x] 19. Update API documentation
  - [x] 19.1 Mark `roleArn` as optional for target accounts
  - [x] 19.2 Mark `roleArn` as optional for staging accounts
  - [x] 19.3 Add examples showing requests without roleArn
  - [x] 19.4 Document ARN construction pattern
  - [x] 19.5 Add note about backward compatibility

- [x] 20. Update deployment guides
  - [x] 20.1 Update `docs/guides/DRS_CROSS_ACCOUNT_SETUP_VERIFICATION.md`
  - [x] 20.2 Update `docs/reference/DRS_CROSS_ACCOUNT_REFERENCE.md`
  - [x] 20.3 Update `README.md` deployment instructions
  - [x] 20.4 Add migration guide for existing deployments
  - [x] 20.5 Document backward compatibility for existing accounts

- [x] 21. Integration testing - Target account without roleArn
  - [x] 21.1 Deploy cross-account role stack in test account
  - [x] 21.2 Add target account via API without roleArn
  - [x] 21.3 Verify account is added successfully
  - [x] 21.4 Verify roleArn is constructed and stored
  - [x] 21.5 Verify API response includes roleArn

- [x] 22. Integration testing - Staging account without roleArn
  - [x] 22.1 Add staging account via API without roleArn
  - [x] 22.2 Verify account is added successfully
  - [x] 22.3 Verify roleArn is constructed and stored
  - [x] 22.4 Verify API response includes roleArn

- [x] 23. Integration testing - Cross-account operations
  - [x] 23.1 Query DRS capacity in target account
  - [x] 23.2 Verify role assumption works with constructed ARN
  - [x] 23.3 Verify DRS API calls succeed

- [x] 24. Integration testing - Backward compatibility
  - [x] 24.1 Add account with explicit roleArn
  - [x] 24.2 Verify explicit ARN is used (not constructed)
  - [x] 24.3 Verify all operations work with explicit ARN
  - [x] 24.4 Update account and verify roleArn is not overwritten

- [x] 25. Integration testing - Validation with both ARN formats
  - [x] 25.1 Test validation with standardized ARN
  - [x] 25.2 Test validation with custom ARN
  - [x] 25.3 Verify both formats are accepted

- [x] 26. Final checkpoint - Ensure all tests pass
  - [x] 26.1 Run all unit tests: `pytest tests/unit/ -v`
  - [x] 26.2 Run all property tests: `pytest tests/property/ -v`
  - [x] 26.3 Run all integration tests: `pytest tests/integration/ -v`
  - [x] 26.4 Validate all CloudFormation templates: `cfn-lint cfn/*.yaml`
  - [x] 26.5 Run security scans: `cfn_nag_scan --input-path cfn/`
  - [x] 26.6 Verify test coverage report: `pytest --cov=lambda --cov-report=term`

## Notes

- All tasks are required for complete implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (minimum 100 iterations)
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- CloudFormation validation ensures template correctness
- Documentation updates ensure clarity for users

## Implementation Order Rationale

1. **Shared utilities first** - Foundation for all other components
2. **Lambda functions next** - Core business logic
3. **CloudFormation templates** - Infrastructure changes
4. **Documentation** - User-facing updates
5. **Integration testing** - End-to-end validation

This order ensures each component can be tested independently before integration.

