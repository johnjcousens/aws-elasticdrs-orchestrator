# Requirements Document

## Introduction

This document defines requirements for hardening the frontend deployment architecture of the DRS Orchestration Platform. The current CloudFormation custom resource implementation has proven fragile during UPDATE operations, causing data loss and stack failures. These requirements ensure production-ready deployment that can be safely integrated with the Enterprise DR Orchestration Platform (HRP).

## Glossary

- **Custom_Resource**: A CloudFormation resource backed by a Lambda function that handles CREATE, UPDATE, and DELETE lifecycle events
- **PhysicalResourceId**: A unique identifier returned by custom resources that CloudFormation uses to track resource identity across updates
- **Resource_Replacement**: When CloudFormation detects a PhysicalResourceId change, it creates a new resource and deletes the old one
- **Stack_Status**: The current state of a CloudFormation stack (e.g., CREATE_IN_PROGRESS, UPDATE_ROLLBACK_FAILED)
- **Frontend_Deployer**: The consolidated Lambda function that handles frontend deployment, configuration injection, and bucket cleanup (replaces separate Frontend_Builder and Bucket_Cleaner)
- **crhelper**: AWS CloudFormation Resource Helper library for building custom resources

## Requirements

### Requirement 1: Consolidated Lambda Architecture

**User Story:** As a DevOps engineer, I want frontend deployment and bucket cleanup handled by a single Lambda function, so that the architecture is simpler and easier to maintain.

#### Acceptance Criteria

1. THE Frontend_Deployer SHALL handle both frontend deployment (CREATE/UPDATE) and bucket cleanup (DELETE) in a single Lambda function
2. THE Frontend_Deployer SHALL replace the separate Frontend_Builder and Bucket_Cleaner Lambda functions
3. THE CloudFormation template SHALL use a single Custom_Resource for frontend deployment instead of two separate resources
4. THE Frontend_Deployer SHALL share common code for stack status checking, logging, and error handling across all operations

### Requirement 2: Stable Resource Identity

**User Story:** As a DevOps engineer, I want frontend deployments to maintain stable resource identity, so that CloudFormation UPDATE operations never trigger resource replacement.

#### Acceptance Criteria

1. THE Frontend_Deployer SHALL use a deterministic PhysicalResourceId based on the bucket name
2. WHEN the Frontend_Deployer handles CREATE or UPDATE events, THE Frontend_Deployer SHALL set PhysicalResourceId to `frontend-deployer-{bucket_name}`
3. THE PhysicalResourceId SHALL remain constant across all UPDATE operations for the same bucket
4. WHEN CloudFormation sends an UPDATE event, THE Frontend_Deployer SHALL NOT trigger resource replacement behavior

### Requirement 3: Safe Delete Handling

**User Story:** As a DevOps engineer, I want bucket cleanup to only occur during actual stack deletion, so that UPDATE operations never cause data loss.

#### Acceptance Criteria

1. WHEN the Frontend_Deployer receives a DELETE event, THE Frontend_Deployer SHALL check the stack status before any cleanup
2. IF the stack status does NOT contain "DELETE", THEN THE Frontend_Deployer SHALL skip bucket cleanup and return success
3. IF the stack status contains "DELETE_IN_PROGRESS", THEN THE Frontend_Deployer SHALL empty the bucket to allow CloudFormation to delete it
4. IF the stack status check fails, THEN THE Frontend_Deployer SHALL skip bucket cleanup to be safe
5. WHEN bucket cleanup is skipped, THE Frontend_Deployer SHALL log the reason and return success
6. THE bucket cleanup logic SHALL only exist to enable stack deletion (S3 buckets with objects cannot be deleted by CloudFormation)

### Requirement 4: Defensive Security Validation

**User Story:** As a security engineer, I want security validation to block actual attacks while allowing legitimate Lambda operations, so that deployments succeed without compromising security.

#### Acceptance Criteria

1. THE validate_file_path function SHALL only block actual path traversal patterns (`..`, URL-encoded variants)
2. THE validate_file_path function SHALL allow Lambda runtime paths like `/var/task/frontend`
3. THE validate_file_path function SHALL allow temporary directory paths like `/tmp`
4. WHEN a path traversal pattern is detected, THE validate_file_path function SHALL log a security event and raise InputValidationError
5. THE security validation SHALL NOT block paths based on directory depth or absolute path patterns
6. THE security utilities SHALL be defensive (block attacks) NOT offensive (sanitize/modify legitimate data)
7. THE security utilities SHALL NOT modify data that Lambda functions expect to receive unchanged
8. WHEN input passes validation, THE security utilities SHALL return the input unchanged
9. THE sanitize functions SHALL only remove characters that are genuinely dangerous (null bytes, control characters) not characters that are valid in file paths or AWS resource names

### Requirement 5: Idempotent Deployments

**User Story:** As a DevOps engineer, I want frontend deployments to be idempotent, so that running the same deployment multiple times produces consistent results.

#### Acceptance Criteria

1. WHEN the Frontend_Deployer deploys files to S3, THE Frontend_Deployer SHALL overwrite existing files with the same keys
2. THE Frontend_Deployer SHALL NOT delete files from S3 that are not part of the current deployment
3. WHEN CloudFront invalidation is created, THE Frontend_Deployer SHALL use a unique CallerReference per invocation
4. IF a deployment fails partway through, THE Frontend_Deployer SHALL leave the bucket in a usable state with previous content

### Requirement 6: Graceful Error Recovery

**User Story:** As a DevOps engineer, I want custom resources to handle errors gracefully, so that stacks can recover from failed states without manual intervention.

#### Acceptance Criteria

1. WHEN the Frontend_Deployer encounters an error during CREATE, THE Frontend_Deployer SHALL return FAILED status with descriptive error message
2. WHEN the Frontend_Deployer encounters an error during UPDATE, THE Frontend_Deployer SHALL return FAILED status without modifying bucket contents
3. WHEN the Frontend_Deployer encounters an error during DELETE, THE Frontend_Deployer SHALL return SUCCESS to allow stack deletion to continue
4. IF the S3 bucket does not exist during DELETE, THEN THE Frontend_Deployer SHALL return SUCCESS
5. THE Frontend_Deployer SHALL always send a response to CloudFormation within the Lambda timeout period

### Requirement 7: Rollback Safety

**User Story:** As a DevOps engineer, I want UPDATE_ROLLBACK operations to complete successfully, so that failed updates don't leave stacks in unrecoverable states.

#### Acceptance Criteria

1. WHEN CloudFormation triggers UPDATE_ROLLBACK, THE Frontend_Deployer SHALL handle the rollback DELETE event without emptying the bucket
2. THE Frontend_Deployer SHALL detect rollback scenarios by checking for "ROLLBACK" in stack status
3. IF stack status contains "ROLLBACK", THEN THE Frontend_Deployer SHALL skip bucket cleanup
4. THE Frontend_Deployer SHALL log rollback detection for debugging purposes

### Requirement 8: Comprehensive Logging

**User Story:** As a DevOps engineer, I want comprehensive logging of deployment operations, so that I can diagnose issues quickly.

#### Acceptance Criteria

1. THE Frontend_Deployer SHALL log the CloudFormation event type (CREATE, UPDATE, DELETE) at the start of each invocation
2. THE Frontend_Deployer SHALL log the stack status when making cleanup decisions
3. THE Frontend_Deployer SHALL log the number of files deployed on successful deployment
4. THE Frontend_Deployer SHALL log the CloudFront invalidation ID on successful cache invalidation
5. WHEN errors occur, THE Frontend_Deployer SHALL log the full stack trace
6. THE Frontend_Deployer SHALL use structured logging with security event classification

### Requirement 9: Configuration Injection Reliability

**User Story:** As a frontend developer, I want AWS configuration to be reliably injected into the frontend build, so that the application can connect to backend services.

#### Acceptance Criteria

1. THE Frontend_Deployer SHALL generate aws-config.json at the root of the dist directory
2. THE Frontend_Deployer SHALL generate aws-config.js in the assets directory for backwards compatibility
3. THE Frontend_Deployer SHALL inject a script tag into index.html before the first script tag
4. IF index.html does not contain script tags, THEN THE Frontend_Deployer SHALL inject before the closing head tag
5. THE configuration files SHALL include UserPoolId, UserPoolClientId, IdentityPoolId, ApiEndpoint, and Region
6. THE Frontend_Deployer SHALL sanitize all configuration values before injection

### Requirement 10: Cache Control Headers

**User Story:** As a frontend developer, I want proper cache control headers on deployed files, so that users always get fresh content for dynamic files and cached content for static assets.

#### Acceptance Criteria

1. WHEN uploading index.html, THE Frontend_Deployer SHALL set Cache-Control to "no-cache, no-store, must-revalidate"
2. WHEN uploading aws-config.json, THE Frontend_Deployer SHALL set Cache-Control to "no-cache, no-store, must-revalidate"
3. WHEN uploading static assets (JS, CSS, images), THE Frontend_Deployer SHALL set Cache-Control to "public, max-age=31536000, immutable"
4. THE Frontend_Deployer SHALL set appropriate Content-Type headers based on file extension

### Requirement 11: Custom Resource Response Compliance

**User Story:** As a CloudFormation user, I want custom resources to comply with CloudFormation response requirements, so that stack operations complete correctly.

#### Acceptance Criteria

1. THE Frontend_Deployer SHALL always send a response to the CloudFormation pre-signed URL
2. THE response SHALL include Status (SUCCESS or FAILED), PhysicalResourceId, StackId, RequestId, and LogicalResourceId
3. THE response SHALL include a Reason field with descriptive message
4. IF the Lambda times out before sending a response, THEN CloudFormation SHALL receive a timeout failure
5. THE Frontend_Deployer SHALL handle network errors when sending responses by logging and re-raising

### Requirement 12: CloudFormation Template Simplification

**User Story:** As a DevOps engineer, I want a simplified CloudFormation template with fewer custom resources, so that deployments are more reliable and easier to debug.

#### Acceptance Criteria

1. THE frontend-stack.yaml SHALL define a single Custom_Resource for frontend deployment
2. THE Custom_Resource SHALL handle CREATE (deploy), UPDATE (redeploy), and DELETE (cleanup) operations
3. THE template SHALL remove the separate EmptyFrontendBucketResource custom resource
4. THE template SHALL remove the BucketCleanerFunctionArn parameter
5. THE DependsOn relationships SHALL be simplified to reflect the single custom resource architecture

### Requirement 13: Configurable Deployment Bucket

**User Story:** As a DevOps engineer, I want to optionally use an existing S3 bucket for frontend deployment, so that I can integrate with existing infrastructure or share buckets across environments.

#### Acceptance Criteria

1. THE frontend-stack.yaml SHALL accept an optional ExistingBucketName parameter
2. IF ExistingBucketName is empty or not provided, THEN THE template SHALL create a new bucket with name `{ProjectName}-fe-{AccountId}-{Environment}`
3. IF ExistingBucketName is provided, THEN THE template SHALL use the existing bucket instead of creating a new one
4. WHEN using an existing bucket, THE template SHALL NOT create the FrontendBucket resource
5. WHEN using an existing bucket, THE template SHALL NOT delete the bucket on stack deletion
6. THE Frontend_Deployer SHALL work identically regardless of whether the bucket is created or existing
7. THE template SHALL use CloudFormation Conditions to conditionally create the bucket resource
8. THE template outputs SHALL correctly reference either the created or existing bucket name

### Requirement 14: CI/CD Integration Support

**User Story:** As a DevOps engineer, I want CI/CD pipelines (GitHub Actions, GitLab CI, CodeBuild) to easily trigger frontend deployments without breaking the stack, so that development workflows are seamless.

#### Acceptance Criteria

1. THE frontend-stack.yaml SHALL accept a FrontendBuildTimestamp parameter that triggers redeployment when changed
2. WHEN FrontendBuildTimestamp changes, THE CloudFormation update SHALL only redeploy frontend content without modifying infrastructure
3. THE Frontend_Deployer SHALL be invokable directly via Lambda invoke for CI/CD pipelines that bypass CloudFormation
4. WHEN invoked directly, THE Frontend_Deployer SHALL accept the same parameters as the CloudFormation custom resource
5. THE Frontend_Deployer SHALL return success/failure status suitable for CI/CD pipeline integration
6. IF a CI/CD pipeline invokes Frontend_Deployer directly, THEN THE deployment SHALL NOT affect CloudFormation stack state
7. THE template SHALL export the Frontend_Deployer Lambda ARN for CI/CD pipeline configuration
8. WHEN invoked directly (not via CloudFormation), THE Frontend_Deployer SHALL skip all bucket cleanup logic since cleanup is only needed for stack deletion


### Requirement 15: Stack Integration Preservation

**User Story:** As a DevOps engineer, I want frontend deployment changes to not affect other stack integrations (Step Functions, EventBridge, API Gateway), so that the full solution remains functional after deployment.

#### Acceptance Criteria

1. THE frontend-stack.yaml changes SHALL NOT modify any outputs consumed by other stacks
2. THE Frontend_Deployer Lambda changes SHALL NOT affect the Lambda stack's other function definitions
3. WHEN the frontend stack is updated, THE master template's DependsOn relationships SHALL remain valid
4. THE frontend deployment changes SHALL be isolated to frontend-stack.yaml and frontend-deployer Lambda only
5. THE CloudFormation nested stack architecture SHALL continue to deploy all stacks in correct order (Database → Lambda → StepFunctions → API → EventBridge → Frontend)
6. AFTER frontend deployment changes, THE Step Functions state machine SHALL remain fully integrated with the orchestration Lambda
7. THE EventBridge rules for execution polling and tag sync SHALL continue to function after frontend changes


### Requirement 16: Deployment Parameter Preservation

**User Story:** As a DevOps engineer, I want all deployment parameters documented and preserved, so that the full stack can be redeployed with identical configuration.

#### Acceptance Criteria

1. THE implementation SHALL preserve all existing master-template.yaml parameters
2. THE deployment SHALL use the following stack configuration:
   - Stack Name: `aws-drs-orch-dev`
   - Project Name: `aws-drs-orch`
   - Environment: `dev`
   - AWS Region: `us-east-1`
   - Source/Deployment Bucket: `aws-drs-orch-dev`
3. THE deployment SHALL preserve the AdminEmail parameter from the previous stack
4. THE deployment SHALL preserve all Cognito configuration (UserPoolId, UserPoolClientId, IdentityPoolId)
5. THE deployment SHALL preserve all DynamoDB table names and configurations
6. THE deployment SHALL preserve all API Gateway configurations
7. THE deployment SHALL preserve all Step Functions state machine configurations
8. THE deployment SHALL preserve all EventBridge rule configurations
9. THE deploy.sh script SHALL be updated to reference the consolidated frontend-deployer Lambda
10. THE implementation notes SHALL document all parameters required for full stack redeployment


### Requirement 17: Execution Notification Functionality

**User Story:** As a DR operator, I want to receive email notifications for execution events, so that I am informed of DR operation status without monitoring the console.

#### Acceptance Criteria

1. THE master-template.yaml SHALL have an `EnableNotifications` parameter (true/false, default false)
2. WHEN EnableNotifications is true, THE stack SHALL send notifications to AdminEmail
3. THE notification-stack.yaml SHALL be simplified to use only AdminEmail (remove NotificationEmail parameter)
4. THE notification-formatter Lambda SHALL be kept and use `EnableNotifications` condition (not `EnablePipelineNotifications`)
5. THE Step Functions state machine SHALL invoke notification-formatter Lambda on execution start
6. THE Step Functions state machine SHALL invoke notification-formatter Lambda on execution completion (success or failure)
7. THE Step Functions state machine SHALL invoke notification-formatter Lambda on wave completion
8. THE Step Functions state machine SHALL invoke notification-formatter Lambda on execution pause (when protection group is paused for manual intervention)
9. THE EventBridge rules for DRS failures SHALL publish to DRSOperationalAlertsTopic (already configured)
10. THE PipelineNotificationsTopic SHALL be removed (CodePipeline remnant - separate from execution notifications)
11. THE ApprovalWorkflowTopic SHALL be repurposed as ExecutionPauseTopic for pause/resume notifications
12. WHEN EnableNotifications is false, THE stack SHALL NOT create SNS subscriptions but SHALL still create topics for programmatic use
13. THE notification-formatter Lambda SHALL format JSON events into human-readable emails with:
    - Clear subject lines with status emojis
    - Structured execution details (ID, plan name, status, timestamp)
    - Status-specific information (duration, errors, wave progress)
    - Console links for quick access
14. THE notification-formatter Lambda SHALL handle three notification types: execution, drs_alert, pause
15. THE pause notification SHALL include protection group name, pause reason, and instructions for resuming execution

#### Deployment Parameters Reference

The following parameters must be captured from the current/previous stack before redeployment:

**Required Parameters (from master-template.yaml):**
- `ProjectName`: aws-drs-orch
- `Environment`: dev
- `SourceBucket`: aws-drs-orch-dev
- `AdminEmail`: [capture from previous stack] - receives all notifications when enabled
- `EnableNotifications`: true/false - when enabled, sends execution and DRS event notifications to AdminEmail
- `CrossAccountRoleName`: Name of pre-existing cross-account role, or leave empty to create one

**Parameters to REMOVE from master-template.yaml:**
- `EnablePipelineNotifications`: CodePipeline remnant - replace with `EnableNotifications`
- `NotificationEmail`: Remove - simplify to just use AdminEmail for all notifications
- `EnableWAF`: Remove - WAF not implemented
- `EnableSecurityStack`: Remove - SecurityStack not developed
- `EnableSecretsManager`: Remove - unused parameter
- `EnableTerminationProtection`: Remove - unused parameter (set via CLI at stack creation)
- `EnableTagSync`: Remove parameter - hardcode to always enabled
- `ForceRecreation`: Remove - internal migration hack that could delete customer data if misused
- `EnableCloudTrail`: Remove - integrate CloudTrail by default (not optional)
- `TagSyncIntervalHours`: Remove - hardcode to 1 hour (internal deployment detail)
- `ApiDeploymentTimestamp`: Remove - internal deployment mechanism (deploy.sh handles this)
- `FrontendBuildTimestamp`: Remove - internal deployment mechanism (deploy.sh handles this)
- `CognitoDomainPrefix`: Remove - unused parameter (condition exists but never referenced)

**SNS Topics Architecture:**
- `ExecutionNotificationsTopic`: Execution start, completion, wave completion notifications
- `ExecutionPauseTopic`: Pause/resume notifications (repurposed from ApprovalWorkflowTopic)
- `DRSOperationalAlertsTopic`: DRS failure alerts from EventBridge rules
- REMOVE `PipelineNotificationsTopic`: CodePipeline remnant

**CloudTrail Integration:**
- CloudTrail should be integrated by default (not optional)
- Integrate CloudTrail logging directly into the stack

**Deployment Command:**
```bash
./scripts/deploy.sh dev
```
