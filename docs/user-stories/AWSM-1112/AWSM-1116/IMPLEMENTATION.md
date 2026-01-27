# DRS Readiness Validation for Pre-Provisioned Instances

**Confluence Title**: DRS Readiness Validation - Pre-Flight Checks for Confident Failover Operations  
**Description**: Implementation guide for comprehensive DRS readiness validation before failover execution. Covers AllowLaunchingIntoThisInstance verification, Name tag matching, replication lag monitoring, and pre-provisioned instance state validation to ensure 99%+ failover success rates.

**JIRA Ticket**: [AWSM-1116](https://healthedge.atlassian.net/browse/AWSM-1116)  
**Epic**: [AWSM-1112 - DRS Integration and EC2 Recovery](https://healthedge.atlassian.net/browse/AWSM-1112)  
**Status**: 🟡 **PARTIALLY IMPLEMENTED**  
**Priority**: Medium  
**Business Impact**: Confidence in DR readiness before failover execution

---

## Executive Summary

DRS readiness validation ensures pre-provisioned instances and DRS replication are properly configured before failover operations. Validation checks AllowLaunchingIntoThisInstance capability, Name tag matching, replication lag, and pre-provisioned instance state to prevent failover failures.

**Current Status**: Replication state validation is implemented (`validate_server_replication_states()`). Missing: AllowLaunchingIntoThisInstance validation, Name tag matching, replication lag duration parsing, and instance state validation.

**Key Achievement Target**: 99%+ failover success rate through comprehensive pre-flight validation.

---

## Acceptance Criteria Status

### ❌ Criterion 1: AllowLaunchingIntoThisInstance Validation
**Requirement**: *Given* pre-provisioned DR instances, *When* validating readiness, *Then* AllowLaunchingIntoThisInstance capability is verified.

**Status**: ❌ **NOT IMPLEMENTED**

**What's Missing**:
- Validation function to check `launchIntoInstanceProperties` configuration
- Verification that target instance exists and is accessible
- Check that DRS launch configuration includes target instance ID
- Validation report generation

**Implementation Approach**:
```python
def validate_allow_launching_capability(
    source_server_id: str,
    region: str
) -> Dict:
    """
    Validate AllowLaunchingIntoThisInstance configuration.
    
    Returns:
        Validation result with status and details
    """
    drs = boto3.client('drs', region_name=region)
    
    # Get DRS launch configuration
    config = drs.get_launch_configuration(sourceServerID=source_server_id)
    
    # Check if launchIntoInstanceProperties is configured
    launch_into = config.get('launchIntoInstanceProperties', {})
    target_instance_id = launch_into.get('launchIntoEC2InstanceID')
    
    if not target_instance_id:
        return {
            'status': 'FAILED',
            'reason': 'AllowLaunchingIntoThisInstance not configured',
            'recommendation': 'Configure target instance in Protection Group'
        }
    
    # Verify target instance exists
    ec2 = boto3.client('ec2', region_name=region)
    try:
        response = ec2.describe_instances(InstanceIds=[target_instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        
        return {
            'status': 'PASSED',
            'targetInstanceId': target_instance_id,
            'instanceState': instance['State']['Name']
        }
    except ClientError as e:
        return {
            'status': 'FAILED',
            'reason': f'Target instance {target_instance_id} not found',
            'error': str(e)
        }
```

---

### ❌ Criterion 2: Name Tag Matching Validation
**Requirement**: *Given* primary-DR instance pairs, *When* validating configuration, *Then* Name tag matching is confirmed between regions.

**Status**: ❌ **NOT IMPLEMENTED**

**What's Missing**:
- Function to compare Name tags between source and target instances
- Validation that Name tags match exactly
- Detection of missing or mismatched Name tags
- Reporting of unmatched instances

**Implementation Approach**:
```python
def validate_name_tag_matching(
    source_server_id: str,
    source_region: str,
    target_region: str
) -> Dict:
    """
    Validate Name tag matching between source and target instances.
    
    Returns:
        Validation result with matching status
    """
    # Get source server name
    source_name = get_source_server_name(source_server_id, source_region)
    
    # Get target instance by Name tag
    ec2 = boto3.client('ec2', region_name=target_region)
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Name', 'Values': [source_name]},
            {'Name': 'tag:AWSDRS', 'Values': ['AllowLaunchingIntoThisInstance']}
        ]
    )
    
    instances = []
    for reservation in response['Reservations']:
        instances.extend(reservation['Instances'])
    
    if len(instances) == 0:
        return {
            'status': 'FAILED',
            'reason': f'No target instance found with Name={source_name}',
            'recommendation': 'Create pre-provisioned instance with matching Name tag'
        }
    
    if len(instances) > 1:
        return {
            'status': 'FAILED',
            'reason': f'Multiple instances found with Name={source_name}',
            'instanceIds': [inst['InstanceId'] for inst in instances],
            'recommendation': 'Ensure unique Name tags in target region'
        }
    
    return {
        'status': 'PASSED',
        'sourceName': source_name,
        'targetInstanceId': instances[0]['InstanceId'],
        'matched': True
    }
```

---

### 🟡 Criterion 3: Replication Lag Validation
**Requirement**: *Given* DRS replication, *When* validating readiness, *Then* replication lag is within acceptable thresholds.

**Status**: 🟡 **PARTIALLY IMPLEMENTED**

**What's Implemented**:
- `validate_server_replication_states()` function exists
- Checks `dataReplicationState` against invalid states
- Checks `lifecycleState` for STOPPED servers
- Returns validation results with unhealthy servers list

**Implementation Location**:
- Validation Function: `lambda/api-handler/index.py` (lines 1192-1265)
- Used in execution validation (line 4210)

**Code Evidence**:
```python
def validate_server_replication_states(
    region: str, server_ids: List[str]
) -> Dict:
    """
    Validate that all servers have healthy replication state for recovery.
    Returns validation result with unhealthy servers list.
    """
    # Checks replication_state and lifecycle_state
    if (
        replication_state in INVALID_REPLICATION_STATES
        or lifecycle_state == "STOPPED"
    ):
        unhealthy_servers.append({
            "serverId": server_id,
            "replicationState": replication_state,
            "lifecycleState": lifecycle_state
        })
```

**What's Missing**:
- Replication lag duration parsing (ISO 8601 format)
- Configurable lag threshold (currently hardcoded invalid states)
- Warning vs. error thresholds
- Per-Protection-Group threshold configuration

**Implementation Approach**:
```python
def validate_replication_lag(
    source_server_id: str,
    region: str,
    max_lag_minutes: int = 5
) -> Dict:
    """
    Validate DRS replication lag is within acceptable threshold.
    
    Args:
        source_server_id: DRS source server ID
        region: AWS region
        max_lag_minutes: Maximum acceptable lag in minutes
        
    Returns:
        Validation result with lag status
    """
    drs = boto3.client('drs', region_name=region)
    
    # Get source server details
    response = drs.describe_source_servers(
        filters={'sourceServerIDs': [source_server_id]}
    )
    
    if not response.get('items'):
        return {
            'status': 'FAILED',
            'reason': 'Source server not found in DRS'
        }
    
    server = response['items'][0]
    data_replication = server.get('dataReplicationInfo', {})
    
    # Check replication state
    replication_state = data_replication.get('dataReplicationState')
    if replication_state != 'CONTINUOUS':
        return {
            'status': 'FAILED',
            'reason': f'Replication state is {replication_state}, expected CONTINUOUS',
            'recommendation': 'Wait for replication to reach CONTINUOUS state'
        }
    
    # Check replication lag
    lag_duration = data_replication.get('lagDuration')
    if lag_duration:
        # Parse ISO 8601 duration (e.g., "PT5M" = 5 minutes)
        lag_minutes = parse_iso_duration_to_minutes(lag_duration)
        
        if lag_minutes > max_lag_minutes:
            return {
                'status': 'WARNING',
                'reason': f'Replication lag is {lag_minutes} minutes (threshold: {max_lag_minutes})',
                'lagMinutes': lag_minutes,
                'recommendation': 'Consider waiting for lag to decrease'
            }
    
    return {
        'status': 'PASSED',
        'replicationState': replication_state,
        'lagMinutes': lag_minutes if lag_duration else 0
    }
```

---

### ❌ Criterion 4: Pre-Provisioned Instance State Validation
**Requirement**: *Given* pre-provisioned instances, *When* validating state, *Then* instances are running without attached storage (cost optimization).

**Status**: ❌ **NOT IMPLEMENTED**

**What's Missing**:
- Function to check instance state (stopped vs. running)
- Validation of attached EBS volumes (root only vs. full storage)
- Cost optimization recommendations
- Alerting for instances with unnecessary storage

**Implementation Approach**:
```python
def validate_preprovisioned_instance_state(
    instance_id: str,
    region: str
) -> Dict:
    """
    Validate pre-provisioned instance state and storage configuration.
    
    Returns:
        Validation result with state and cost optimization recommendations
    """
    ec2 = boto3.client('ec2', region_name=region)
    
    response = ec2.describe_instances(InstanceIds=[instance_id])
    instance = response['Reservations'][0]['Instances'][0]
    
    state = instance['State']['Name']
    volumes = instance.get('BlockDeviceMappings', [])
    
    # Check instance state
    if state != 'stopped':
        return {
            'status': 'WARNING',
            'reason': f'Instance is {state}, expected stopped for cost optimization',
            'recommendation': 'Stop instance when not in use to reduce costs'
        }
    
    # Check storage configuration
    if len(volumes) > 1:
        total_size = sum(
            get_volume_size(vol['Ebs']['VolumeId'], ec2)
            for vol in volumes
        )
        
        return {
            'status': 'WARNING',
            'reason': f'Instance has {len(volumes)} volumes ({total_size} GB total)',
            'recommendation': 'Consider minimal storage (root volume only) for cost optimization',
            'volumeCount': len(volumes),
            'totalSizeGB': total_size
        }
    
    return {
        'status': 'PASSED',
        'instanceState': state,
        'volumeCount': len(volumes),
        'costOptimized': True
    }
```

---

## Definition of Done - Implementation Checklist

### ❌ 1. AllowLaunchingIntoThisInstance Validation Logic
**Status**: ❌ **NOT STARTED**

See Criterion 1 above for requirements and implementation approach.

---

### ❌ 2. Name Tag Matching Validation Logic
**Status**: ❌ **NOT STARTED**

See Criterion 2 above for requirements and implementation approach.

**Files to Create**:
- `infra/orchestration/drs-orchestration/lambda/shared/name_tag_validator.py`

**Testing Required**:
- Unit tests for matching logic
- Test cases: exact match, no match, multiple matches, case sensitivity

---

### 🟡 3. Replication Lag Threshold Checks
**Status**: 🟡 **PARTIALLY IMPLEMENTED** (State validation exists, lag duration parsing missing)

**What's Implemented**:
- `validate_server_replication_states()` function in `lambda/api-handler/index.py`
- Checks against `INVALID_REPLICATION_STATES` constant
- Validates lifecycle state (detects STOPPED servers)
- Returns structured validation results

**What's Missing**:
- `validate_replication_lag()` - Check lag against threshold
- `parse_iso_duration_to_minutes()` - Parse DRS lag duration format
- `get_replication_status()` - Query DRS replication state

**Configuration**:
- Default threshold: 5 minutes
- Configurable per Protection Group
- Warning vs. error thresholds

**Files to Create**:
- `infra/orchestration/drs-orchestration/lambda/shared/replication_validator.py`

**Testing Required**:
- Unit tests for lag calculation
- Test cases: within threshold, exceeds threshold, no replication

---

### ❌ 4. Pre-Provisioned Instance State Validation
**Status**: ❌ **NOT STARTED**

**Required Functions**:
- `validate_preprovisioned_instance_state()` - Check instance state and storage
- `get_volume_size()` - Calculate total attached storage
- `generate_cost_optimization_recommendations()` - Suggest improvements

**Files to Create**:
- `infra/orchestration/drs-orchestration/lambda/shared/instance_state_validator.py`

**Testing Required**:
- Unit tests for state validation
- Test cases: stopped with minimal storage, running, multiple volumes

---

### ❌ 5. Readiness Validation Testing
**Status**: ❌ **NOT STARTED**

**Test Scenarios**:

1. **Complete Readiness Test**:
   - All validations pass
   - Verify readiness report shows "READY"

2. **Partial Readiness Test**:
   - Some validations fail (e.g., replication lag high)
   - Verify warnings generated
   - Verify failover can proceed with warnings

3. **Not Ready Test**:
   - Critical validations fail (e.g., target instance missing)
   - Verify failover blocked
   - Verify error messages actionable

4. **Validation Report Test**:
   - Execute full validation
   - Verify report includes all checks
   - Verify recommendations provided

**Test Files to Create**:
- `tests/integration/test_drs_readiness_validation.py`
- `tests/unit/test_validation_functions.py`

---

## Readiness Validation Workflow

### Pre-Failover Validation

```
User Initiates Failover
         │
         ▼
┌─────────────────────────┐
│ Run Readiness Validation│
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ Validation Checks (Parallel)                            │
├─────────────────────────────────────────────────────────┤
│ 1. AllowLaunchingIntoThisInstance configured? ✓         │
│ 2. Name tags match between regions? ✓                   │
│ 3. Replication lag < 5 minutes? ⚠️ (7 minutes)          │
│ 4. Pre-provisioned instances stopped? ✓                 │
│ 5. Minimal storage configuration? ⚠️ (3 volumes)        │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Generate Report         │
│ Status: READY (warnings)│
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ User Reviews Report     │
│ Proceed with failover?  │
└────────┬────────────────┘
         │
    ┌────┴────┐
    │         │
   Yes       No
    │         │
    ▼         ▼
Proceed    Cancel
```

### Validation Report Format

```json
{
  "validationId": "val-12345",
  "timestamp": "2026-01-20T17:00:00Z",
  "protectionGroupId": "pg-prod-001",
  "overallStatus": "READY_WITH_WARNINGS",
  "checks": [
    {
      "checkName": "AllowLaunchingIntoThisInstance",
      "status": "PASSED",
      "details": "All 10 servers configured with target instances"
    },
    {
      "checkName": "NameTagMatching",
      "status": "PASSED",
      "details": "All source-target pairs matched successfully"
    },
    {
      "checkName": "ReplicationLag",
      "status": "WARNING",
      "details": "2 servers have lag > 5 minutes (max: 7 minutes)",
      "affectedServers": ["srv-001", "srv-005"]
    },
    {
      "checkName": "InstanceState",
      "status": "PASSED",
      "details": "All target instances stopped"
    },
    {
      "checkName": "StorageOptimization",
      "status": "WARNING",
      "details": "3 instances have non-optimal storage configuration",
      "recommendation": "Consider reducing to root volume only for cost savings"
    }
  ],
  "recommendations": [
    "Wait for replication lag to decrease on srv-001 and srv-005",
    "Optimize storage on 3 instances to reduce costs by ~$500/month"
  ],
  "proceedWithFailover": true
}
```

---

## Implementation Priority

### Phase 1: Core Validation Functions (2 weeks)
1. Implement AllowLaunchingIntoThisInstance validation
2. Implement Name tag matching validation
3. Implement replication lag validation
4. Implement instance state validation
5. Unit tests for all validation functions

### Phase 2: Validation Orchestration (1 week)
1. Create validation orchestration function
2. Implement parallel validation execution
3. Generate validation reports
4. Add validation to API endpoints

### Phase 3: Integration and Testing (1 week)
1. Integration tests with real DRS servers
2. End-to-end validation workflow testing
3. Validation report generation testing
4. Performance testing (validate 100+ servers)

### Phase 4: Documentation (1 week)
1. Readiness validation user guide
2. Validation troubleshooting guide
3. Pre-failover checklist runbook

---

## Related Documentation

- [AWSM-1111: DRS Orchestration Module](../AWSM-1111/IMPLEMENTATION.md) - Core DRS integration
- [AWSM-1119: AllowLaunchingIntoThisInstance](../AWSM-1119/IMPLEMENTATION.md) - Target instance configuration
- [AWSM-1113: DRS Drill Mode](../AWSM-1113/IMPLEMENTATION.md) - Drill mode validation

---

## Repository Information

**Repository**: [he.platform.devops.aws.dr-orchestration](https://code.aws.dev/personal_projects/alias_d/duvvip/he.platform.devops.aws.dr-orchestration)  
**Branch**: feature/drs-orchestration-engine  
**Implementation Files**:
- `infra/orchestration/drs-orchestration/lambda/shared/drs_validation.py` (to be created)
- `infra/orchestration/drs-orchestration/lambda/shared/name_tag_validator.py` (to be created)
- `infra/orchestration/drs-orchestration/lambda/shared/replication_validator.py` (to be created)
- `infra/orchestration/drs-orchestration/lambda/shared/instance_state_validator.py` (to be created)
