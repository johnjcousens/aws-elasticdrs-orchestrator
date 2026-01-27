# Requirements Document

## Introduction

This document specifies the requirements for decomposing the monolithic DR Orchestration API Handler Lambda function (11,558 lines) into three focused Lambda functions. The decomposition improves deployment safety, performance optimization, code organization, team workflow, and enables direct Lambda invocation for automation.

## Glossary

- **API_Handler**: The current monolithic Lambda function handling all REST API operations
- **Data_Management_Handler**: New Lambda function for Protection Groups and Recovery Plans CRUD operations
- **Execution_Handler**: New Lambda function for DR execution operations and Step Functions orchestration
- **Query_Handler**: New Lambda function for read-only DRS and EC2 infrastructure queries
- **Lambda_Layer**: Shared code library containing common utilities used by all three handlers
- **Protection_Group**: Tag-based or explicit server grouping for disaster recovery
- **Recovery_Plan**: Wave-based execution plan with DRS service limit validation
- **DRS**: AWS Elastic Disaster Recovery Service
- **Step_Functions**: AWS service for orchestrating long-running DR operations
- **API_Gateway**: AWS service providing REST API endpoints with Cognito authentication
- **Direct_Invocation**: Calling Lambda functions directly without API Gateway (for automation)
- **Cross_Account_Operation**: DR operations across multiple AWS accounts using IAM role assumption
- **DRS_Service_Limits**: Hard limits enforced by AWS DRS (100 servers/job, 20 concurrent jobs, 500 total servers)

## Requirements

### Requirement 1: Data Management Handler

**User Story:** As a DR administrator, I want to manage Protection Groups and Recovery Plans through dedicated CRUD operations, so that I can organize servers and define recovery strategies without affecting execution logic.

#### Acceptance Criteria

1. WHEN a user creates a Protection Group, THE Data_Management_Handler SHALL validate the request and store it in DynamoDB
2. WHEN a user updates a Recovery Plan, THE Data_Management_Handler SHALL validate wave sizes against the 100 servers per job limit
3. WHEN a user deletes a Protection Group, THE Data_Management_Handler SHALL check for conflicts with active executions before allowing deletion
4. WHEN a user resolves tag-based server selection, THE Data_Management_Handler SHALL query DRS API and return matching servers
5. THE Data_Management_Handler SHALL support both API Gateway invocation and direct Lambda invocation patterns
6. WHEN performing cross-account operations, THE Data_Management_Handler SHALL assume the appropriate IAM role for the target account

### Requirement 2: Execution Handler

**User Story:** As a DR operator, I want to execute recovery plans and manage active DR operations, so that I can perform failover and failback operations safely and efficiently.

#### Acceptance Criteria

1. WHEN a user executes a Recovery Plan, THE Execution_Handler SHALL validate server availability and start Step Functions execution
2. WHEN a user cancels an execution, THE Execution_Handler SHALL terminate the Step Functions execution and update DynamoDB status
3. WHEN a user pauses an execution, THE Execution_Handler SHALL update the execution status and notify Step Functions
4. WHEN a user resumes an execution, THE Execution_Handler SHALL validate current state and continue Step Functions execution
5. WHEN terminating recovery instances, THE Execution_Handler SHALL call DRS API to terminate instances and update execution status
6. THE Execution_Handler SHALL detect conflicts by checking both DynamoDB execution records and live DRS job status
7. WHEN validating execution requests, THE Execution_Handler SHALL enforce DRS service limits (100 servers/job, 20 concurrent jobs, 500 servers in all jobs, 300 replicating servers)
8. THE Execution_Handler SHALL support async execution pattern with worker mode to avoid API Gateway 29-second timeout
9. WHEN querying execution status, THE Execution_Handler SHALL return real-time status from DynamoDB and Step Functions

### Requirement 3: Query Handler

**User Story:** As a DR administrator, I want to query DRS infrastructure and EC2 resources efficiently, so that I can monitor capacity, validate configurations, and troubleshoot issues without impacting DR operations.

#### Acceptance Criteria

1. WHEN a user queries DRS source servers, THE Query_Handler SHALL return server details with replication status across all regions
2. WHEN a user queries DRS quotas, THE Query_Handler SHALL return current capacity metrics and service limits
3. WHEN a user queries target accounts, THE Query_Handler SHALL return registered cross-account configurations
4. WHEN a user queries EC2 resources, THE Query_Handler SHALL return subnets, security groups, instance types, and instance profiles
5. WHEN a user queries current account info, THE Query_Handler SHALL return account ID and region information
6. WHEN a user exports configuration, THE Query_Handler SHALL return Protection Groups and Recovery Plans in JSON format
7. WHEN a user queries permissions, THE Query_Handler SHALL return RBAC permissions based on Cognito user attributes
8. THE Query_Handler SHALL use read-only IAM permissions (no write access to DynamoDB or DRS)
9. THE Query_Handler SHALL support cross-account queries by assuming read-only roles in target accounts

### Requirement 4: Shared Lambda Layer

**User Story:** As a developer, I want common utilities extracted to a Lambda Layer, so that code is reused efficiently and updates to shared logic propagate to all handlers.

#### Acceptance Criteria

1. THE Lambda_Layer SHALL contain conflict detection logic for checking active executions and DRS jobs
2. THE Lambda_Layer SHALL contain DRS service limit validation functions (wave sizes, concurrent jobs, total servers)
3. THE Lambda_Layer SHALL contain cross-account IAM role assumption utilities
4. THE Lambda_Layer SHALL contain execution utilities for termination logic
5. THE Lambda_Layer SHALL contain DecimalEncoder for DynamoDB Decimal serialization (always used)
6. THE Lambda_Layer MAY contain RBAC middleware (used only in API Gateway + Cognito mode)
7. THE Lambda_Layer MAY contain API Gateway response utilities (used only in standalone mode)
8. WHEN any handler imports shared utilities, THE Lambda_Layer SHALL provide consistent behavior across all functions
9. WHEN deployed in HRP mode (no API Gateway, no Cognito), THE handlers SHALL skip RBAC middleware and API Gateway response formatting

### Requirement 5: API Compatibility

**User Story:** As a frontend developer, I want all existing API endpoints to continue working identically, so that the frontend, CLI tools, and automation scripts require no changes.

#### Acceptance Criteria

1. WHEN the frontend calls any existing API endpoint, THE System SHALL return identical responses to the current implementation
2. WHEN API Gateway routes requests, THE System SHALL route to the appropriate handler based on path prefix
3. WHEN authentication is required, THE System SHALL enforce Cognito User Pool authentication via API Gateway authorizer
4. WHEN CORS preflight requests arrive, THE System SHALL return appropriate CORS headers
5. THE System SHALL maintain backward compatibility for all 48 existing API endpoints
6. WHEN EventBridge triggers tag sync, THE System SHALL bypass authentication and invoke the appropriate handler
7. WHEN a handler receives an API Gateway request, THE System SHALL route to the correct function based on HTTP method and path
8. THE Data_Management_Handler SHALL correctly route 13 API Gateway endpoints
9. THE Execution_Handler SHALL correctly route 22 API Gateway endpoints
10. THE Query_Handler SHALL correctly route 13 API Gateway endpoints
11. WHEN an unrecognized path is requested, THE System SHALL return 404 Not Found with appropriate error message

### Requirement 6: Direct Lambda Invocation

**User Story:** As an automation engineer, I want to invoke Lambda functions directly without API Gateway, so that I can integrate DR operations into automated workflows and scheduled tasks.

#### Acceptance Criteria

1. WHEN invoking Data_Management_Handler directly, THE System SHALL accept both API Gateway event format and direct invocation payload
2. WHEN invoking Execution_Handler directly, THE System SHALL accept both API Gateway event format and direct invocation payload
3. WHEN invoking Query_Handler directly, THE System SHALL accept both API Gateway event format and direct invocation payload
4. WHEN direct invocation payload is provided, THE System SHALL extract operation parameters and execute the requested operation
5. WHEN direct invocation completes, THE System SHALL return results in a consistent format (not API Gateway response format)

### Requirement 7: Performance Optimization

**User Story:** As a platform engineer, I want each Lambda function optimized for its workload, so that cold starts are minimized and execution costs are reduced.

#### Acceptance Criteria

1. THE Data_Management_Handler SHALL be configured with 512 MB memory and 120-second timeout
2. THE Execution_Handler SHALL be configured with 512 MB memory and 300-second timeout (for DRS operations)
3. THE Query_Handler SHALL be configured with 256 MB memory and 60-second timeout (read-only operations)
4. WHEN Query_Handler is invoked frequently, THE System SHALL benefit from reduced cold start times (smaller code package)
5. WHEN Execution_Handler is deployed, THE System SHALL not affect Data_Management_Handler or Query_Handler availability
6. ALL handlers SHALL use a single unified IAM execution role (not individual per-handler roles)

### Requirement 8: Independent Deployment

**User Story:** As a DevOps engineer, I want to deploy each Lambda function independently, so that changes to one function do not risk breaking others.

#### Acceptance Criteria

1. WHEN Data_Management_Handler is deployed, THE System SHALL not require redeployment of Execution_Handler or Query_Handler
2. WHEN Execution_Handler is deployed, THE System SHALL not require redeployment of Data_Management_Handler or Query_Handler
3. WHEN Query_Handler is deployed, THE System SHALL not require redeployment of Data_Management_Handler or Execution_Handler
4. WHEN Lambda_Layer is updated, THE System SHALL require redeployment of all handlers that depend on it
5. THE System SHALL support rolling deployments where handlers are updated one at a time

### Requirement 9: Testing and Validation

**User Story:** As a QA engineer, I want comprehensive tests for each handler, so that I can verify correctness and prevent regressions.

#### Acceptance Criteria

1. WHEN Data_Management_Handler is tested, THE System SHALL validate CRUD operations for Protection Groups and Recovery Plans
2. WHEN Execution_Handler is tested, THE System SHALL validate execution lifecycle (start, pause, resume, cancel, terminate)
3. WHEN Query_Handler is tested, THE System SHALL validate all query operations return correct data
4. WHEN Lambda_Layer is tested, THE System SHALL validate shared utilities work correctly in isolation
5. WHEN integration tests run, THE System SHALL validate end-to-end flows across all three handlers
6. WHEN API Gateway integration is tested, THE System SHALL validate routing to correct handlers based on path

### Requirement 10: Migration Strategy

**User Story:** As a project manager, I want a phased migration approach, so that risk is minimized and rollback is possible at each phase.

#### Acceptance Criteria

1. WHEN Phase 1 completes, THE Query_Handler SHALL be deployed and operational (lowest risk)
2. WHEN Phase 2 completes, THE Execution_Handler SHALL be deployed and operational (highest value)
3. WHEN Phase 3 completes, THE Data_Management_Handler SHALL replace the original API_Handler
4. WHEN any phase fails, THE System SHALL support rollback to the previous phase
5. WHEN migration completes, THE System SHALL have zero downtime for API operations

### Requirement 11: Cross-Account Operations

**User Story:** As a multi-account administrator, I want cross-account DR operations to work identically across all three handlers, so that hub-and-spoke architecture is preserved.

#### Acceptance Criteria

1. WHEN Data_Management_Handler resolves tag-based servers, THE System SHALL assume cross-account roles if accountId is specified
2. WHEN Execution_Handler executes Recovery Plans, THE System SHALL determine target account from Protection Group metadata
3. WHEN Query_Handler queries DRS infrastructure, THE System SHALL assume cross-account roles for target account queries
4. WHEN cross-account role assumption fails, THE System SHALL return clear error messages with troubleshooting guidance
5. THE System SHALL validate that all Protection Groups in a Recovery Plan belong to the same account (mixed accounts not supported)

### Requirement 12: DRS Service Limits Enforcement

**User Story:** As a DR operator, I want DRS service limits enforced consistently, so that executions do not fail due to exceeding AWS quotas.

#### Acceptance Criteria

1. WHEN validating Recovery Plans, THE System SHALL enforce 100 servers per job limit (L-B827C881, hard limit)
2. WHEN starting executions, THE System SHALL enforce 20 concurrent jobs per region limit (L-D88FAC3A, hard limit)
3. WHEN starting executions, THE System SHALL enforce 500 servers across all active jobs limit (L-05AFA8C6, hard limit)
4. WHEN checking capacity, THE System SHALL enforce 300 replicating servers hard limit (L-C1D14A2B, cannot be increased)
5. WHEN checking capacity, THE System SHALL monitor against 4000 source servers limit (L-E28BE5E0, adjustable via service quota request)
6. WHEN replicating servers reach 250, THE System SHALL emit warning alerts (83% of 300 hard limit)
7. WHEN replicating servers reach 280, THE System SHALL block new operations (93% of 300 hard limit)
8. THE System SHALL validate server replication states before allowing recovery operations

### Requirement 13: Observability and Monitoring

**User Story:** As a platform engineer, I want comprehensive logging and metrics for each handler, so that I can troubleshoot issues and monitor performance.

#### Acceptance Criteria

1. WHEN any handler processes a request, THE System SHALL log request details (method, path, user)
2. WHEN any handler encounters an error, THE System SHALL log full stack traces with context
3. WHEN cross-account operations occur, THE System SHALL log account ID and role assumption details
4. WHEN DRS service limits are checked, THE System SHALL log current capacity metrics
5. THE System SHALL emit CloudWatch metrics for handler invocation count, duration, and errors
6. WHEN conflict detection runs, THE System SHALL log servers in active executions and DRS jobs

### Requirement 14: Code Quality and Style Consistency

**User Story:** As a developer, I want the refactored code to maintain existing conventions and style, so that the codebase remains consistent and maintainable.

#### Acceptance Criteria

1. THE System SHALL preserve the existing CamelCase naming convention for all Python variables and functions
2. THE System SHALL maintain existing code comments that explain WHY code works a certain way
3. THE System SHALL preserve existing error handling patterns and logging statements
4. THE System SHALL maintain existing DynamoDB attribute naming conventions (camelCase)
5. THE System SHALL preserve existing API response formats and field names
6. WHEN extracting code to Lambda Layer, THE System SHALL maintain the original function signatures and behavior

### Requirement 15: Documentation and Knowledge Transfer

**User Story:** As a developer, I want comprehensive documentation for the new architecture, so that I can understand the design and maintain the system.

#### Acceptance Criteria

1. THE System SHALL provide architecture diagrams showing the three handlers and their interactions
2. THE System SHALL provide API routing documentation mapping endpoints to handlers
3. THE System SHALL provide IAM permission documentation for each handler
4. THE System SHALL provide deployment documentation for each phase of migration
5. THE System SHALL provide troubleshooting guides for common issues
6. THE System SHALL provide code examples for direct Lambda invocation patterns

---

## Future Enhancements (Phase 2 - Separate Spec)

The following enhancements are planned for Phase 2 after the API handler decomposition is complete. These will be documented in a separate spec session focused on HRP integration.

### HRP Integration Parameters

**Objective**: Enable the DRS orchestration to integrate seamlessly with the Enterprise DR Orchestration Platform (HRP) by making infrastructure components optional and supporting external resource references.

**Key Features**:

1. **Deployment Mode Flags**:
   - `DeployAPI` parameter (true/false) - Skip API Gateway + Cognito when false
   - `DeployFrontend` parameter (true/false) - Skip React UI when false (already exists)
   - `DeployStepFunctions` parameter (true/false) - Skip DRS Step Functions when false

2. **External Resource Integration**:
   - `ExternalStateMachineArn` parameter - Use HRP's Step Functions instead of deploying our own
   - `ExternalDynamoDBName` parameter - Create DRS tables in HRP's DynamoDB database

3. **HRP Integration Mode**:
   - When `DeployAPI=false`, `DeployFrontend=false`, `DeployStepFunctions=false`
   - Deploy only Lambda functions (Data Management, Execution, Query handlers)
   - Create DRS tables in HRP's DynamoDB database
   - Lambda functions called directly by HRP Step Functions (no API Gateway)
   - RBAC middleware and API Gateway response utilities not used (reduces package size)

4. **Deployment Scenarios**:
   - **Standalone** (current): All components deployed, own infrastructure, RBAC via Cognito
   - **HRP Integration** (future): Lambda-only deployment, uses HRP infrastructure, no RBAC middleware
   - **Hybrid**: API-only without frontend, for automation/testing

**Benefits**:
- Eliminates duplicate infrastructure (API Gateway, Cognito, Step Functions, DynamoDB)
- Reduces operational overhead and costs
- Enables unified HRP platform with multiple technology adapters
- Maintains backward compatibility with standalone deployment mode

**Implementation Notes**:
- Phase 1 (current spec) focuses on API handler decomposition
- Phase 2 (future spec) adds HRP integration parameters
- Lambda functions designed to work in both modes (API Gateway OR direct invocation)
- DynamoDB table names passed as environment variables (works with any database)
