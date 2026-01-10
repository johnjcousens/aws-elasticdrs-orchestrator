# Requirements Document

## Introduction

The AWS DRS Orchestration execution polling system was functional from December 20-27, 2025 and January 6, 2026, but broke after restoration from January 6th commits. Systematic analysis of 322 commits reveals the root causes and required fixes to restore functionality.

## Glossary

- **Execution_Poller**: Lambda function that polls DRS job status and updates execution progress
- **Execution_Finder**: EventBridge-triggered Lambda that finds executions needing polling
- **Orchestration_Lambda**: Step Functions Lambda that initiates DRS recovery jobs
- **Reconcile_Function**: Critical function that reconciled stale wave statuses with actual DRS results (REMOVED on Jan 7, 2026)
- **Wave_Status**: Status of individual recovery waves (STARTED, POLLING, LAUNCHED, completed, failed)
- **Execution_Status**: Overall execution status (RUNNING, POLLING, COMPLETED, FAILED, CANCELLED)
- **DRS_Job**: AWS DRS recovery job with unique job ID and status

## Requirements

### Requirement 1: Restore Missing Reconcile Function

**User Story:** As a system operator, I want the execution polling system to automatically reconcile stale wave statuses with actual DRS job results, so that executions show correct status even when polling fails.

#### Acceptance Criteria

1. WHEN the API handler processes a get_execution_details request, THE System SHALL call reconcile_wave_status_with_drs function for each wave
2. WHEN a wave has status in ["UNKNOWN", "", "STARTED", "INITIATED", "POLLING", "LAUNCHING", "IN_PROGRESS"] and has a JobId, THE Reconcile_Function SHALL query DRS for actual job status
3. WHEN DRS job status is "COMPLETED" and all participating servers have launchStatus "LAUNCHED", THE Reconcile_Function SHALL update wave status to "completed" and set EndTime
4. WHEN DRS job status is "FAILED", THE Reconcile_Function SHALL update wave status to "failed" and set EndTime
5. WHEN wave status is updated by reconcile function, THE System SHALL save the updated wave to DynamoDB immediately

### Requirement 2: Fix Status Transition Flow

**User Story:** As a system operator, I want executions to properly transition from RUNNING to POLLING status after DRS job creation, so that execution-finder can discover and poll them.

#### Acceptance Criteria

1. WHEN orchestration Lambda creates a DRS recovery job successfully, THE System SHALL update execution status from "RUNNING" to "POLLING"
2. WHEN execution status is set to "POLLING", THE System SHALL save the updated execution to DynamoDB immediately
3. WHEN execution-finder runs every minute, THE System SHALL find all executions with status ["POLLING", "CANCELLING"]
4. WHEN execution-finder finds polling executions, THE System SHALL trigger execution-poller for each execution
5. WHEN execution-poller completes successfully, THE System SHALL update wave and execution statuses based on DRS job results

### Requirement 3: Validate Execution-Finder EventBridge Integration

**User Story:** As a system operator, I want execution-finder to run automatically every minute via EventBridge, so that polling executions are discovered and processed continuously.

#### Acceptance Criteria

1. WHEN EventBridge rule triggers every minute, THE Execution_Finder SHALL execute successfully
2. WHEN execution-finder executes, THE System SHALL log the number of executions found with POLLING status
3. WHEN execution-finder finds executions to poll, THE System SHALL invoke execution-poller Lambda for each execution
4. WHEN execution-finder encounters errors, THE System SHALL log detailed error information for debugging
5. WHEN no executions need polling, THE Execution_Finder SHALL complete successfully without errors

### Requirement 4: Validate Execution-Poller Lambda Packaging

**User Story:** As a system operator, I want execution-poller Lambda to be properly packaged and deployed, so that it can execute without 502 errors or import failures.

#### Acceptance Criteria

1. WHEN execution-poller Lambda is invoked, THE System SHALL execute without 502 HTTP errors
2. WHEN execution-poller imports required modules, THE System SHALL find all dependencies in the deployment package
3. WHEN execution-poller queries DRS APIs, THE System SHALL have proper IAM permissions for all required DRS operations
4. WHEN execution-poller updates DynamoDB, THE System SHALL have proper IAM permissions for table write operations
5. WHEN execution-poller encounters errors, THE System SHALL log detailed error information and return proper error responses

### Requirement 5: Restore Wave Status Reconciliation Logic

**User Story:** As a system operator, I want wave statuses to be automatically reconciled with actual DRS job results, so that the frontend displays accurate execution progress.

#### Acceptance Criteria

1. WHEN a wave has JobId and stale status, THE Reconcile_Function SHALL query DRS describe_jobs API for actual job status
2. WHEN DRS job shows COMPLETED status, THE Reconcile_Function SHALL check all participating servers for LAUNCHED status
3. WHEN all servers are LAUNCHED, THE Reconcile_Function SHALL update wave status to "completed" and set EndTime to current timestamp
4. WHEN any server failed to launch, THE Reconcile_Function SHALL update wave status to "failed" and set EndTime to current timestamp
5. WHEN wave status is updated, THE Reconcile_Function SHALL save the complete wave object to DynamoDB with updated Status and EndTime

### Requirement 6: Validate Cross-Account DRS Permissions

**User Story:** As a system operator, I want the execution polling system to work across multiple AWS accounts, so that cross-account DRS operations are properly monitored and updated.

#### Acceptance Criteria

1. WHEN execution involves cross-account DRS operations, THE System SHALL assume proper cross-account roles for DRS API calls
2. WHEN querying DRS job status in target accounts, THE System SHALL have describe_jobs permissions in each target account
3. WHEN updating execution status, THE System SHALL handle cross-account authentication errors gracefully
4. WHEN cross-account operations fail, THE System SHALL log detailed error information including account ID and region
5. WHEN cross-account roles are missing or invalid, THE System SHALL return descriptive error messages for troubleshooting

### Requirement 7: Implement Execution Status Timeout Handling

**User Story:** As a system operator, I want executions to timeout appropriately based on realistic DRS operation timeframes, so that stuck executions are properly handled.

#### Acceptance Criteria

1. WHEN calculating execution timeout, THE System SHALL use 31,536,000 seconds (1 year) as the maximum timeout period
2. WHEN an execution exceeds the timeout period, THE System SHALL mark the execution as "TIMEOUT" status
3. WHEN marking execution as timeout, THE System SHALL preserve the ability to resume the execution if DRS jobs are still active
4. WHEN timeout occurs, THE System SHALL log the timeout event with execution ID and duration
5. WHEN checking for timeout, THE System SHALL compare current time against execution StartTime plus timeout period

### Requirement 8: Validate Frontend Real-Time Polling Integration

**User Story:** As a frontend user, I want to see real-time execution progress updates, so that I can monitor DRS recovery operations as they progress.

#### Acceptance Criteria

1. WHEN frontend polls for execution details every 3 seconds, THE API SHALL return current execution and wave statuses
2. WHEN wave statuses are reconciled by the reconcile function, THE Frontend SHALL display the updated statuses immediately
3. WHEN execution completes successfully, THE Frontend SHALL show all waves as "completed" with proper timestamps
4. WHEN execution fails, THE Frontend SHALL show failed waves with error details
5. WHEN execution is paused, THE Frontend SHALL show PAUSED status and enable resume functionality

### Requirement 9: Implement Comprehensive Error Handling and Logging

**User Story:** As a system operator, I want comprehensive error handling and logging throughout the execution polling system, so that issues can be quickly diagnosed and resolved.

#### Acceptance Criteria

1. WHEN any component of the execution polling system encounters an error, THE System SHALL log detailed error information including function name, execution ID, and error details
2. WHEN DRS API calls fail, THE System SHALL log the specific DRS error code and message
3. WHEN DynamoDB operations fail, THE System SHALL log the table name and operation type
4. WHEN Lambda functions fail, THE System SHALL return proper HTTP status codes and error messages
5. WHEN debugging execution issues, THE System SHALL provide sufficient log information to trace the complete execution flow

### Requirement 10: Validate Step Functions Integration

**User Story:** As a system operator, I want Step Functions orchestration to properly integrate with the execution polling system, so that pause/resume functionality works correctly.

#### Acceptance Criteria

1. WHEN Step Functions execution is paused, THE System SHALL preserve PAUSED status and prevent status recalculation
2. WHEN Step Functions execution is resumed, THE System SHALL restore POLLING status and continue monitoring
3. WHEN Step Functions uses waitForTaskToken pattern, THE System SHALL support up to 1 year pause duration
4. WHEN Step Functions execution completes, THE System SHALL update final execution status appropriately
5. WHEN Step Functions execution fails, THE System SHALL mark execution as FAILED and log error details