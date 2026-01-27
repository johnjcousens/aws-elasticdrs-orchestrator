# Requirements Document

## Introduction

The frontend execution details UI is not displaying wave progress, server status, or DRS job events even though the execution poller is correctly updating DynamoDB with complete data. After the API handler decomposition (AWSM-1103), the UI shows "No DRS job events available yet" for all executions, preventing users from monitoring DR recovery progress.

This issue breaks a critical monitoring capability - users cannot see real-time progress of their disaster recovery executions, which is essential for validating recovery operations and troubleshooting failures.

## Glossary

- **Execution**: A single run of a Recovery Plan, containing one or more waves
- **Wave**: A group of servers that are recovered together in a specific order
- **DRS Job**: AWS Elastic Disaster Recovery job that launches recovery instances
- **Job Events**: Detailed progress events from DRS (SNAPSHOT_START, CONVERSION_START, LAUNCH_START, etc.)
- **Server Status**: Current state of each server in a wave (PENDING, LAUNCHING, LAUNCHED, FAILED)
- **Execution Poller**: Background Lambda function that polls DRS and updates DynamoDB with execution progress
- **ExecutionDetails Component**: React component that displays execution progress in a modal dialog
- **API Client**: Frontend service layer that makes HTTP requests to the backend API Gateway
- **Execution Handler**: Backend Lambda function that handles execution-related API requests
- **Query Handler**: Backend Lambda function that handles read-only query operations

## Requirements

### Requirement 1: Display Wave Progress

**User Story:** As a DR operator, I want to see wave-by-wave progress of my execution, so that I can monitor which waves have completed and which are in progress.

#### Acceptance Criteria

1. WHEN an execution has wave data in DynamoDB, THE ExecutionDetails Component SHALL display all waves with their status
2. WHEN a wave is in progress, THE ExecutionDetails Component SHALL show the wave number, status, and server count
3. WHEN a wave is completed, THE ExecutionDetails Component SHALL show completion time and final status
4. WHEN wave data exists in DynamoDB, THE Frontend SHALL fetch and display it without showing "No DRS job events available yet"

### Requirement 2: Display Server Status

**User Story:** As a DR operator, I want to see the status of each server in each wave, so that I can identify which servers are launching successfully and which are failing.

#### Acceptance Criteria

1. WHEN a wave contains server status data, THE ExecutionDetails Component SHALL display each server with its current status
2. WHEN a server status changes, THE ExecutionDetails Component SHALL reflect the updated status after the next poll
3. WHEN a server has a launch status, THE ExecutionDetails Component SHALL display the DRS launch status (PENDING, LAUNCHING, LAUNCHED, FAILED)
4. WHEN server data exists in DynamoDB under serverStatuses array, THE Frontend SHALL extract and display it correctly

### Requirement 3: Display DRS Job Events

**User Story:** As a DR operator, I want to see detailed DRS job events, so that I can understand the progress of snapshot creation, conversion, and instance launch operations.

#### Acceptance Criteria

1. WHEN DRS job events are available, THE ExecutionDetails Component SHALL display them in chronological order
2. WHEN job events include errors, THE ExecutionDetails Component SHALL highlight error events
3. WHEN the execution has multiple waves, THE ExecutionDetails Component SHALL group job events by wave
4. WHEN job log data is available from the API, THE Frontend SHALL parse and display it without errors

### Requirement 4: Real-Time Updates

**User Story:** As a DR operator, I want the execution details to update automatically, so that I can see progress without manually refreshing.

#### Acceptance Criteria

1. WHEN an execution is in progress, THE ExecutionDetails Component SHALL poll for updates every 5 seconds
2. WHEN new wave or server data is available, THE ExecutionDetails Component SHALL update the display without user action
3. WHEN an execution completes, THE ExecutionDetails Component SHALL stop polling
4. WHEN the poller updates DynamoDB, THE Frontend SHALL fetch the updated data on the next poll cycle

### Requirement 5: API Data Structure Compatibility

**User Story:** As a developer, I want the frontend to correctly parse the API response structure, so that execution data displays properly after the API decomposition.

#### Acceptance Criteria

1. WHEN the API returns execution data, THE Frontend SHALL correctly parse the waves array structure
2. WHEN wave data includes serverStatuses, THE Frontend SHALL extract server information from the correct field name
3. WHEN the API returns job logs, THE Frontend SHALL correctly parse the jobLogs array structure
4. WHEN field names differ between DynamoDB and the frontend types, THE Frontend SHALL map them correctly

### Requirement 6: Error Handling

**User Story:** As a DR operator, I want clear error messages when execution details cannot be loaded, so that I can understand what went wrong and take appropriate action.

#### Acceptance Criteria

1. WHEN the API request fails, THE ExecutionDetails Component SHALL display a user-friendly error message
2. WHEN execution data is missing required fields, THE Frontend SHALL handle it gracefully without crashing
3. WHEN job logs cannot be fetched, THE ExecutionDetails Component SHALL show execution details without job logs
4. WHEN the execution is not found, THE Frontend SHALL display "Execution not found" instead of "No DRS job events available yet"

### Requirement 7: Backward Compatibility

**User Story:** As a system maintainer, I want the fix to work with existing execution data, so that historical executions display correctly.

#### Acceptance Criteria

1. WHEN viewing an execution created before the fix, THE Frontend SHALL display available data without errors
2. WHEN execution data uses old field names, THE Frontend SHALL map them to new field names
3. WHEN wave data is missing optional fields, THE Frontend SHALL use sensible defaults
4. WHEN the API response structure changes, THE Frontend SHALL handle both old and new formats

### Requirement 8: Data Source Transparency

**User Story:** As a DR operator, I want to know if I'm viewing cached or real-time data, so that I can understand the freshness of the information.

#### Acceptance Criteria

1. WHEN execution data is from DynamoDB cache, THE ExecutionDetails Component SHALL indicate "cached" data source
2. WHEN execution data includes real-time DRS queries, THE ExecutionDetails Component SHALL indicate "real-time" data source
3. WHEN the last update timestamp is available, THE ExecutionDetails Component SHALL display it
4. WHEN polling is active, THE ExecutionDetails Component SHALL show a visual indicator
