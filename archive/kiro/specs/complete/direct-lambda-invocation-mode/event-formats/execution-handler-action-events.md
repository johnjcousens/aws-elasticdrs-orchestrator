# Execution Handler Action-Based Event Formats

**Handler**: `lambda/execution-handler/index.py`  
**Invocation Pattern**: Action-Based (Step Functions Orchestration)  
**Purpose**: Wave-based recovery execution orchestrated by Step Functions

## Overview

The execution-handler supports **action-based invocation** for Step Functions orchestration. This pattern is used when the Step Functions state machine needs to trigger specific recovery actions during wave execution.

## Detection Logic

Action-based invocation is detected when the event contains an `action` field:

```python
if event.get("action"):
    # Route to action-based handler
    return handle_action_invocation(event)
```

## Event Structure

```json
{
  "action": "action_name",
  "state": {
    "executionId": "uuid",
    "planId": "uuid",
    "accountContext": {...},
    "waves": [...]
  },
  "wave_number": 1
}
```

**Required Fields**:
- `action` (string): Action name (currently only `start_wave_recovery` supported)
- `state` (object): Step Functions state object
- `wave_number` (number): Wave number to execute

## Supported Actions

### 1. start_wave_recovery

Initiate DRS StartRecovery API call for a specific wave.

**Event**:
```json
{
  "action": "start_wave_recovery",
  "state": {
    "executionId": "exec-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "planId": "rp-b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "accountContext": {
      "accountId": "123456789012",
      "region": "us-east-1",
      "roleName": "DRSOrchestrationRole",
      "externalId": "unique-external-id"
    },
    "waves": [
      {
        "waveNumber": 1,
        "waveName": "Database Tier",
        "protectionGroupId": "pg-database",
        "servers": [
          {
            "serverId": "s-1234567890abcdef0",
            "hostname": "db-primary-01",
            "launchConfig": {
              "instanceType": "r5.xlarge",
              "subnet": "subnet-0123456789abcdef0",
              "securityGroups": ["sg-0123456789abcdef0"],
              "instanceProfile": "EC2-DRS-Role"
            }
          }
        ],
        "launchOrder": 1,
        "pauseBeforeWave": false,
        "dependsOnWaves": []
      },
      {
        "waveNumber": 2,
        "waveName": "Application Tier",
        "protectionGroupId": "pg-app",
        "servers": [...],
        "launchOrder": 2,
        "pauseBeforeWave": true,
        "dependsOnWaves": [1]
      }
    ],
    "currentWave": 1,
    "executionType": "DRILL",
    "initiatedBy": "user@example.com",
    "startTime": "2025-01-31T15:30:00Z"
  },
  "wave_number": 1
}
```

**State Object Fields**:
- `executionId` (string, required): Unique execution identifier
- `planId` (string, required): Recovery plan ID
- `accountContext` (object, required): Cross-account context
  - `accountId` (string): Target AWS account ID
  - `region` (string): Target AWS region
  - `roleName` (string): IAM role name for cross-account access
  - `externalId` (string, optional): External ID for role assumption
- `waves` (array, required): Complete wave configuration
  - `waveNumber` (number): Wave sequence number
  - `waveName` (string): Wave display name
  - `protectionGroupId` (string): Protection group ID
  - `servers` (array): Servers to recover with launch configurations
  - `launchOrder` (number): Launch order within wave
  - `pauseBeforeWave` (boolean): Pause gate before wave
  - `dependsOnWaves` (array): Wave dependencies
- `currentWave` (number, required): Current wave being executed
- `executionType` (string, required): DRILL or RECOVERY
- `initiatedBy` (string, required): User who initiated execution
- `startTime` (string, required): Execution start timestamp

**Wave Number Parameter**:
- `wave_number` (number, required): Specific wave to execute (must match a wave in `state.waves`)

**Response**:
```json
{
  "executionId": "exec-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "planId": "rp-b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "waveNumber": 1,
  "waveName": "Database Tier",
  "drsJobId": "drsjob-1234567890abcdef0",
  "status": "STARTED",
  "serversLaunched": 5,
  "accountContext": {
    "accountId": "123456789012",
    "region": "us-east-1"
  },
  "waves": [...],
  "currentWave": 1,
  "executionType": "DRILL",
  "initiatedBy": "user@example.com",
  "startTime": "2025-01-31T15:30:00Z"
}
```

**Response Fields**:
- Returns modified `state` object with DRS job information
- `drsJobId` (string): DRS recovery job ID from StartRecovery API
- `status` (string): Wave execution status
- `serversLaunched` (number): Number of servers in recovery job

**DRS API Call**:
The action performs these operations:
1. Assumes cross-account role using `accountContext`
2. Applies launch configurations from Protection Group to DRS source servers
3. Calls DRS `StartRecovery` API with server list
4. Updates execution record in DynamoDB with job ID
5. Returns modified state for Step Functions continuation

**Error Response**:
```json
{
  "error": "DRS_API_ERROR",
  "message": "Failed to start recovery: InsufficientCapacity",
  "executionId": "exec-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "waveNumber": 1,
  "state": {...}
}
```

---

## Step Functions Integration

### State Machine Invocation

The Step Functions state machine invokes this action during wave execution:

```json
{
  "StartWave1": {
    "Type": "Task",
    "Resource": "arn:aws:lambda:us-east-1:123456789012:function:execution-handler",
    "Parameters": {
      "action": "start_wave_recovery",
      "state.$": "$",
      "wave_number": 1
    },
    "ResultPath": "$",
    "Next": "PollWave1Status"
  }
}
```

### State Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Step Functions State                     │
├─────────────────────────────────────────────────────────────┤
│ executionId, planId, accountContext, waves[], currentWave   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Lambda: start_wave_recovery Action              │
├─────────────────────────────────────────────────────────────┤
│ 1. Extract wave configuration for wave_number                │
│ 2. Assume cross-account role                                │
│ 3. Apply launch configs to DRS source servers               │
│ 4. Call DRS StartRecovery API                               │
│ 5. Update execution record with drsJobId                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Modified State Returned                    │
├─────────────────────────────────────────────────────────────┤
│ Original state + drsJobId, status, serversLaunched          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Step Functions: Poll Wave Status                │
└─────────────────────────────────────────────────────────────┘
```

---

## Launch Configuration Application

Before calling DRS StartRecovery, the action applies launch configurations:

### Configuration Merge Priority

1. **Per-Server Override** (highest priority)
2. **Protection Group Default**
3. **DRS Default** (lowest priority)

### Example Configuration Merge

**Protection Group Default**:
```json
{
  "instanceType": "t3.medium",
  "subnet": "subnet-default",
  "securityGroups": ["sg-default"]
}
```

**Per-Server Override**:
```json
{
  "serverId": "s-abc",
  "launchConfig": {
    "instanceType": "r5.xlarge"
  }
}
```

**Final Applied Configuration**:
```json
{
  "serverId": "s-abc",
  "launchConfig": {
    "instanceType": "r5.xlarge",
    "subnet": "subnet-default",
    "securityGroups": ["sg-default"]
  }
}
```

---

## DRS StartRecovery API Call

The action constructs and calls the DRS StartRecovery API:

```python
drs_client.start_recovery(
    sourceServers=[
        {
            'sourceServerID': 's-1234567890abcdef0',
            'recoverySnapshotID': 'AUTO'
        }
    ],
    isDrill=True,  # Based on executionType
    tags={
        'ExecutionId': 'exec-a1b2c3d4-e5f6-7890-abcd-ef1234567890',
        'PlanId': 'rp-b2c3d4e5-f6a7-8901-bcde-f12345678901',
        'WaveNumber': '1',
        'WaveName': 'Database Tier'
    }
)
```

**Response from DRS**:
```json
{
  "job": {
    "jobID": "drsjob-1234567890abcdef0",
    "status": "PENDING",
    "type": "LAUNCH",
    "initiatedBy": "START_RECOVERY",
    "creationDateTime": "2025-01-31T15:30:00Z",
    "participatingServers": [
      {
        "sourceServerID": "s-1234567890abcdef0",
        "launchStatus": "PENDING"
      }
    ]
  }
}
```

---

## Error Handling

### DRS API Errors

**InsufficientCapacity**:
```json
{
  "error": "DRS_API_ERROR",
  "message": "Failed to start recovery: InsufficientCapacity - Not enough DRS capacity in region us-east-1",
  "executionId": "exec-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "waveNumber": 1,
  "retryable": false
}
```

**InvalidSourceServer**:
```json
{
  "error": "DRS_API_ERROR",
  "message": "Failed to start recovery: InvalidSourceServer - Server s-abc is not in READY_FOR_RECOVERY state",
  "executionId": "exec-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "waveNumber": 1,
  "retryable": false
}
```

**AccessDenied**:
```json
{
  "error": "CROSS_ACCOUNT_ERROR",
  "message": "Failed to assume role DRSOrchestrationRole in account 123456789012",
  "executionId": "exec-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "waveNumber": 1,
  "retryable": false
}
```

---

## Validation Rules

Before executing the action, the following validations are performed:

1. **Wave Exists**: `wave_number` must exist in `state.waves`
2. **Server Count**: Wave must have at least 1 server
3. **DRS Limit**: Wave must have ≤ 100 servers (DRS limit)
4. **Account Context**: Valid `accountContext` with required fields
5. **Launch Configs**: All servers must have valid launch configurations
6. **Replication State**: All servers must be in CONTINUOUS replication state
7. **Lifecycle State**: All servers must be in READY_FOR_RECOVERY state

---

## Complete Example: Multi-Wave Execution

### Wave 1 Invocation

```json
{
  "action": "start_wave_recovery",
  "state": {
    "executionId": "exec-123",
    "planId": "rp-456",
    "accountContext": {
      "accountId": "123456789012",
      "region": "us-east-1",
      "roleName": "DRSOrchestrationRole"
    },
    "waves": [
      {
        "waveNumber": 1,
        "waveName": "Database Tier",
        "protectionGroupId": "pg-db",
        "servers": [
          {
            "serverId": "s-db-01",
            "hostname": "db-primary",
            "launchConfig": {
              "instanceType": "r5.xlarge",
              "subnet": "subnet-db",
              "securityGroups": ["sg-db"]
            }
          }
        ],
        "launchOrder": 1
      },
      {
        "waveNumber": 2,
        "waveName": "App Tier",
        "protectionGroupId": "pg-app",
        "servers": [...],
        "launchOrder": 2,
        "dependsOnWaves": [1]
      }
    ],
    "currentWave": 1,
    "executionType": "DRILL",
    "initiatedBy": "user@example.com",
    "startTime": "2025-01-31T15:30:00Z"
  },
  "wave_number": 1
}
```

### Wave 1 Response

```json
{
  "executionId": "exec-123",
  "planId": "rp-456",
  "waveNumber": 1,
  "waveName": "Database Tier",
  "drsJobId": "drsjob-wave1",
  "status": "STARTED",
  "serversLaunched": 1,
  "accountContext": {...},
  "waves": [...],
  "currentWave": 1,
  "executionType": "DRILL",
  "initiatedBy": "user@example.com",
  "startTime": "2025-01-31T15:30:00Z"
}
```

### Wave 2 Invocation (After Wave 1 Completes)

```json
{
  "action": "start_wave_recovery",
  "state": {
    "executionId": "exec-123",
    "planId": "rp-456",
    "accountContext": {...},
    "waves": [...],
    "currentWave": 2,
    "executionType": "DRILL",
    "initiatedBy": "user@example.com",
    "startTime": "2025-01-31T15:30:00Z",
    "wave1JobId": "drsjob-wave1",
    "wave1Status": "COMPLETED"
  },
  "wave_number": 2
}
```

---

## Backward Compatibility

This action-based invocation pattern is **stable** and used by the Step Functions state machine. It must remain backward compatible with existing state machine definitions.

**Do NOT change**:
- Event structure (`action`, `state`, `wave_number` fields)
- Response structure (modified `state` object)
- Field names in `state` object
- Validation rules

**Safe to add**:
- New optional fields in `state` object
- New validation checks (non-breaking)
- Enhanced error messages
- Additional logging
