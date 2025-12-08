# Software Requirements Specification
# AWS DRS Orchestration System

**Version**: 2.0  
**Date**: December 2025  
**Status**: Production Release

---

## Document Purpose

This Software Requirements Specification (SRS) defines the functional and non-functional requirements for the AWS DRS Orchestration system. It serves as the authoritative source for system capabilities and validation criteria.

---

## Scope

### In Scope
- Protection Group Management (CRUD, server assignment, conflict detection)
- Recovery Plan Management (wave configuration, dependencies, execution types)
- Recovery Execution (drill/production modes, wave orchestration, health checks)
- Server Discovery (DRS API integration, automatic detection)
- User Management (Cognito authentication, JWT authorization)
- Audit Trail (execution history, CloudWatch Logs)

### Out of Scope
- Pre/Post Recovery Scripts (Phase 2)
- VPC Test Isolation (Phase 2)
- Automated Rollback (Phase 2)
- Reprotection/Failback (Phase 3)

---

## Functional Requirements

### FR-1: Protection Group Management

#### FR-1.1: Create Protection Group
**Priority**: Critical

The system shall allow users to create a Protection Group with:
- Unique name (case-insensitive, 1-128 characters)
- AWS region (13 supported regions)
- Optional description (max 512 characters)
- List of DRS source server IDs

**Validation Rules**:
- Name must be globally unique (case-insensitive)
- Server IDs must exist in DRS for the specified region
- Server IDs cannot be assigned to another Protection Group
- System generates UUID as Protection Group ID
- System records creation timestamp

**API**: `POST /protection-groups`
**Response**: 201 Created with Protection Group data
**Errors**: 400 (validation), 409 (duplicate name or server conflict)

#### FR-1.2: List Protection Groups
**Priority**: Critical

The system shall return all Protection Groups with:
- ID, name, region, description
- Server IDs and server count
- Created and updated timestamps

**API**: `GET /protection-groups`
**Response**: Array of Protection Group objects, sorted by creation date descending

#### FR-1.3: Get Protection Group
**Priority**: Critical

The system shall return a single Protection Group by ID with all fields.

**API**: `GET /protection-groups/{id}`
**Response**: Protection Group object
**Errors**: 404 (not found)

#### FR-1.4: Update Protection Group
**Priority**: High

The system shall allow updating:
- Description
- Server assignments (add/remove)

Immutable fields: name, region

**API**: `PUT /protection-groups/{id}`
**Response**: Updated Protection Group object
**Errors**: 400 (validation), 404 (not found), 409 (server conflict)

#### FR-1.5: Delete Protection Group
**Priority**: High

The system shall delete a Protection Group if not referenced by Recovery Plans.

**API**: `DELETE /protection-groups/{id}`
**Response**: 204 No Content
**Errors**: 404 (not found), 409 (referenced by Recovery Plans)

#### FR-1.6: Server Assignment Validation
**Priority**: Critical

The system shall enforce that each DRS source server can be assigned to at most one Protection Group (globally unique constraint).

---

### FR-2: Recovery Plan Management

#### FR-2.1: Create Recovery Plan
**Priority**: Critical

The system shall allow users to create a Recovery Plan with:
- Unique name (case-insensitive)
- One or more Protection Group IDs
- Wave configuration with server assignments

**Wave Configuration**:
```json
{
  "waveNumber": 1,
  "waveName": "Database Tier",
  "serverIds": ["s-xxx", "s-yyy"],
  "executionType": "SEQUENTIAL|PARALLEL",
  "waitTimeSeconds": 60
}
```

**Validation Rules**:
- All Protection Group IDs must exist
- At least one wave required
- Each server assigned to exactly one wave
- No circular wave dependencies
- executionType: SEQUENTIAL or PARALLEL
- waitTimeSeconds: 0-3600

**API**: `POST /recovery-plans`
**Response**: 201 Created with Recovery Plan data

#### FR-2.2: List Recovery Plans
**Priority**: Critical

The system shall return all Recovery Plans with summary data.

**API**: `GET /recovery-plans`
**Response**: Array of Recovery Plan objects

#### FR-2.3: Get Recovery Plan
**Priority**: Critical

The system shall return a single Recovery Plan with full wave configuration.

**API**: `GET /recovery-plans/{id}`
**Response**: Recovery Plan object with waves array

#### FR-2.4: Update Recovery Plan
**Priority**: High

The system shall allow updating wave configuration and description.
Cannot update if plan is currently executing.

**API**: `PUT /recovery-plans/{id}`
**Errors**: 409 (currently executing)

#### FR-2.5: Delete Recovery Plan
**Priority**: High

The system shall delete a Recovery Plan if not currently executing.

**API**: `DELETE /recovery-plans/{id}`
**Errors**: 409 (currently executing)

---

### FR-3: Execution Engine

#### FR-3.1: Start Execution
**Priority**: Critical

The system shall start a recovery execution with:
- Plan ID
- Execution type: DRILL or RECOVERY
- Target AWS account ID
- Target AWS region

**API**: `POST /executions`
**Response**: 202 Accepted with execution ID

**Behavior**:
- Creates execution record with status PENDING
- Initiates Step Functions state machine
- Returns immediately (async execution)

#### FR-3.2: Wave Orchestration
**Priority**: Critical

The system shall execute waves sequentially:
1. Validate dependencies satisfied
2. Launch DRS recovery for all servers in wave
3. Monitor jobs until complete (poll every 30 seconds)
4. Perform health checks on recovered instances
5. Wait configured seconds
6. Proceed to next wave

**Execution Types**:
- SEQUENTIAL: Launch servers one-by-one, wait for each
- PARALLEL: Launch all servers simultaneously

#### FR-3.3: DRS Integration
**Priority**: Critical

The system shall call DRS StartRecovery API:
- Pass sourceServerID array
- Set isDrill=true for DRILL executions
- Use recoverySnapshotID='LATEST'
- Tag jobs with ExecutionId, WaveNumber

#### FR-3.4: Job Monitoring
**Priority**: Critical

The system shall monitor DRS jobs:
- Poll DescribeJobs every 30 seconds
- Track status: PENDING → STARTED → COMPLETED/FAILED
- Timeout after 30 minutes
- Continue to next wave on completion

#### FR-3.5: Health Checks
**Priority**: High

The system shall verify recovered instances:
- Check EC2 InstanceState = 'running'
- Check SystemStatus = 'ok'
- Wait up to 5 minutes for checks to pass
- Mark unhealthy but continue execution

#### FR-3.6: Get Execution Status
**Priority**: Critical

The system shall return execution status:
- Overall status: PENDING, POLLING, LAUNCHING, COMPLETED, FAILED, CANCELLED
- Per-wave status and progress
- Server recovery status
- Duration and timestamps

**API**: `GET /executions/{id}`

#### FR-3.7: List Executions
**Priority**: Critical

The system shall return execution history with filtering by status.

**API**: `GET /executions`

#### FR-3.8: Cancel Execution
**Priority**: Medium

The system shall cancel a running execution:
- Stop Step Functions execution
- Skip pending waves that have not yet been initiated
- Already-running waves cannot be cancelled (DRS jobs continue to completion)
- Update status to CANCELLED

**Note**: Cancel only prevents future waves from starting. DRS recovery jobs already in progress will complete normally.

**API**: `DELETE /executions/{id}`

---

### FR-4: Server Discovery

#### FR-4.1: Discover DRS Servers
**Priority**: Critical

The system shall discover DRS source servers by region:
- Query DRS DescribeSourceServers API
- Return server ID, hostname, replication status
- Indicate assignment status (available vs assigned)
- Support real-time search filtering

**API**: `GET /drs/source-servers?region={region}`

---

### FR-5: Authentication

#### FR-5.1: User Authentication
**Priority**: Critical

The system shall authenticate users via AWS Cognito:
- Username/password authentication
- JWT token issuance
- Token refresh support
- Session management

#### FR-5.2: API Authorization
**Priority**: Critical

The system shall authorize API requests:
- Validate JWT token on each request
- Extract user identity from token
- Log user actions for audit

---

## Non-Functional Requirements

### NFR-1: Performance

| Metric | Target |
|--------|--------|
| API Response Time (p95) | <200ms |
| Page Load Time | <2 seconds |
| Recovery Initiation | <5 seconds |
| Concurrent Users | 50+ |
| DRS Job Polling | Every 30 seconds |
| UI Refresh (active executions) | Every 3 seconds |
| UI Refresh (dashboard) | Every 30 seconds |

### NFR-2: Availability

| Metric | Target |
|--------|--------|
| API Availability | 99.9% |
| Frontend Availability | 99.9% |
| Planned Downtime | <4 hours/month |

### NFR-3: Scalability

| Metric | Target |
|--------|--------|
| Protection Groups | 1,000+ |
| Recovery Plans | 500+ |
| Servers per Plan | 200+ |
| Concurrent Executions | 10+ |

### NFR-4: Security

- All data encrypted at rest (DynamoDB, S3)
- All data encrypted in transit (HTTPS/TLS 1.2+)
- JWT token expiration: 1 hour
- Cognito password policy: 8+ chars, mixed case, numbers, symbols
- IAM least-privilege for Lambda roles

### NFR-5: Compliance

- Execution history retained 90 days minimum
- All API calls logged to CloudWatch
- CloudTrail integration for audit
- WCAG 2.1 AA accessibility

---

## API Specifications

### Base URL
`https://{api-id}.execute-api.{region}.amazonaws.com/{stage}`

### Authentication
All endpoints require `Authorization: Bearer {jwt-token}` header.

### Endpoints Summary

| Method | Path | Description |
|--------|------|-------------|
| GET | /protection-groups | List all Protection Groups |
| POST | /protection-groups | Create Protection Group |
| GET | /protection-groups/{id} | Get Protection Group |
| PUT | /protection-groups/{id} | Update Protection Group |
| DELETE | /protection-groups/{id} | Delete Protection Group |
| GET | /recovery-plans | List all Recovery Plans |
| POST | /recovery-plans | Create Recovery Plan |
| GET | /recovery-plans/{id} | Get Recovery Plan |
| PUT | /recovery-plans/{id} | Update Recovery Plan |
| DELETE | /recovery-plans/{id} | Delete Recovery Plan |
| GET | /executions | List executions |
| POST | /executions | Start execution |
| GET | /executions/{id} | Get execution status |
| POST | /executions/{id}/cancel | Cancel execution |
| POST | /executions/{id}/pause | Pause execution |
| POST | /executions/{id}/resume | Resume execution |
| DELETE | /executions | Delete all completed executions |
| GET | /drs/source-servers | Discover DRS servers |
| GET | /health | Health check endpoint |

### Response Format

**Success**:
```json
{
  "success": true,
  "data": { ... }
}
```

**Error**:
```json
{
  "success": false,
  "error": {
    "message": "Error description",
    "code": "ERROR_CODE"
  }
}
```

---

## Data Requirements

### DynamoDB Tables

**protection-groups-{env}**
- Partition Key: `GroupId` (String)
- Attributes: GroupName, Region, Description, SourceServerIds, CreatedDate, LastModifiedDate

**recovery-plans-{env}**
- Partition Key: `PlanId` (String)
- Attributes: PlanName, Description, ProtectionGroupIds, Waves, CreatedDate, LastModifiedDate

**execution-history-{env}**
- Partition Key: `ExecutionId` (String)
- Sort Key: `PlanId` (String)
- GSI: StatusIndex (Status, StartTime)
- Attributes: Status, ExecutionType, Waves, StartTime, EndTime, InitiatedBy

### Data Retention
- Protection Groups: Indefinite
- Recovery Plans: Indefinite
- Execution History: 90 days minimum
