# Standardized Cross-Account Role Naming

## Overview

Simplify cross-account role management by standardizing the role name across all target and staging accounts. This eliminates the need to manually specify role ARNs when adding accounts - the system will automatically construct the ARN based on the account ID and a hardcoded role name.

## Problem Statement

Currently, when adding target or staging accounts, users must:
1. Deploy the cross-account role stack in each account
2. Manually copy the role ARN from CloudFormation outputs
3. Paste the ARN when adding the account via API

This creates friction and potential for errors. The role name varies by environment (`DRSOrchestrationRole-dev`, `DRSOrchestrationRole-test`, etc.), making it difficult to predict the ARN.

## Proposed Solution

**Standardize the role name to a single, predictable value across all accounts:**
- Role name: `DRSOrchestrationRole` (no environment suffix)
- ARN pattern: `arn:aws:iam::{account-id}:role/DRSOrchestrationRole`

When adding an account, users only need to provide:
- Account ID (12 digits)
- Account name (human-readable)
- External ID (for security)

The system automatically constructs the role ARN: `arn:aws:iam::{account-id}:role/DRSOrchestrationRole`

## User Stories

### 1. As a DR administrator, I want to add a target account without manually specifying the role ARN

**Acceptance Criteria:**
- 1.1: When adding a target account via API, the `roleArn` field is optional
- 1.2: If `roleArn` is not provided, the system constructs it as `arn:aws:iam::{accountId}:role/DRSOrchestrationRole`
- 1.3: If `roleArn` is provided explicitly, the system uses the provided value (backward compatibility)
- 1.4: The constructed ARN is stored in DynamoDB for future use
- 1.5: API response includes the role ARN (whether constructed or provided)

### 2. As a DR administrator, I want to add a staging account without manually specifying the role ARN

**Acceptance Criteria:**
- 2.1: When adding a staging account via API, the `roleArn` field is optional
- 2.2: If `roleArn` is not provided, the system constructs it as `arn:aws:iam::{accountId}:role/DRSOrchestrationRole`
- 2.3: If `roleArn` is provided explicitly, the system uses the provided value (backward compatibility)
- 2.4: The constructed ARN is stored in DynamoDB for future use
- 2.5: API response includes the role ARN (whether constructed or provided)

### 3. As a DevOps engineer, I want to deploy the cross-account role with a predictable name

**Acceptance Criteria:**
- 3.1: The `cfn/cross-account-role-stack.yaml` template creates a role named `DRSOrchestrationRole` (no environment suffix)
- 3.2: The role name is hardcoded in the template (not parameterized)
- 3.3: The template can be deployed in any account without parameter changes
- 3.4: CloudFormation outputs include the role ARN for reference
- 3.5: The role has all necessary permissions for DRS operations

### 4. As a developer, I want the master template to expect the standardized role name

**Acceptance Criteria:**
- 4.1: The `cfn/master-template.yaml` documentation references the standardized role name
- 4.2: Cross-account operations assume the role using the pattern `arn:aws:iam::{account-id}:role/DRSOrchestrationRole`
- 4.3: The STS AssumeRole policy in the orchestration role allows assuming `DRSOrchestrationRole` in any account
- 4.4: Documentation is updated to reflect the new naming convention

### 5. As a DR administrator, I want existing accounts with custom role names to continue working

**Acceptance Criteria:**
- 5.1: Accounts with explicitly specified `roleArn` values continue to work without changes
- 5.2: The system does not overwrite existing `roleArn` values during updates
- 5.3: Validation logic accepts both standardized and custom role ARNs
- 5.4: Migration path is documented for moving from custom to standardized role names

## Technical Requirements

### CloudFormation Changes

**File: `cfn/cross-account-role-stack.yaml`**
- Remove `Environment` parameter (no longer needed for role naming)
- Hardcode role name to `DRSOrchestrationRole`
- Update role description to indicate standardized naming
- Keep all existing permissions unchanged
- Update outputs to reflect new role name

**File: `cfn/master-template.yaml`**
- Update documentation to reference standardized role name
- Update STS AssumeRole resource pattern to `arn:aws:iam::*:role/DRSOrchestrationRole`
- Add comments explaining the standardized naming convention

### Lambda Changes

**File: `lambda/data-management-handler/index.py`**
- Update `handle_add_target_account()` to construct role ARN if not provided
- Update `handle_update_target_account()` to construct role ARN if not provided
- Update `handle_add_staging_account()` to construct role ARN if not provided
- Add helper function `construct_role_arn(account_id: str) -> str`
- Maintain backward compatibility with explicitly provided role ARNs

**File: `lambda/query-handler/index.py`**
- Update capacity query logic to construct role ARN if not present in DynamoDB
- Update validation logic to construct role ARN if not provided
- Ensure all cross-account operations use the role ARN (constructed or stored)

**File: `lambda/orchestration-stepfunctions/index.py`**
- Update cross-account role assumption to use standardized role name
- Add fallback logic for accounts with custom role names

### Shared Utilities

**File: `lambda/shared/account_utils.py`** (new or existing)
- Add `construct_role_arn(account_id: str) -> str` function
- Add `STANDARD_ROLE_NAME = "DRSOrchestrationRole"` constant
- Add validation for account ID format (12 digits)

### Data Model Changes

**DynamoDB Schema:**
- `roleArn` field remains optional in both target accounts and staging accounts
- If `roleArn` is not present, construct it on-the-fly using the account ID
- Store the constructed ARN in DynamoDB for consistency

## Non-Functional Requirements

### Backward Compatibility
- Existing accounts with custom role ARNs must continue to work
- API accepts both explicit `roleArn` and auto-constructed ARN
- No breaking changes to existing API contracts

### Security
- External ID remains required for all cross-account role assumptions
- Role permissions remain unchanged
- STS AssumeRole policy restricts to specific role name pattern

### Performance
- ARN construction is a simple string operation (negligible overhead)
- No additional API calls required

### Documentation
- Update deployment guides to reference standardized role name
- Provide migration guide for existing deployments
- Update API documentation to indicate `roleArn` is optional

## Success Criteria

1. Users can add target accounts without specifying role ARN
2. Users can add staging accounts without specifying role ARN
3. Cross-account role stack deploys with predictable role name
4. All existing accounts continue to work without changes
5. Documentation is updated and clear
6. All tests pass (unit, integration, property-based)

## Out of Scope

- Automatic migration of existing accounts to standardized role names
- Changing the role name for the orchestration account's own role
- Modifying role permissions or policies
- Changes to external ID generation logic

## Dependencies

- CloudFormation templates (`cfn/cross-account-role-stack.yaml`, `cfn/master-template.yaml`)
- Lambda functions (`data-management-handler`, `query-handler`, `orchestration-stepfunctions`)
- DynamoDB tables (target accounts, staging accounts)
- Existing cross-account role deployments

## Risks and Mitigations

### Risk: Breaking existing deployments
**Mitigation:** Maintain backward compatibility by accepting explicit role ARNs

### Risk: Role name conflicts in accounts with existing roles
**Mitigation:** Document the standardized name clearly; provide migration guide

### Risk: Confusion about which role name to use
**Mitigation:** Clear documentation; CloudFormation template enforces standardized name

## Testing Strategy

### Unit Tests
- Test ARN construction logic with valid account IDs
- Test ARN construction with invalid account IDs
- Test backward compatibility with explicit role ARNs
- Test DynamoDB storage of constructed ARNs

### Integration Tests
- Test adding target account without role ARN
- Test adding staging account without role ARN
- Test cross-account operations with constructed ARN
- Test validation with constructed ARN

### Property-Based Tests
- Property: Constructed ARN always follows pattern `arn:aws:iam::{12-digit-id}:role/DRSOrchestrationRole`
- Property: Account ID extraction from ARN is inverse of ARN construction
- Property: Explicit role ARN always takes precedence over constructed ARN

## Migration Guide

For existing deployments:

1. **New accounts:** Deploy cross-account role stack with standardized name
2. **Existing accounts:** Continue using current role names (no changes required)
3. **Optional migration:** Redeploy cross-account role stack with new template, update account configuration

## Documentation Updates

- `docs/guides/DRS_CROSS_ACCOUNT_SETUP_VERIFICATION.md` - Update role name references
- `docs/reference/DRS_CROSS_ACCOUNT_REFERENCE.md` - Document standardized naming
- `README.md` - Update deployment instructions
- API documentation - Mark `roleArn` as optional

## Timeline

- Requirements review: 1 day
- Design and implementation: 2-3 days
- Testing: 1-2 days
- Documentation: 1 day
- Total: 5-7 days
