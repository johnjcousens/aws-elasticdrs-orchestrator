# Requirements Document

## Introduction

This document specifies requirements for completing and standardizing Direct Lambda Invocation Mode in the AWS DRS Orchestration Platform. The platform currently has **partial** direct invocation support in query-handler and data-management-handler, but lacks:

1. **Standardized direct invocation interface** in execution-handler
2. **Complete operation coverage** for all frontend features (server launch configs, staging accounts, tag sync, DRS capacity management, conflict detection)
3. **Conditional CloudFormation deployment** to optionally exclude API Gateway, Cognito, and frontend
4. **Comprehensive documentation** for all direct invocation operations

This feature will enable full headless operation where all Lambda functions can be invoked directly via AWS SDK/CLI with IAM-based authorization, supporting infrastructure-as-code workflows, CI/CD pipelines, and programmatic disaster recovery operations without requiring a web UI or user authentication system.

## Current Implementation Status

**query-handler** (lambda/query-handler/index.py):
- ✅ Has `handle_direct_invocation()` function
- ✅ Supports ~16 operations: get_drs_source_servers, get_drs_account_capacity, get_target_accounts, export_configuration, validate_staging_account, discover_staging_accounts, get_combined_capacity, sync_staging_accounts, etc.
- ⚠️ Missing: Server launch config operations, tag sync status, extended source server sync, DRS capacity conflict detection

**data-management-handler** (lambda/data-management-handler/index.py):
- ✅ Has `handle_direct_invocation()` function
- ⚠️ Operation coverage unknown - needs investigation
- ⚠️ Missing: Server launch config CRUD, staging account CRUD, tag sync trigger/settings, configuration import

**execution-handler** (lambda/execution-handler/index.py):
- ⚠️ Has action-based invocation (`action="start_wave_recovery"`) for Step Functions
- ⚠️ Has operation-based invocation (`operation="find|poll|finalize"`) for EventBridge
- ❌ Does NOT have standardized `handle_direct_invocation()` function
- ❌ Missing: Direct invocation interface for start/cancel/pause/resume/terminate operations

**CloudFormation**:
- ❌ No conditional deployment support (DeployApiGateway parameter)
- ❌ API Gateway, Cognito, and frontend are always deployed

## Glossary

- **System**: The AWS DRS Orchestration Platform
- **Direct_Invocation_Mode**: Operation mode where Lambda functions are invoked directly via AWS SDK/CLI without API Gateway
- **API_Gateway_Mode**: Current operation mode where Lambda functions are invoked through API Gateway with Cognito authentication
- **OrchestrationRole**: IAM role that controls all direct Lambda invocations and cross-account DRS operations
- **Query_Handler**: Lambda function that handles read-only queries (GET operations)
- **Execution_Handler**: Lambda function that handles recovery execution lifecycle operations
- **Data_Management_Handler**: Lambda function that handles CRUD operations for protection groups and recovery plans
- **Dual_Mode_Support**: Ability for Lambda functions to handle both API Gateway and direct invocation patterns
- **IAM_Principal**: The AWS IAM entity (user, role, or service) making the direct Lambda invocation
- **Event_Format**: The JSON structure passed to Lambda functions during invocation
- **Cognito_User**: User authenticated through AWS Cognito User Pools
- **Cross_Account_Operation**: DRS operation performed in a target AWS account different from the orchestration account

## Requirements

### Requirement 1: Dual Invocation Mode Support

**User Story:** As a platform operator, I want Lambda functions to support both API Gateway and direct invocation modes, so that existing API Gateway deployments continue working while enabling new direct invocation capabilities.

#### Acceptance Criteria

1. WHEN a Lambda function receives an event with "requestContext", THE System SHALL process it as an API Gateway invocation
2. WHEN a Lambda function receives an event with "operation" field, THE System SHALL process it as a direct invocation
3. WHEN processing API Gateway invocations, THE System SHALL extract user context from Cognito claims
4. WHEN processing direct invocations, THE System SHALL extract IAM principal from Lambda context
5. WHEN a Lambda function processes either invocation mode, THE System SHALL return responses in the appropriate format for that mode

### Requirement 2: Direct Invocation Event Format

**User Story:** As a developer, I want a standardized event format for direct Lambda invocations, so that I can programmatically invoke operations without API Gateway.

#### Acceptance Criteria

1. WHEN invoking Query_Handler directly, THE System SHALL accept events with "operation" and optional "queryParams" fields
2. WHEN invoking Execution_Handler directly, THE System SHALL accept events with "operation" and required operation-specific parameters
3. WHEN invoking Data_Management_Handler directly, THE System SHALL accept events with "operation" and "body" fields
4. WHEN an event contains both "requestContext" and "operation" fields, THE System SHALL prioritize "requestContext" (API Gateway mode)
5. WHEN an event contains neither "requestContext" nor "operation" fields, THE System SHALL return an error indicating invalid invocation format

### Requirement 3: IAM-Based Authorization

**User Story:** As a security administrator, I want direct Lambda invocations to use IAM-based authorization instead of Cognito, so that I can control access through AWS IAM policies.

#### Acceptance Criteria

1. WHEN a direct invocation occurs, THE System SHALL extract the IAM principal ARN from the Lambda context
2. WHEN the IAM principal is OrchestrationRole, THE System SHALL grant full access to all operations
3. WHEN the IAM principal is not OrchestrationRole, THE System SHALL deny the invocation with an authorization error
4. WHEN audit logging occurs for direct invocations, THE System SHALL record the IAM principal ARN instead of Cognito user ID
5. WHEN a direct invocation is denied, THE System SHALL log a security event with the IAM principal and attempted operation

### Requirement 4: Query Handler Operation Completion

**User Story:** As a developer, I want to query all DRS resources and configurations directly via Lambda invocation, so that I can retrieve complete data programmatically without API Gateway.

#### Acceptance Criteria

1. WHEN invoking Query_Handler with operation "list_protection_groups", THE System SHALL return all protection groups
2. WHEN invoking Query_Handler with operation "get_protection_group" and "groupId" parameter, THE System SHALL return the specified protection group with all launch configurations
3. WHEN invoking Query_Handler with operation "get_server_launch_config" and "groupId" + "serverId" parameters, THE System SHALL return individual server launch configuration
4. WHEN invoking Query_Handler with operation "get_server_config_history" and "groupId" + "serverId" parameters, THE System SHALL return configuration change audit history
5. WHEN invoking Query_Handler with operation "list_recovery_plans", THE System SHALL return all recovery plans
6. WHEN invoking Query_Handler with operation "get_recovery_plan" and "planId" parameter, THE System SHALL return the specified recovery plan
7. WHEN invoking Query_Handler with operation "list_executions", THE System SHALL return all executions with optional filtering
8. WHEN invoking Query_Handler with operation "get_execution" and "executionId" parameter, THE System SHALL return the specified execution details
9. WHEN invoking Query_Handler with operation "get_drs_source_servers" and optional "region" parameter, THE System SHALL return DRS source servers
10. WHEN invoking Query_Handler with operation "get_target_accounts", THE System SHALL return all registered target accounts
11. WHEN invoking Query_Handler with operation "get_staging_accounts" and "targetAccountId" parameter, THE System SHALL return staging accounts for the target account
12. WHEN invoking Query_Handler with operation "get_combined_capacity" and "targetAccountId" parameter, THE System SHALL return combined DRS capacity for target and staging accounts
13. WHEN invoking Query_Handler with operation "get_all_accounts_capacity", THE System SHALL return DRS capacity for all accounts
14. WHEN invoking Query_Handler with operation "get_tag_sync_status", THE System SHALL return current tag synchronization status
15. WHEN invoking Query_Handler with operation "get_tag_sync_settings", THE System SHALL return tag synchronization configuration
16. WHEN invoking Query_Handler with operation "get_drs_capacity_conflicts", THE System SHALL return detected capacity conflicts across accounts
17. WHEN invoking Query_Handler with an invalid operation, THE System SHALL return an error indicating the operation is not supported

### Requirement 5: Execution Handler Standardization

**User Story:** As a developer, I want to manage recovery executions directly via standardized Lambda invocation, so that I can automate disaster recovery operations without API Gateway.

#### Acceptance Criteria

1. WHEN invoking Execution_Handler with operation "start_execution" and required parameters, THE System SHALL initiate a recovery plan execution
2. WHEN invoking Execution_Handler with operation "cancel_execution" and "executionId" parameter, THE System SHALL cancel the specified execution
3. WHEN invoking Execution_Handler with operation "pause_execution" and "executionId" parameter, THE System SHALL pause the specified execution
4. WHEN invoking Execution_Handler with operation "resume_execution" and "executionId" parameter, THE System SHALL resume the specified execution
5. WHEN invoking Execution_Handler with operation "terminate_instances" and "executionId" parameter, THE System SHALL terminate recovery instances for the specified execution
6. WHEN invoking Execution_Handler with operation "get_recovery_instances" and "executionId" parameter, THE System SHALL return recovery instance details
7. WHEN invoking Execution_Handler with operation "list_executions", THE System SHALL return all executions (delegating to Query_Handler)
8. WHEN invoking Execution_Handler with operation "get_execution" and "executionId" parameter, THE System SHALL return execution details (delegating to Query_Handler)
9. WHEN Execution_Handler receives action-based invocations from Step Functions, THE System SHALL continue processing them identically
10. WHEN Execution_Handler receives operation-based invocations from EventBridge, THE System SHALL continue processing them identically
11. WHEN invoking Execution_Handler with an invalid operation, THE System SHALL return an error indicating the operation is not supported

### Requirement 6: Data Management Handler Operation Completion

**User Story:** As a developer, I want to manage all protection groups, recovery plans, and configurations directly via Lambda invocation, so that I can automate infrastructure configuration without API Gateway.

#### Acceptance Criteria

1. WHEN invoking Data_Management_Handler with operation "create_protection_group" and group data, THE System SHALL create a new protection group
2. WHEN invoking Data_Management_Handler with operation "update_protection_group" with "groupId" and updated data, THE System SHALL update the specified protection group
3. WHEN invoking Data_Management_Handler with operation "delete_protection_group" and "groupId" parameter, THE System SHALL delete the specified protection group
4. WHEN invoking Data_Management_Handler with operation "update_server_launch_config" with "groupId", "serverId", and config data, THE System SHALL update individual server launch configuration
5. WHEN invoking Data_Management_Handler with operation "delete_server_launch_config" with "groupId" and "serverId" parameters, THE System SHALL delete individual server launch configuration
6. WHEN invoking Data_Management_Handler with operation "bulk_update_server_configs" with "groupId" and array of server configs, THE System SHALL update multiple server configurations
7. WHEN invoking Data_Management_Handler with operation "validate_static_ip" with IP address and subnet parameters, THE System SHALL validate static IP availability
8. WHEN invoking Data_Management_Handler with operation "create_recovery_plan" and plan data, THE System SHALL create a new recovery plan
9. WHEN invoking Data_Management_Handler with operation "update_recovery_plan" with "planId" and updated data, THE System SHALL update the specified recovery plan
10. WHEN invoking Data_Management_Handler with operation "delete_recovery_plan" and "planId" parameter, THE System SHALL delete the specified recovery plan
11. WHEN invoking Data_Management_Handler with operation "add_target_account" with account data, THE System SHALL register a new target account
12. WHEN invoking Data_Management_Handler with operation "update_target_account" with "accountId" and updated data, THE System SHALL update target account configuration
13. WHEN invoking Data_Management_Handler with operation "delete_target_account" and "accountId" parameter, THE System SHALL remove target account registration
14. WHEN invoking Data_Management_Handler with operation "add_staging_account" with "targetAccountId" and staging account data, THE System SHALL add staging account to target account
15. WHEN invoking Data_Management_Handler with operation "remove_staging_account" with "targetAccountId" and "stagingAccountId" parameters, THE System SHALL remove staging account from target account
16. WHEN invoking Data_Management_Handler with operation "trigger_tag_sync", THE System SHALL initiate tag synchronization across all accounts
17. WHEN invoking Data_Management_Handler with operation "update_tag_sync_settings" with settings data, THE System SHALL update tag synchronization configuration
18. WHEN invoking Data_Management_Handler with operation "sync_extended_source_servers" with "targetAccountId" parameter, THE System SHALL synchronize extended source servers from staging accounts
19. WHEN invoking Data_Management_Handler with operation "import_configuration" with configuration data, THE System SHALL import protection groups and recovery plans
20. WHEN invoking Data_Management_Handler with an invalid operation, THE System SHALL return an error indicating the operation is not supported

### Requirement 7: CloudFormation Conditional Deployment

**User Story:** As a platform administrator, I want to optionally deploy API Gateway, Cognito, and frontend components, so that I can run the platform in headless mode when those components are not needed.

#### Acceptance Criteria

1. WHEN the CloudFormation parameter "DeployApiGateway" is set to "false", THE System SHALL NOT create API Gateway resources
2. WHEN the CloudFormation parameter "DeployApiGateway" is set to "false", THE System SHALL NOT create Cognito User Pool resources
3. WHEN the CloudFormation parameter "DeployApiGateway" is set to "false", THE System SHALL NOT create frontend S3 bucket and CloudFront distribution
4. WHEN the CloudFormation parameter "DeployApiGateway" is set to "true", THE System SHALL create all API Gateway, Cognito, and frontend resources
5. WHEN deploying without API Gateway, THE System SHALL still create all Lambda functions, DynamoDB tables, Step Functions, and EventBridge rules
6. WHEN deploying without API Gateway, THE System SHALL configure Lambda functions to accept direct invocations from OrchestrationRole
7. WHEN deploying with API Gateway, THE System SHALL configure Lambda functions to accept both API Gateway and direct invocations

### Requirement 8: Audit Logging for Direct Invocations

**User Story:** As a compliance officer, I want all direct Lambda invocations to be logged with IAM principal information, so that I can audit who performed which operations.

#### Acceptance Criteria

1. WHEN a direct invocation occurs, THE System SHALL log the IAM principal ARN
2. WHEN a direct invocation occurs, THE System SHALL log the operation name and parameters
3. WHEN a direct invocation occurs, THE System SHALL log the timestamp in ISO 8601 format
4. WHEN a direct invocation succeeds, THE System SHALL log the operation result summary
5. WHEN a direct invocation fails, THE System SHALL log the error message and error type
6. WHEN audit logs are written, THE System SHALL include the invocation request ID for traceability
7. WHEN audit logs are written for API Gateway invocations, THE System SHALL continue using Cognito user information

### Requirement 9: Error Handling for Direct Invocations

**User Story:** As a developer, I want clear error messages when direct invocations fail, so that I can troubleshoot issues quickly.

#### Acceptance Criteria

1. WHEN a direct invocation is missing required parameters, THE System SHALL return an error indicating which parameters are missing
2. WHEN a direct invocation uses an invalid operation name, THE System SHALL return an error listing supported operations
3. WHEN a direct invocation is denied due to IAM permissions, THE System SHALL return an error indicating authorization failure
4. WHEN a direct invocation fails due to a DynamoDB error, THE System SHALL return an error with the DynamoDB error details
5. WHEN a direct invocation fails due to a DRS API error, THE System SHALL return an error with the DRS error details
6. WHEN a direct invocation fails due to an unexpected exception, THE System SHALL return an error with a sanitized error message
7. WHEN error responses are returned for direct invocations, THE System SHALL use a consistent JSON structure with "error", "message", and optional "details" fields

### Requirement 10: Response Format Consistency

**User Story:** As a developer, I want consistent response formats between API Gateway and direct invocation modes, so that I can process responses uniformly.

#### Acceptance Criteria

1. WHEN Query_Handler returns data in API Gateway mode, THE System SHALL wrap the response in API Gateway format with statusCode, headers, and body
2. WHEN Query_Handler returns data in direct invocation mode, THE System SHALL return the data directly without API Gateway wrapping
3. WHEN Execution_Handler returns data in API Gateway mode, THE System SHALL wrap the response in API Gateway format
4. WHEN Execution_Handler returns data in direct invocation mode, THE System SHALL return the data directly without API Gateway wrapping
5. WHEN Data_Management_Handler returns data in API Gateway mode, THE System SHALL wrap the response in API Gateway format
6. WHEN Data_Management_Handler returns data in direct invocation mode, THE System SHALL return the data directly without API Gateway wrapping
7. WHEN errors occur in either mode, THE System SHALL return error information in a consistent JSON structure

### Requirement 11: OrchestrationRole IAM Permissions

**User Story:** As a platform administrator, I want OrchestrationRole to have permissions for direct Lambda invocations, so that automated systems can invoke Lambda functions programmatically.

#### Acceptance Criteria

1. WHEN OrchestrationRole is created, THE System SHALL grant lambda:InvokeFunction permission for Query_Handler
2. WHEN OrchestrationRole is created, THE System SHALL grant lambda:InvokeFunction permission for Execution_Handler
3. WHEN OrchestrationRole is created, THE System SHALL grant lambda:InvokeFunction permission for Data_Management_Handler
4. WHEN OrchestrationRole is created, THE System SHALL grant permissions to read from all DynamoDB tables
5. WHEN OrchestrationRole is created, THE System SHALL grant permissions to write to all DynamoDB tables
6. WHEN OrchestrationRole is created, THE System SHALL grant permissions to start Step Functions executions
7. WHEN OrchestrationRole is created, THE System SHALL grant permissions to assume cross-account DRS roles

### Requirement 12: Backward Compatibility

**User Story:** As a platform operator, I want existing API Gateway deployments to continue working without changes, so that I can adopt direct invocation mode gradually.

#### Acceptance Criteria

1. WHEN Lambda functions are updated to support direct invocation, THE System SHALL continue processing API Gateway requests identically to before
2. WHEN Lambda functions are updated to support direct invocation, THE System SHALL continue extracting Cognito user context from API Gateway requests
3. WHEN Lambda functions are updated to support direct invocation, THE System SHALL continue applying RBAC permissions for API Gateway requests
4. WHEN Lambda functions are updated to support direct invocation, THE System SHALL continue returning API Gateway response format for API Gateway requests
5. WHEN existing CloudFormation stacks are updated, THE System SHALL default "DeployApiGateway" parameter to "true" to maintain current behavior

### Requirement 13: Cross-Account Operations in Direct Mode

**User Story:** As a developer, I want direct Lambda invocations to support cross-account DRS operations, so that I can manage disaster recovery across multiple AWS accounts programmatically.

#### Acceptance Criteria

1. WHEN a direct invocation specifies a target account ID, THE System SHALL assume the DRSOrchestrationRole in that account
2. WHEN a direct invocation performs DRS operations, THE System SHALL use the assumed role credentials
3. WHEN a direct invocation fails to assume a cross-account role, THE System SHALL return an error indicating the assume role failure
4. WHEN a direct invocation completes cross-account operations, THE System SHALL log the target account ID in audit logs
5. WHEN a direct invocation operates in the orchestration account, THE System SHALL use the Lambda execution role credentials

### Requirement 14: Step Functions Integration

**User Story:** As a platform operator, I want Step Functions to continue working with direct invocation mode, so that wave-based orchestration remains functional.

#### Acceptance Criteria

1. WHEN Step Functions invokes Execution_Handler with action-based events, THE System SHALL process them identically in both deployment modes
2. WHEN Step Functions invokes Query_Handler for wave status polling, THE System SHALL process them identically in both deployment modes
3. WHEN Step Functions invokes dr-orchestration-stepfunction Lambda, THE System SHALL process them identically in both deployment modes
4. WHEN Step Functions completes a recovery execution, THE System SHALL update DynamoDB execution status identically in both deployment modes

### Requirement 15: EventBridge Integration

**User Story:** As a platform operator, I want EventBridge scheduled rules to continue working with direct invocation mode, so that automatic polling and monitoring remain functional.

#### Acceptance Criteria

1. WHEN EventBridge invokes Execution_Handler for execution polling, THE System SHALL process the invocation identically in both deployment modes
2. WHEN EventBridge invokes Data_Management_Handler for tag synchronization, THE System SHALL process the invocation identically in both deployment modes
3. WHEN EventBridge rules are created, THE System SHALL grant permissions to invoke Lambda functions regardless of deployment mode

### Requirement 16: Documentation and Examples

**User Story:** As a developer, I want documentation and examples for direct Lambda invocation, so that I can integrate the platform into my automation workflows.

#### Acceptance Criteria

1. WHEN documentation is provided, THE System SHALL include AWS CLI examples for each supported operation
2. WHEN documentation is provided, THE System SHALL include Python boto3 examples for each supported operation
3. WHEN documentation is provided, THE System SHALL include event format specifications for each Lambda function
4. WHEN documentation is provided, THE System SHALL include IAM policy examples for OrchestrationRole
5. WHEN documentation is provided, THE System SHALL include CloudFormation parameter examples for both deployment modes
6. WHEN documentation is provided, THE System SHALL include troubleshooting guidance for common errors
7. WHEN documentation is provided, THE System SHALL include migration guidance from API Gateway mode to direct invocation mode
