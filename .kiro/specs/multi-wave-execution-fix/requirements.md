# Multi-Wave Execution Lifecycle Fix - Requirements

## Overview

Fix the critical bug where multi-wave DR executions are prematurely marked as COMPLETED after the first wave completes, preventing subsequent waves from executing. This fix includes consolidating the execution-finder and execution-poller Lambdas into the execution-handler to simplify the architecture and centralize execution lifecycle management.

## Problem Statement

**Current Behavior**:
- Architecture has 3 separate Lambdas: execution-handler, execution-finder, execution-poller
- Step Functions starts a 3-wave execution
- Step Functions creates wave 1 in DynamoDB and starts DRS job
- Execution-finder discovers executions in POLLING status
- Execution-poller polls wave 1 status from DRS
- Wave 1 completes successfully
- Execution-poller sees all waves in DynamoDB are complete (only wave 1 exists)
- Execution-poller calls `finalize_execution()` and marks execution as COMPLETED
- Step Functions is still RUNNING with waves 2 and 3 pending
- Waves 2 and 3 never execute

**Expected Behavior**:
- Single consolidated execution-handler Lambda manages all execution operations
- Step Functions orchestrates all waves through completion
- Execution-handler updates wave status without finalizing executions
- Step Functions finalizes execution after all waves complete
- Multi-wave executions with pause/resume work correctly
- Simplified architecture with fewer moving parts

## User Stories

### US-1: Consolidated Execution Handler
**As a** system architect  
**I want** execution-finder and execution-poller consolidated into execution-handler  
**So that** execution lifecycle management is centralized and simplified

**Acceptance Criteria**:
- AC-1.1: Execution-handler handles all execution operations (create, find, poll, update, finalize)
- AC-1.2: Execution-finder Lambda is removed from the system
- AC-1.3: Execution-poller Lambda is removed from the system
- AC-1.4: Step Functions calls single execution-handler with operation type
- AC-1.5: CloudFormation stack deploys only execution-handler Lambda

### US-2: Multi-Wave Execution Completion
**As a** DR operator  
**I want** multi-wave recovery plans to execute all waves sequentially  
**So that** complex DR scenarios with dependencies complete successfully

**Acceptance Criteria**:
- AC-2.1: Execution with 3 waves completes all 3 waves
- AC-2.2: Execution status remains POLLING or PAUSED between waves
- AC-2.3: Execution status changes to COMPLETED only after final wave completes
- AC-2.4: Each wave's status is tracked independently in DynamoDB
- AC-2.5: Step Functions state machine controls execution lifecycle

### US-3: Wave Status Updates Without Finalization
**As a** execution-handler Lambda  
**I want** to update wave status without finalizing executions  
**So that** Step Functions maintains control of the execution lifecycle

**Acceptance Criteria**:
- AC-3.1: Execution-handler updates wave status in DynamoDB
- AC-3.2: Execution-handler updates `lastPolledTime` for adaptive polling
- AC-3.3: Execution-handler NEVER calls `finalize_execution()` during polling
- AC-3.4: Execution-handler logs wave completion without changing execution status
- AC-3.5: Execution status remains unchanged by polling operations

### US-3A: Server Data Enrichment During Polling
**As a** DR operator  
**I want** server data enriched with current DRS and EC2 state during polling  
**So that** I can see real-time recovery progress and instance details

**Acceptance Criteria**:
- AC-3A.1: Execution-handler queries DRS for current server status during each poll
- AC-3A.2: Execution-handler queries EC2 for instance details when instances are launched
- AC-3A.3: Server data includes: sourceServerId, serverName, launchStatus, launchTime
- AC-3A.4: Server data includes: instanceId, privateIp, hostname, instanceType (when available)
- AC-3A.5: Server data is normalized and stored in DynamoDB `serverStatuses` field
- AC-3A.6: Frontend displays enriched server data in real-time
- AC-3A.7: DRS job data includes: jobId, status, participatingServers, startTime, endTime

### US-4: Step Functions Execution Finalization
**As a** Step Functions state machine  
**I want** to finalize executions when all waves complete  
**So that** execution lifecycle is controlled by the orchestrator

**Acceptance Criteria**:
- AC-4.1: Step Functions checks if all waves are complete
- AC-4.2: Step Functions calls execution-handler finalize operation when all waves complete
- AC-4.3: Execution-handler updates execution status to COMPLETED
- AC-4.4: Execution-handler handles finalization errors gracefully
- AC-4.5: Finalization occurs only once per execution

### US-5: Pause/Resume Between Waves
**As a** DR operator  
**I want** executions to pause between waves when configured  
**So that** I can validate each wave before proceeding

**Acceptance Criteria**:
- AC-5.1: Execution pauses after wave completes if `pauseBeforeWave: true` for next wave
- AC-5.2: Execution status changes to PAUSED
- AC-5.3: Execution remains PAUSED until manual resume
- AC-5.4: Resume operation creates next wave and continues execution
- AC-5.5: Execution status changes from PAUSED to POLLING when resumed

### US-6: Frontend Status Display
**As a** DR operator viewing the frontend  
**I want** to see accurate execution status during multi-wave operations  
**So that** I understand the current state of the DR operation

**Acceptance Criteria**:
- AC-6.1: Frontend shows POLLING status while waves are executing
- AC-6.2: Frontend shows PAUSED status between waves
- AC-6.3: Frontend shows COMPLETED status only after all waves complete
- AC-6.4: Frontend displays current wave number and total waves
- AC-6.5: Frontend shows individual wave statuses

### US-7: CloudFormation Template Updates
**As a** DevOps engineer  
**I want** CloudFormation templates updated to support the consolidated architecture  
**So that** infrastructure deployment reflects the new single-Lambda design

**Acceptance Criteria**:
- AC-7.1: Lambda stack defines execution-handler with appropriate memory and timeout
- AC-7.2: Lambda stack removes execution-finder and execution-poller definitions
- AC-7.3: Step Functions state machine calls execution-handler with operation parameter
- AC-7.4: API Gateway endpoints route to execution-handler
- AC-7.5: EventBridge rules trigger execution-handler for polling
- AC-7.6: IAM roles grant execution-handler all necessary permissions (DRS, EC2, DynamoDB)
- AC-7.7: CloudFormation stack updates deploy without downtime
- AC-7.8: Old Lambda functions are cleanly removed after successful deployment

## Functional Requirements

### FR-1: Consolidated Execution Handler
- FR-1.1: Execution-handler SHALL support multiple operation types via `operation` parameter
- FR-1.2: Execution-handler SHALL handle: `create`, `find`, `poll`, `update`, `finalize`, `pause`, `resume`
- FR-1.3: Execution-handler SHALL route to appropriate function based on operation type
- FR-1.4: Execution-handler SHALL maintain backward compatibility with existing API contracts
- FR-1.5: Execution-handler SHALL replace execution-finder and execution-poller Lambdas

### FR-2: Polling Operation Behavior
- FR-2.1: Poll operation SHALL query DRS job status for active waves
- FR-2.2: Poll operation SHALL update wave status in DynamoDB
- FR-2.3: Poll operation SHALL update `lastPolledTime` timestamp
- FR-2.4: Poll operation SHALL NOT modify execution status
- FR-2.5: Poll operation SHALL NOT call finalize operation
- FR-2.6: Poll operation SHALL enrich server data with current DRS state
- FR-2.7: Poll operation SHALL enrich server data with EC2 instance details when available
- FR-2.8: Poll operation SHALL normalize all DRS response data before storing
- FR-2.9: Poll operation SHALL update `serverStatuses` field with enriched data
- FR-2.10: Poll operation SHALL handle missing or incomplete data gracefully

### FR-3: Server Data Enrichment
- FR-3.1: Enrichment SHALL query DRS DescribeRecoveryInstances API for each server
- FR-3.2: Enrichment SHALL query EC2 DescribeInstances API when instanceId is available
- FR-3.3: Enrichment SHALL extract: sourceServerId, serverName, launchStatus, launchTime from DRS
- FR-3.4: Enrichment SHALL extract: instanceId, privateIp, hostname, instanceType from EC2
- FR-3.5: Enrichment SHALL normalize PascalCase fields to camelCase
- FR-3.6: Enrichment SHALL handle API throttling and rate limits
- FR-3.7: Enrichment SHALL cache EC2 data to minimize API calls
- FR-3.8: Enrichment SHALL update server data on every poll cycle

### FR-4: Step Functions Orchestration
- FR-4.1: Step Functions SHALL maintain list of all waves in execution state
- FR-4.2: Step Functions SHALL create waves sequentially in DynamoDB
- FR-4.3: Step Functions SHALL monitor wave completion status
- FR-4.4: Step Functions SHALL pause execution if `pauseBeforeWave: true`
- FR-4.5: Step Functions SHALL call finalize operation when all waves complete

### FR-5: Execution Finalization
- FR-5.1: Finalize operation SHALL occur only when all waves are COMPLETED
- FR-5.2: Finalize operation SHALL update execution status to COMPLETED
- FR-5.3: Finalize operation SHALL update `completedTime` timestamp
- FR-5.4: Finalize operation SHALL be idempotent (safe to call multiple times)
- FR-5.5: Finalize operation SHALL be triggered only by Step Functions

### FR-6: Wave Status Tracking
- FR-6.1: Each wave SHALL have independent status in DynamoDB
- FR-6.2: Wave statuses SHALL include: PENDING, POLLING, COMPLETED, FAILED
- FR-6.3: Execution record SHALL track `totalWaves` count
- FR-6.4: Execution record SHALL track `completedWaves` count
- FR-6.5: Wave completion SHALL not affect execution status during polling

### FR-7: Pause/Resume Operations
- FR-7.1: Pause operation SHALL occur after wave completion if configured
- FR-7.2: Pause operation SHALL change execution status to PAUSED
- FR-7.3: Resume operation SHALL create next wave in DynamoDB
- FR-7.4: Resume operation SHALL change execution status to POLLING
- FR-7.5: Resume operation SHALL be triggered by API call or Step Functions

### FR-8: CloudFormation Infrastructure Updates
- FR-8.1: Lambda stack SHALL define single execution-handler Lambda function
- FR-8.2: Lambda stack SHALL remove execution-finder Lambda function definition
- FR-8.3: Lambda stack SHALL remove execution-poller Lambda function definition
- FR-8.4: Step Functions stack SHALL update all task definitions to call execution-handler
- FR-8.5: Step Functions stack SHALL pass `operation` parameter to execution-handler
- FR-8.6: API Gateway stack SHALL update endpoints to route to execution-handler
- FR-8.7: EventBridge stack SHALL update rules to trigger execution-handler
- FR-8.8: IAM roles SHALL grant execution-handler permissions for DRS, EC2, DynamoDB
- FR-8.9: CloudFormation outputs SHALL export execution-handler ARN only
- FR-8.10: Deployment SHALL be backward compatible during transition period

## Non-Functional Requirements

### NFR-1: Reliability
- NFR-1.1: Multi-wave executions SHALL complete successfully 99%+ of the time
- NFR-1.2: Execution status SHALL be consistent between Step Functions and DynamoDB
- NFR-1.3: Wave status updates SHALL be atomic operations
- NFR-1.4: Finalization SHALL handle concurrent calls safely

### NFR-2: Performance
- NFR-2.1: Wave status updates SHALL complete within 500ms
- NFR-2.2: Execution finalization SHALL complete within 1 second
- NFR-2.3: Polling interval SHALL adapt based on wave status
- NFR-2.4: Step Functions SHALL not exceed AWS service quotas

### NFR-3: Observability
- NFR-3.1: All wave status changes SHALL be logged
- NFR-3.2: Execution finalization SHALL be logged with all wave statuses
- NFR-3.3: Poller SHALL log when waves complete without finalizing
- NFR-3.4: Step Functions SHALL emit CloudWatch metrics for wave completion

### NFR-4: Maintainability
- NFR-4.1: Execution lifecycle logic SHALL be centralized in Step Functions
- NFR-4.2: Poller SHALL have single responsibility (status updates only)
- NFR-4.3: Finalization logic SHALL be reusable across handlers
- NFR-4.4: Code SHALL include clear comments explaining lifecycle management

## Technical Constraints

### TC-1: Architecture
- TC-1.1: Must work with existing decomposed Lambda architecture
- TC-1.2: Must maintain compatibility with single-wave executions
- TC-1.3: Must not break existing API contracts
- TC-1.4: Must use existing DynamoDB table schema

### TC-2: AWS Services
- TC-2.1: Step Functions execution time limit: 1 year
- TC-2.2: DynamoDB conditional writes for atomic updates
- TC-2.3: Lambda timeout: 15 minutes maximum
- TC-2.4: CloudWatch Logs retention: 30 days

### TC-3: Backward Compatibility
- TC-3.1: Must support existing single-wave executions
- TC-3.2: Must not require DynamoDB schema changes
- TC-3.3: Must work with existing frontend code
- TC-3.4: Must maintain existing API response formats

## Success Metrics

### SM-1: Functional Success
- Multi-wave executions complete all waves: 100%
- Execution status accuracy: 100%
- Pause/resume operations work: 100%
- No premature finalization: 100%

### SM-2: Performance Success
- Wave status update latency: <500ms p95
- Execution finalization latency: <1s p95
- Step Functions execution success rate: >99%
- No execution timeouts

### SM-3: Operational Success
- Zero production incidents from premature finalization
- Clear audit trail in CloudWatch Logs
- Frontend displays accurate status
- DR operators can pause/resume successfully

## Out of Scope

- Changes to DynamoDB table schema
- Changes to frontend UI components (beyond consuming existing API data)
- Migration of existing completed executions
- Retry logic for failed waves (separate feature)
- Wave dependency management (separate feature)
- Changes to API Gateway endpoint paths or request/response formats
- Changes to authentication/authorization mechanisms

## Dependencies

- Existing execution-handler Lambda function (to be enhanced)
- Existing execution-poller Lambda function (to be consolidated)
- Existing execution-finder Lambda function (to be consolidated)
- Existing Step Functions state machine definition (to be updated)
- Existing DynamoDB execution table
- #[[file:infra/orchestration/drs-orchestration/lambda/shared/drs_utils.py]] - DRS normalization utilities (to be enhanced with EC2 enrichment)
- Existing API handler functions
- CloudFormation templates:
  - `cfn/lambda-stack.yaml` (Lambda function definitions)
  - `cfn/step-functions-stack.yaml` (Step Functions state machine)
  - `cfn/api-gateway-*-stack.yaml` (API Gateway endpoints)
  - `cfn/eventbridge-stack.yaml` (EventBridge rules)

## Risks and Mitigations

### Risk 1: Breaking Single-Wave Executions
**Mitigation**: Comprehensive testing of single-wave scenarios, maintain backward compatibility

### Risk 2: Race Conditions in Status Updates
**Mitigation**: Use DynamoDB conditional writes, implement idempotent operations

### Risk 3: Step Functions Timeout
**Mitigation**: Use wait states with heartbeat, implement proper error handling

### Risk 4: Incomplete Wave Data
**Mitigation**: Validate wave data before finalization, log all state transitions

## References

- Multi-Wave Bug Analysis: `.kiro/specs/missing-function-migration/MULTI_WAVE_BUG_ANALYSIS.md`
- Normalization Bug Summary: `.kiro/specs/missing-function-migration/NORMALIZATION_BUG_SUMMARY.md`
- Reference Stack: `aws-elasticdrs-orchestrator-test`
- Execution ID: `0754e970-3f18-4cc4-9091-3bed3983d56f`
