# Software Requirements Specification (SRS)
# AWS DRS Orchestration System

**Version**: 1.0  
**Date**: November 12, 2025  
**Status**: Production Release (MVP Complete)  
**Document Owner**: Requirements Engineering Team  
**Target Audience**: Software Engineers, QA Engineers, Product Managers, Business Analysts

---

## Document Purpose

This Software Requirements Specification (SRS) defines the complete functional and non-functional requirements for the AWS DRS Orchestration system. It serves as the authoritative source for what the system must do (functional requirements) and how well it must do it (non-functional requirements).

**Key Objective**: Enable engineers and stakeholders to understand system capabilities, validate implementations, and plan testing strategies.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Scope & Context](#scope--context)
3. [Functional Requirements](#functional-requirements)
4. [User Stories & Acceptance Criteria](#user-stories--acceptance-criteria)
5. [Use Cases](#use-cases)
6. [Non-Functional Requirements](#non-functional-requirements)
7. [API Specifications](#api-specifications)
8. [Data Requirements](#data-requirements)
9. [Validation Rules](#validation-rules)
10. [Requirements Traceability](#requirements-traceability)

---

## Executive Summary

### Requirements Overview

This SRS specifies 87 functional requirements across 6 major feature areas:
1. **Protection Groups** (16 requirements) - Server grouping and management
2. **Recovery Plans** (24 requirements) - Wave-based recovery orchestration
3. **Execution Engine** (18 requirements) - Recovery execution and monitoring
4. **Server Discovery** (8 requirements) - DRS server integration
5. **Authentication & Authorization** (11 requirements) - User management
6. **Audit & Monitoring** (10 requirements) - Logging and compliance

### Requirements Status

| Category | Total | Implemented | Tested | Status |
|----------|-------|-------------|--------|--------|
| Functional | 87 | 83 (95%) | 13 (15%) | ⚠️ Testing needed |
| Non-Functional | 32 | 30 (94%) | 8 (25%) | ⚠️ Testing needed |
| **Total** | **119** | **113 (95%)** | **21 (18%)** | **⚠️ Testing Gap** |

**Critical Gap**: Execution Engine untested (0% coverage) - highest priority for next phase.

---

## Scope & Context

### In Scope

1. **Protection Group Management**: CRUD operations, server assignment, tag filtering
2. **Recovery Plan Management**: Wave configuration, dependencies, parallel/sequential execution
3. **Recovery Execution**: Drill/production modes, wave orchestration, health checks
4. **Server Discovery**: DRS API integration, automatic server detection
5. **User Management**: Cognito authentication, JWT token authorization
6. **Audit Trail**: CloudWatch Logs, CloudTrail integration, execution history

### Out of Scope (Phase 2+)

1. **Pre/Post Recovery Scripts**: Lambda hooks, SSM document execution
2. **Test Isolation**: VPC isolation for drill executions
3. **Automated Rollback**: Auto-rollback on failure detection
4. **Advanced Scheduling**: Cron-based scheduled recoveries
5. **Multi-Tenancy**: Customer isolation, tenant management
6. **Advanced Reporting**: Custom dashboards, compliance reports

---

## Functional Requirements

### FR-1: Protection Group Management

#### FR-1.1: Create Protection Group

**Requirement ID**: FR-PG-001  
**Priority**: Critical  
**Status**: ✅ Implemented, ⚠️ Needs Testing

**Description**: The system shall allow users to create a Protection Group by specifying a unique name, AWS region, optional description, optional tags, and a list of DRS source server IDs.

**Acceptance Criteria**:
- AC-001: User provides required fields: name (string, 1-128 chars), region (valid AWS region)
- AC-002: Name must be globally unique (case-insensitive across all Protection Groups)
- AC-003: Server IDs must exist in DRS API for the specified region
- AC-004: Server IDs cannot already be assigned to another Protection Group
- AC-005: System generates unique UUID as Protection Group ID
- AC-006: System records creation timestamp (Unix epoch seconds)
- AC-007: System stores Protection Group in DynamoDB with 100ms response time (p95)
- AC-008: System returns 201 Created with full Protection Group data on success
- AC-009: System returns 400 Bad Request if validation fails with specific error message
- AC-010: System returns 409 Conflict if name already exists or server already assigned

**Input Validation**:
```
name: required, string, min=1, max=128, alphanumeric + spaces/hyphens/underscores
region: required, enum [us-east-1, us-east-2, us-west-1, us-west-2, eu-west-1, ...]
description: optional, string, max=512
tags: optional, map<string, string>, max=50 entries
serverIds: required, array<string>, min=1, max=200, pattern=s-[a-f0-9]{17}
```

**Preconditions**:
- User authenticated with valid JWT token
- User has "drs-orchestration:CreateProtectionGroup" permission

**Postconditions**:
- Protection Group created in DynamoDB
- Servers marked as "assigned" to this Protection Group
- CloudWatch log entry created: "Created Protection Group: {name}"
- CloudTrail API call logged for compliance

**Error Scenarios**:
| Error | HTTP Code | Message |
|-------|-----------|---------|
| Duplicate name (case-insensitive) | 409 | "Protection Group name 'X' already exists" |
| Server already assigned | 409 | "Server 's-123' is already assigned to Protection Group 'Y'" |
| Server not found in DRS | 400 | "Server 's-123' not found in AWS DRS for region us-east-1" |
| Invalid region | 400 | "Region 'invalid' is not a valid AWS region" |
| Name too long | 400 | "Name exceeds maximum length of 128 characters" |

---

#### FR-1.2: List Protection Groups

**Requirement ID**: FR-PG-002  
**Priority**: Critical  
**Status**: ✅ Implemented, ✅ Tested

**Description**: The system shall return a list of all Protection Groups accessible to the authenticated user.

**Acceptance Criteria**:
- AC-001: Returns array of Protection Group objects (id, name, region, serverIds, createdAt, updatedAt)
- AC-002: Results sorted by creation date descending (newest first)
- AC-003: Empty array returned if no Protection Groups exist
- AC-004: Response time < 200ms for up to 100 Protection Groups
- AC-005: Includes server count per Protection Group
- AC-006: No pagination required for MVP (<1000 Protection Groups expected)

**API Response Example**:
```json
{
  "success": true,
  "data": [
    {
      "id": "d0441093-51e6-4e8f-989d-79b608ae97dc",
      "name": "Production-Database",
      "region": "us-east-1",
      "description": "Production Oracle and SQL Server databases",
      "serverIds": ["s-123", "s-456"],
      "serverCount": 2,
      "createdAt": 1699999999,
      "updatedAt": 1700000000
    }
  ]
}
```

---

#### FR-1.3: Get Single Protection Group

**Requirement ID**: FR-PG-003  
**Priority**: Critical  
**Status**: ✅ Implemented, ✅ Tested

**Description**: The system shall return detailed information for a specific Protection Group by ID.

**Acceptance Criteria**:
- AC-001: Accepts Protection Group ID as path parameter
- AC-002: Returns complete Protection Group object with all fields
- AC-003: Includes list of server IDs and server metadata (hostname, IP, status)
- AC-004: Returns 404 Not Found if Protection Group doesn't exist
- AC-005: Response time < 100ms (p95)

---

#### FR-1.4: Update Protection Group

**Requirement ID**: FR-PG-004  
**Priority**: High  
**Status**: ✅ Implemented, ⚠️ Needs Testing

**Description**: The system shall allow users to update an existing Protection Group's mutable fields: description, tags, and server assignments.

**Acceptance Criteria**:
- AC-001: Can update description (max 512 chars)
- AC-002: Can add/remove tags (max 50 key-value pairs)
- AC-003: Can add servers (if not assigned elsewhere)
- AC-004: Can remove servers (if not in active Recovery Plan execution)
- AC-005: Cannot update name or region (immutable fields)
- AC-006: System validates server availability before assignment
- AC-007: System updates UpdatedAt timestamp
- AC-008: Returns 409 Conflict if trying to add already-assigned server
- AC-009: Returns 400 Bad Request if trying to update immutable field

**Partial Update Example**:
```json
PUT /protection-groups/{id}
{
  "description": "Updated description",
  "serverIds": ["s-123", "s-456", "s-789"]  // Add s-789
}
```

---

#### FR-1.5: Delete Protection Group

**Requirement ID**: FR-PG-005  
**Priority**: High  
**Status**: ✅ Implemented, ⚠️ Needs Testing

**Description**: The system shall allow users to delete a Protection Group if it's not currently referenced by any Recovery Plans.

**Acceptance Criteria**:
- AC-001: Accepts Protection Group ID as path parameter
- AC-002: Checks if Protection Group is referenced by any Recovery Plans
- AC-003: Returns 409 Conflict if referenced by active Recovery Plans with list of plans
- AC-004: Soft-deletes Protection Group from DynamoDB (marks deleted, retains for 30 days)
- AC-005: Releases server assignments (servers become available for reassignment)
- AC-006: Returns 204 No Content on successful deletion
- AC-007: Returns 404 Not Found if Protection Group doesn't exist

**Error Response**:
```json
{
  "success": false,
  "error": {
    "message": "Cannot delete Protection Group 'Database' - referenced by 2 active Recovery Plans",
    "code": "PROTECTION_GROUP_IN_USE",
    "details": {
      "referencedBy": [
        {"planId": "plan-123", "planName": "Production-3Tier"},
        {"planId": "plan-456", "planName": "DR-Test"}
      ]
    }
  }
}
```

---

#### FR-1.6: Server Assignment Validation

**Requirement ID**: FR-PG-006  
**Priority**: Critical  
**Status**: ✅ Implemented, ⚠️ Needs Testing

**Description**: The system shall enforce that each DRS source server can be assigned to at most one Protection Group at any given time (globally unique constraint).

**Acceptance Criteria**:
- AC-001: When creating/updating Protection Group, system scans all existing Protection Groups
- AC-002: Checks if any provided server ID already exists in another Protection Group
- AC-003: Returns specific error identifying conflicting server and Protection Group
- AC-004: Validation completes in <500ms even with 100 Protection Groups
- AC-005: Atomic transaction: either all servers assigned or none (rollback on conflict)

**Implementation**: Global scan of DynamoDB protection-groups table filtering by serverIds attribute.

---

#### FR-1.7: Tag-Based Server Filtering

**Requirement ID**: FR-PG-007  
**Priority**: Medium  
**Status**: ✅ Implemented, ⚠️ Needs Testing

**Description**: The system shall allow users to filter DRS source servers by tags when discovering servers for Protection Group assignment.

**Acceptance Criteria**:
- AC-001: User specifies tag filters as key-value pairs (e.g., {"Environment": "prod"})
- AC-002: System queries DRS API with tag filters
- AC-003: Returns only servers matching ALL specified tags (AND logic)
- AC-004: Indicates which servers are already assigned to Protection Groups
- AC-005: Maximum 10 tag filters per request

**Discovery API Request**:
```
GET /drs/source-servers?region=us-east-1&tags=Environment:prod,Tier:database

Response:
{
  "success": true,
  "data": [
    {
      "sourceServerID": "s-123",
      "hostname": "db-prod-01",
      "tags": {"Environment": "prod", "Tier": "database"},
      "assignedToProtectionGroup": null
    },
    {
      "sourceServerID": "s-456",
      "hostname": "db-prod-02",
      "tags": {"Environment": "prod", "Tier": "database"},
      "assignedToProtectionGroup": "pg-abc-123"
    }
  ]
}
```

---

### FR-2: Recovery Plan Management

#### FR-2.1: Create Recovery Plan

**Requirement ID**: FR-RP-001  
**Priority**: Critical  
**Status**: ✅ Implemented, ⚠️ Needs Testing

**Description**: The system shall allow users to create a Recovery Plan with a unique name, description, one or more Protection Group IDs, and wave configuration defining recovery execution order.

**Acceptance Criteria**:
- AC-001: Name must be globally unique (case-insensitive)
- AC-002: Must include at least one Protection Group ID
- AC-003: All Protection Group IDs must exist in the system
- AC-004: Must define at least one wave
- AC-005: Waves numbered sequentially starting from 1
- AC-006: Each wave must contain at least one server
- AC-007: No server duplication across waves
- AC-008: All servers from included Protection Groups must be assigned to exactly one wave
- AC-009: System generates unique UUID as Plan ID
- AC-010: System validates wave dependencies (Wave N cannot depend on Wave >N)

**Wave Configuration Schema**:
```json
{
  "waveNumber": 1,
  "waveName": "Database Tier",
  "waveDescription": "Primary Oracle databases",
  "serverIds": ["s-db1", "s-db2"],
  "executionType": "SEQUENTIAL",  // or "PARALLEL"
  "executionOrder": [1, 2],  // Order if SEQUENTIAL
  "dependencies": [],  // Wave numbers this wave depends on
  "waitTimeSeconds": 60  // Wait before next wave (0-3600)
}
```

**Validation Rules**:
1. All servers from Protection Groups must appear in exactly one wave
2. No duplicate servers across waves
3. Wave dependencies must reference valid wave numbers
4. Circular dependencies not allowed (Wave 2→Wave 3→Wave 2 invalid)
5. executionType must be "SEQUENTIAL" or "PARALLEL"
6. waitTimeSeconds range: 0-3600 (max 1 hour between waves)

---

#### FR-2.2: List Recovery Plans

**Requirement ID**: FR-RP-002  
**Priority**: Critical  
**Status**: ✅ Implemented, ✅ Tested

**Description**: The system shall return a list of all Recovery Plans accessible to the authenticated user.

**Acceptance Criteria**:
- AC-001: Returns array of Recovery Plan objects
- AC-002: Includes summary data: planId, name, description, protection group count, wave count, server count
- AC-003: Sorted by creation date descending
- AC-004: Response time < 300ms for up to 100 plans

---

#### FR-2.3: Get Single Recovery Plan

**Requirement ID**: FR-RP-003  
**Priority**: Critical  
**Status**: ✅ Implemented, ✅ Tested

**Description**: The system shall return complete details for a specific Recovery Plan including all wave configurations.

**Acceptance Criteria**:
- AC-001: Returns full Recovery Plan object with nested wave array
- AC-002: Includes Protection Group metadata for all referenced PGs
- AC-003: Includes server count per wave
- AC-004: Indicates if plan is currently executing
- AC-005: Returns 404 Not Found if plan doesn't exist

---

#### FR-2.4: Update Recovery Plan

**Requirement ID**: FR-RP-004  
**Priority**: High  
**Status**: ✅ Implemented, ⚠️ **CRITICAL BUG DISCOVERED**

**Description**: The system shall allow users to update an existing Recovery Plan's waves, description, and Protection Group assignments.

**Acceptance Criteria**:
- AC-001: Can update description
- AC-002: Can add/remove Protection Groups (must update wave assignments accordingly)
- AC-003: Can modify wave configurations (add/remove/reorder waves)
- AC-004: Cannot update plan name (immutable)
- AC-005: All validation rules from FR-RP-001 apply
- AC-006: Returns 409 Conflict if plan is currently executing
- AC-007: Updates UpdatedAt timestamp

**CRITICAL BUG**: 
- **Issue**: When updating Recovery Plan with renamed waves (e.g., "Database Wave" → "Database Tier"), frontend may receive inconsistent data causing UI errors
- **Root Cause**: Wave data transformation bug in API Lambda (PascalCase ↔ camelCase conversion)
- **Status**: ⚠️ **Fix in progress** (Session 33 identified the issue)
- **Workaround**: Refresh page after editing Recovery Plan
- **Priority**: P1 - Blocks production use

---

#### FR-2.5: Delete Recovery Plan

**Requirement ID**: FR-RP-005  
**Priority**: High  
**Status**: ✅ Implemented, ⚠️ Needs Testing

**Description**: The system shall allow users to delete a Recovery Plan if it's not currently executing.

**Acceptance Criteria**:
- AC-001: Returns 409 Conflict if plan has RUNNING executions
- AC-002: Soft-deletes plan from DynamoDB (marks deleted, retains execution history)
- AC-003: Does NOT delete Protection Groups (they remain independent)
- AC-004: Returns 204 No Content on success

---

#### FR-2.6: Wave Dependency Validation

**Requirement ID**: FR-RP-006  
**Priority**: Critical  
**Status**: ✅ Implemented, ❌ Untested

**Description**: The system shall validate wave dependencies to ensure no circular dependencies and that dependent waves execute after their prerequisites.

**Acceptance Criteria**:
- AC-001: During plan creation/update, system constructs dependency graph
- AC-002: Detects circular dependencies (Wave A→B→C→A)
- AC-003: Returns 400 Bad Request with specific circular dependency path
- AC-004: Ensures Wave N cannot depend on Wave M where M>N
- AC-005: Validation completes in <100ms for plans with up to 50 waves

**Circular Dependency Example**:
```
Wave 1 depends on: []
Wave 2 depends on: [1]
Wave 3 depends on: [2]
Wave 1 depends on: [3]  ← INVALID! Circular: 1→3→2→1

Error Response:
{
  "error": {
    "message": "Circular dependency detected",
    "code": "CIRCULAR_DEPENDENCY",
    "path": ["Wave-1", "Wave-3", "Wave-2", "Wave-1"]
  }
}
```

---

#### FR-2.7: Wave Execution Types

**Requirement ID**: FR-RP-007  
**Priority**: High  
**Status**: ✅ Implemented, ❌ Untested

**Description**: The system shall support two wave execution types: SEQUENTIAL (servers launch one-by-one) and PARALLEL (all servers launch simultaneously).

**Acceptance Criteria**:
- AC-001: SEQUENTIAL: Launch servers in specified executionOrder, wait for each to complete before next
- AC-002: PARALLEL: Launch all servers simultaneously, wait for all to complete
- AC-003: Within SEQUENTIAL wave, timeout 30 minutes per server
- AC-004: Within PARALLEL wave, timeout 30 minutes total (not per server)
- AC-005: If any server fails in SEQUENTIAL, remaining servers in wave skip but next wave continues
- AC-006: If any server fails in PARALLEL, wave marked failed but next wave continues

**Execution Flow - SEQUENTIAL**:
```
Wave 1 (SEQUENTIAL): [s-db1, s-db2]
  1. Launch s-db1 → Wait until COMPLETED
  2. Launch s-db2 → Wait until COMPLETED
  3. Mark Wave 1 COMPLETED
  4. Wait 60 seconds (waitTimeSeconds)
  5. Proceed to Wave 2
```

**Execution Flow - PARALLEL**:
```
Wave 2 (PARALLEL): [s-app1, s-app2, s-app3]
  1. Launch s-app1, s-app2, s-app3 simultaneously
  2. Poll all 3 jobs every 30 seconds
  3. When all COMPLETED, mark Wave 2 COMPLETED
  4. Wait 30 seconds
  5. Proceed to Wave 3
```

---

### FR-3: Execution Engine

#### FR-3.1: Start Recovery Execution

**Requirement ID**: FR-EXE-001  
**Priority**: Critical  
**Status**: ✅ Implemented, ❌ **UNTESTED - HIGHEST PRIORITY**

**Description**: The system shall allow users to start a recovery execution for a specified Recovery Plan with either DRILL or RECOVERY mode.

**Acceptance Criteria**:
- AC-001: Accepts Plan ID, ExecutionType (DRILL/RECOVERY), AccountId, Region as inputs
- AC-002: Validates Recovery Plan exists and is not currently executing
- AC-003: Generates unique execution ID (UUID)
- AC-004: Creates execution history record with status=RUNNING
- AC-005: Initiates Step Functions state machine asynchronously
- AC-006: Returns 202 Accepted with execution ID immediately (doesn't wait for completion)
- AC-007: Records InitiatedBy username from JWT token
- AC-008: DRILL mode launches instances with isDrill=true (isolated network)
- AC-009: RECOVERY mode launches instances with isDrill=false (production network)

**API Request**:
```
POST /executions
{
  "PlanId": "plan-abc-123",
  "ExecutionType": "DRILL",
  "AccountId": "123456789012",
  "Region": "us-east-1"
}

Response: 202 Accepted
{
  "success": true,
  "data": {
    "ExecutionId": "exec-xyz-789",
    "Status": "RUNNING",
    "StartTime": 1699999999,
    "Message": "Recovery execution started successfully"
  }
}
```

**Preconditions**:
- Recovery Plan must exist
- Recovery Plan must not have RUNNING executions
- User authenticated with valid JWT token
- AWS credentials configured for target account/region

**Postconditions**:
- Execution history record created in DynamoDB
- Step Functions execution started
- CloudWatch log entry: "Started execution {id} for plan {planId}"

---

#### FR-3.2: Wave-Based Execution Orchestration

**Requirement ID**: FR-EXE-002  
**Priority**: Critical  
**Status**: ✅ Implemented, ❌ **UNTESTED - CRITICAL**

**Description**: The system shall execute waves sequentially according to their wave number, respecting dependencies and wait times.

**Acceptance Criteria**:
- AC-001: Waves execute in order: Wave 1 → Wave 2 → Wave 3 → ...
- AC-002: Wave N+1 doesn't start until Wave N completes successfully
- AC-003: If Wave N fails, execution continues to Wave N+1 (fail-forward strategy)
- AC-004: System waits configurable seconds (waitTimeSeconds) between waves
- AC-005: If wave has dependencies, waits for all dependency waves to complete
- AC-006: Updates execution history after each wave completes

**Orchestration State Machine** (simplified):
```
FOR EACH wave IN recovery_plan.waves:
  1. Validate dependencies satisfied
  2. Launch DRS recovery jobs for all servers in wave
  3. Monitor jobs until all COMPLETED or FAILED
  4. Perform health checks on recovered instances
  5. Update execution history with wave status
  6. Wait {waitTimeSeconds}
  7. Continue to next wave
```

---

#### FR-3.3: DRS Recovery Job Initiation

**Requirement ID**: FR-EXE-003  
**Priority**: Critical  
**Status**: ✅ Implemented, ❌ **UNTESTED**

**Description**: The system shall call AWS DRS StartRecovery API for each server in a wave, passing appropriate parameters for drill vs production mode.

**Acceptance Criteria**:
- AC-001: Calls drs.start_recovery() with sourceServerID array
- AC-002: Sets isDrill=true for DRILL executions
- AC-003: Sets isDrill=false for RECOVERY executions
- AC-004: Uses recoverySnapshotID='LATEST' for most recent recovery point
- AC-005: Tags recovery jobs with ExecutionId, WaveNumber, PlanName
- AC-006: Returns job IDs for monitoring
- AC-007: Handles DRS API errors gracefully (retry on throttle, fail-forward on server not found)
- AC-008: Logs job initiation to CloudWatch

**DRS API Call**:
```python
response = drs_client.start_recovery(
    sourceServers=[
        {'sourceServerID': 's-123', 'recoverySnapshotID': 'LATEST'},
        {'sourceServerID': 's-456', 'recoverySnapshotID': 'LATEST'}
    ],
    isDrill=True,  # or False for production
    tags={
        'ExecutionId': 'exec-xyz',
        'WaveNumber': '1',
        'PlanName': 'Production-3Tier'
    }
)

job_id = response['job']['jobID']
```

---

#### FR-3.4: Recovery Job Monitoring

**Requirement ID**: FR-EXE-004  
**Priority**: Critical  
**Status**: ✅ Implemented, ❌ **UNTESTED**

**Description**: The system shall monitor DRS recovery jobs by polling DRS DescribeJobs API every 30 seconds until all jobs reach terminal state (COMPLETED or FAILED).

**Acceptance Criteria**:
- AC-001: Polls drs.describe_jobs() every 30 seconds
- AC-002: Tracks job status: PENDING → STARTED → COMPLETED/FAILED
- AC-003: Timeout after 30 minutes if jobs don't complete
- AC-004: Collects recovery instance IDs for health checks
- AC-005: Logs job progress to CloudWatch
- AC-006: Continues to health checks when all jobs terminal

**Job Status Transitions**:
```
PENDING (queued by DRS)
  ↓
STARTED (launching EC2 instance)
  ↓
COMPLETED (instance running) → Health Check
  OR
FAILED (launch error) → Mark server failed, continue
```

---

#### FR-3.5: Instance Health Checks

**Requirement ID**: FR-EXE-005  
**Priority**: High  
**Status**: ✅ Implemented, ❌ **UNTESTED**

**Description**: The system shall perform health checks on recovered EC2 instances using EC2 DescribeInstanceStatus API to verify instances are running and passing system checks.

**Acceptance Criteria**:
- AC-001: Calls ec2.describe_instance_status() for each recovered instance
- AC-002: Checks InstanceState.Name == 'running'
- AC-003: Checks SystemStatus.Status == 'ok'
- AC-004: Checks InstanceStatus.Status == 'ok'
- AC-005: Waits up to 5 minutes for checks to pass
- AC-006: If checks fail after 5 minutes, marks server as "unhealthy" but continues execution
- AC-007: Logs health check results to execution history

**Health Check Logic**:
```python
def health_check(instance_id, timeout=300):
    start = time.time()
    while time.time() - start < timeout:
        status = ec2.describe_instance_status(InstanceIds=[instance_id])
        if (status['InstanceState']['Name'] == 'running' and
            status['SystemStatus']['Status'] == 'ok'):
            return 'HEALTHY'
        time.sleep(30)
    return 'UNHEALTHY'
```

---

#### FR-3.6: Get Execution Status

**Requirement ID**: FR-EXE-006  
**Priority**: Critical  
**Status**: ✅ Implemented, ✅ Tested

**Description**: The system shall allow users to query the status of a running or completed execution.

**Acceptance Criteria**:
- AC-001: Returns current execution status: RUNNING, COMPLETED, FAILED, CANCELLED
- AC-002: Includes per-wave status and progress
- AC-003: Shows servers recovered per wave
- AC-004: Real-time updates (no caching)
- AC-005: Returns 404 if execution doesn't exist

**Response Example**:
```json
{
  "ExecutionId": "exec-xyz",
  "Status": "RUNNING",
  "StartTime": 1699999999,
  "PlanName": "Production-3Tier",
  "ExecutionType": "DRILL",
  "WaveStatus": [
    {
      "WaveNumber": 1,
      "WaveName": "Database",
      "Status": "COMPLETED",
      "ServersRecovered": 2,
      "Duration": "5m 23s"
    },
    {
      "WaveNumber": 2,
      "WaveName": "Application",
      "Status": "RUNNING",
      "ServersRecovered": 1,
      "Progress": "33% (1/3 servers)"
    },
    {
      "WaveNumber": 3,
      "WaveName": "Web",
      "Status": "PENDING",
      "ServersRecovered": 0
    }
  ]
}
```

---

#### FR-3.7: Cancel Execution

**Requirement ID**: FR-EXE-007  
**Priority**: Medium  
**Status**: ✅ Implemented, ❌ **UNTESTED**

**Description**: The system shall allow users to cancel a running execution, stopping recovery job initiation and terminating drill instances.

**Acceptance Criteria**:
- AC-001: Only RUNNING executions can be cancelled
- AC-002: Step Functions execution stopped immediately
- AC-003: In-progress DRS jobs continue (cannot be stopped mid-launch)
- AC-004: Pending waves are skipped
- AC-005: If DRILL mode, terminates all recovered instances
- AC-006: Updates execution status to CANCELLED
- AC-007: Records cancellation timestamp and user

---

#### FR-3.8: Execution History

**Requirement
