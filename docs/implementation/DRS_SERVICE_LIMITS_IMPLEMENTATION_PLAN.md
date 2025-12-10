# DRS Service Limits Compliance - Implementation Plan

## Executive Summary

This document outlines the implementation plan to add AWS DRS service limits validation to the orchestration solution. The goal is to prevent execution failures by validating against DRS quotas before starting recovery operations.

**Reference Document**: [AWS DRS Service Limits Research](../research/AWS_DRS_SERVICE_LIMITS_AND_CAPABILITIES_RESEARCH.md)

## Current State Analysis

### Existing Validations in `lambda/index.py`

The `execute_recovery_plan()` function currently validates:

| Validation | Status | Location |
|------------|--------|----------|
| Required fields (PlanId, ExecutionType, InitiatedBy) | ✅ Implemented | Line 1076-1079 |
| Valid execution type (DRILL/RECOVERY) | ✅ Implemented | Line 1083-1084 |
| Plan exists | ✅ Implemented | Line 1087-1089 |
| Plan has waves | ✅ Implemented | Line 1093-1094 |
| No active execution for same plan | ✅ Implemented | Line 1097-1104 |
| No server conflicts with other executions | ✅ Implemented | Line 1107-1124 |

### Missing DRS Service Limits Validations

| Validation | Status | DRS Limit |
|------------|--------|-----------|
| Max servers per wave/job | ❌ Missing | 100 servers |
| Max concurrent jobs | ❌ Missing | 20 total |
| Max servers in all active jobs | ❌ Missing | 500 servers |
| Server replication state healthy | ❌ Missing | Must be CONTINUOUS_REPLICATION |
| Account capacity (replicating servers) | ❌ Missing | 300 hard limit |

## Implementation Plan

### Phase 1: Backend Validation Functions

#### 1.1 Add DRS Limits Constants

**File**: `lambda/index.py`
**Location**: After line 30 (after environment variables)

```python
# DRS Service Limits (from AWS Service Quotas)
DRS_LIMITS = {
    'MAX_SERVERS_PER_JOB': 100,           # L-B827C881 - Hard limit
    'MAX_CONCURRENT_JOBS': 20,             # L-D88FAC3A - Hard limit
    'MAX_SERVERS_IN_ALL_JOBS': 500,        # L-05AFA8C6 - Hard limit
    'MAX_REPLICATING_SERVERS': 300,        # L-C1D14A2B - Hard limit (cannot increase)
    'MAX_SOURCE_SERVERS': 4000,            # L-E28BE5E0 - Adjustable
    'WARNING_REPLICATING_THRESHOLD': 250,  # Show warning
    'CRITICAL_REPLICATING_THRESHOLD': 280  # Block new servers
}

# Valid replication states for recovery
VALID_REPLICATION_STATES = [
    'CONTINUOUS_REPLICATION',
    'INITIAL_SYNC',
    'RESCAN'
]

INVALID_REPLICATION_STATES = [
    'DISCONNECTED',
    'STOPPED',
    'STALLED',
    'NOT_STARTED'
]
```

#### 1.2 Add Wave Size Validation Function

**File**: `lambda/index.py`
**New Function**:

```python
def validate_wave_sizes(plan: Dict) -> List[Dict]:
    """
    Validate that no wave exceeds the DRS limit of 100 servers per job.
    Returns list of validation errors.
    """
    errors = []
    
    for idx, wave in enumerate(plan.get('Waves', []), start=1):
        server_count = len(wave.get('ServerIds', []))
        if server_count > DRS_LIMITS['MAX_SERVERS_PER_JOB']:
            errors.append({
                'type': 'WAVE_SIZE_EXCEEDED',
                'wave': wave.get('WaveName', f'Wave {idx}'),
                'waveIndex': idx,
                'serverCount': server_count,
                'limit': DRS_LIMITS['MAX_SERVERS_PER_JOB'],
                'message': f"Wave '{wave.get('WaveName', f'Wave {idx}')}' has {server_count} servers, exceeds limit of {DRS_LIMITS['MAX_SERVERS_PER_JOB']}"
            })
    
    return errors
```

#### 1.3 Add Concurrent Jobs Validation Function

**File**: `lambda/index.py`
**New Function**:

```python
def validate_concurrent_jobs(region: str) -> Dict:
    """
    Check current DRS job count against the 20 concurrent jobs limit.
    Returns validation result with current count and availability.
    """
    try:
        # Create regional DRS client
        regional_drs = boto3.client('drs', region_name=region)
        
        # Get active jobs (PENDING or STARTED status)
        active_jobs = []
        paginator = regional_drs.get_paginator('describe_jobs')
        
        for page in paginator.paginate():
            for job in page.get('items', []):
                if job.get('status') in ['PENDING', 'STARTED']:
                    active_jobs.append({
                        'jobId': job.get('jobID'),
                        'status': job.get('status'),
                        'type': job.get('type'),
                        'serverCount': len(job.get('participatingServers', []))
                    })
        
        current_count = len(active_jobs)
        available_slots = DRS_LIMITS['MAX_CONCURRENT_JOBS'] - current_count
        
        return {
            'valid': current_count < DRS_LIMITS['MAX_CONCURRENT_JOBS'],
            'currentJobs': current_count,
            'maxJobs': DRS_LIMITS['MAX_CONCURRENT_JOBS'],
            'availableSlots': available_slots,
            'activeJobs': active_jobs,
            'message': f"DRS has {current_count}/{DRS_LIMITS['MAX_CONCURRENT_JOBS']} active jobs" if current_count < DRS_LIMITS['MAX_CONCURRENT_JOBS'] else f"DRS concurrent job limit reached ({current_count}/{DRS_LIMITS['MAX_CONCURRENT_JOBS']})"
        }
        
    except Exception as e:
        print(f"Error checking concurrent jobs: {e}")
        # Return valid=True to not block on API errors, but include warning
        return {
            'valid': True,
            'warning': f'Could not verify concurrent jobs: {str(e)}',
            'currentJobs': None,
            'maxJobs': DRS_LIMITS['MAX_CONCURRENT_JOBS']
        }
```

#### 1.4 Add Servers in All Jobs Validation Function

**File**: `lambda/index.py`
**New Function**:

```python
def validate_servers_in_all_jobs(region: str, new_server_count: int) -> Dict:
    """
    Check if adding new servers would exceed the 500 servers in all jobs limit.
    Returns validation result.
    """
    try:
        regional_drs = boto3.client('drs', region_name=region)
        
        # Count servers in active jobs
        servers_in_jobs = 0
        paginator = regional_drs.get_paginator('describe_jobs')
        
        for page in paginator.paginate():
            for job in page.get('items', []):
                if job.get('status') in ['PENDING', 'STARTED']:
                    servers_in_jobs += len(job.get('participatingServers', []))
        
        total_after_new = servers_in_jobs + new_server_count
        
        return {
            'valid': total_after_new <= DRS_LIMITS['MAX_SERVERS_IN_ALL_JOBS'],
            'currentServersInJobs': servers_in_jobs,
            'newServerCount': new_server_count,
            'totalAfterNew': total_after_new,
            'maxServers': DRS_LIMITS['MAX_SERVERS_IN_ALL_JOBS'],
            'message': f"Would have {total_after_new}/{DRS_LIMITS['MAX_SERVERS_IN_ALL_JOBS']} servers in active jobs" if total_after_new <= DRS_LIMITS['MAX_SERVERS_IN_ALL_JOBS'] else f"Would exceed max servers in all jobs ({total_after_new}/{DRS_LIMITS['MAX_SERVERS_IN_ALL_JOBS']})"
        }
        
    except Exception as e:
        print(f"Error checking servers in all jobs: {e}")
        return {
            'valid': True,
            'warning': f'Could not verify servers in jobs: {str(e)}',
            'currentServersInJobs': None,
            'maxServers': DRS_LIMITS['MAX_SERVERS_IN_ALL_JOBS']
        }
```

#### 1.5 Add Server Replication State Validation Function

**File**: `lambda/index.py`
**New Function**:

```python
def validate_server_replication_states(region: str, server_ids: List[str]) -> Dict:
    """
    Validate that all servers have healthy replication state for recovery.
    Returns validation result with unhealthy servers list.
    """
    try:
        regional_drs = boto3.client('drs', region_name=region)
        
        unhealthy_servers = []
        healthy_servers = []
        
        # Batch describe servers (max 200 per call)
        for i in range(0, len(server_ids), 200):
            batch = server_ids[i:i+200]
            
            response = regional_drs.describe_source_servers(
                filters={'sourceServerIDs': batch}
            )
            
            for server in response.get('items', []):
                server_id = server.get('sourceServerID')
                replication_state = server.get('dataReplicationInfo', {}).get('dataReplicationState', 'UNKNOWN')
                lifecycle_state = server.get('lifeCycle', {}).get('state', 'UNKNOWN')
                
                if replication_state in INVALID_REPLICATION_STATES or lifecycle_state == 'STOPPED':
                    unhealthy_servers.append({
                        'serverId': server_id,
                        'hostname': server.get('sourceProperties', {}).get('identificationHints', {}).get('hostname', 'Unknown'),
                        'replicationState': replication_state,
                        'lifecycleState': lifecycle_state,
                        'reason': f"Replication: {replication_state}, Lifecycle: {lifecycle_state}"
                    })
                else:
                    healthy_servers.append(server_id)
        
        return {
            'valid': len(unhealthy_servers) == 0,
            'healthyCount': len(healthy_servers),
            'unhealthyCount': len(unhealthy_servers),
            'unhealthyServers': unhealthy_servers,
            'message': f"All {len(healthy_servers)} servers have healthy replication" if len(unhealthy_servers) == 0 else f"{len(unhealthy_servers)} server(s) have unhealthy replication state"
        }
        
    except Exception as e:
        print(f"Error checking server replication states: {e}")
        return {
            'valid': True,
            'warning': f'Could not verify server replication states: {str(e)}',
            'unhealthyServers': []
        }
```

#### 1.6 Add Account Capacity Check Function

**File**: `lambda/index.py`
**New Function**:

```python
def get_drs_account_capacity(region: str) -> Dict:
    """
    Get current DRS account capacity metrics.
    Returns capacity info including replicating server count vs 300 hard limit.
    """
    try:
        regional_drs = boto3.client('drs', region_name=region)
        
        # Count all source servers and replicating servers
        total_servers = 0
        replicating_servers = 0
        
        paginator = regional_drs.get_paginator('describe_source_servers')
        
        for page in paginator.paginate():
            for server in page.get('items', []):
                total_servers += 1
                replication_state = server.get('dataReplicationInfo', {}).get('dataReplicationState', '')
                if replication_state in ['CONTINUOUS_REPLICATION', 'INITIAL_SYNC', 'RESCAN', 'CREATING_SNAPSHOT']:
                    replicating_servers += 1
        
        # Determine capacity status
        if replicating_servers >= DRS_LIMITS['MAX_REPLICATING_SERVERS']:
            status = 'CRITICAL'
            message = f"Account at hard limit: {replicating_servers}/{DRS_LIMITS['MAX_REPLICATING_SERVERS']} replicating servers"
        elif replicating_servers >= DRS_LIMITS['CRITICAL_REPLICATING_THRESHOLD']:
            status = 'WARNING'
            message = f"Approaching hard limit: {replicating_servers}/{DRS_LIMITS['MAX_REPLICATING_SERVERS']} replicating servers"
        elif replicating_servers >= DRS_LIMITS['WARNING_REPLICATING_THRESHOLD']:
            status = 'INFO'
            message = f"Monitor capacity: {replicating_servers}/{DRS_LIMITS['MAX_REPLICATING_SERVERS']} replicating servers"
        else:
            status = 'OK'
            message = f"Capacity OK: {replicating_servers}/{DRS_LIMITS['MAX_REPLICATING_SERVERS']} replicating servers"
        
        return {
            'totalSourceServers': total_servers,
            'replicatingServers': replicating_servers,
            'maxReplicatingServers': DRS_LIMITS['MAX_REPLICATING_SERVERS'],
            'maxSourceServers': DRS_LIMITS['MAX_SOURCE_SERVERS'],
            'availableReplicatingSlots': max(0, DRS_LIMITS['MAX_REPLICATING_SERVERS'] - replicating_servers),
            'status': status,
            'message': message
        }
        
    except Exception as e:
        print(f"Error getting account capacity: {e}")
        return {
            'error': str(e),
            'status': 'UNKNOWN',
            'message': f'Could not determine account capacity: {str(e)}'
        }
```

### Phase 2: Integrate Validations into execute_recovery_plan()

**File**: `lambda/index.py`
**Location**: After existing server conflict check (around line 1124)

Add the following validation block:

```python
        # ============================================================
        # DRS SERVICE LIMITS VALIDATION
        # ============================================================
        
        # Get region from first wave's protection group
        first_wave = plan.get('Waves', [{}])[0]
        pg_id = first_wave.get('ProtectionGroupId')
        pg_result = protection_groups_table.get_item(Key={'GroupId': pg_id})
        region = pg_result.get('Item', {}).get('Region', 'us-east-1')
        
        # Collect all server IDs from all waves
        all_server_ids = []
        for wave in plan.get('Waves', []):
            all_server_ids.extend(wave.get('ServerIds', []))
        total_servers_in_plan = len(all_server_ids)
        
        # 1. Validate wave sizes (max 100 servers per wave)
        wave_size_errors = validate_wave_sizes(plan)
        if wave_size_errors:
            return response(400, {
                'error': 'WAVE_SIZE_LIMIT_EXCEEDED',
                'message': f'{len(wave_size_errors)} wave(s) exceed the DRS limit of {DRS_LIMITS["MAX_SERVERS_PER_JOB"]} servers per job',
                'errors': wave_size_errors,
                'limit': DRS_LIMITS['MAX_SERVERS_PER_JOB']
            })
        
        # 2. Validate concurrent jobs (max 20)
        concurrent_jobs_result = validate_concurrent_jobs(region)
        if not concurrent_jobs_result.get('valid'):
            return response(429, {  # Too Many Requests
                'error': 'CONCURRENT_JOBS_LIMIT_EXCEEDED',
                'message': concurrent_jobs_result.get('message'),
                'currentJobs': concurrent_jobs_result.get('currentJobs'),
                'maxJobs': concurrent_jobs_result.get('maxJobs'),
                'activeJobs': concurrent_jobs_result.get('activeJobs', [])
            })
        
        # 3. Validate servers in all jobs (max 500)
        servers_in_jobs_result = validate_servers_in_all_jobs(region, total_servers_in_plan)
        if not servers_in_jobs_result.get('valid'):
            return response(429, {
                'error': 'SERVERS_IN_JOBS_LIMIT_EXCEEDED',
                'message': servers_in_jobs_result.get('message'),
                'currentServersInJobs': servers_in_jobs_result.get('currentServersInJobs'),
                'newServerCount': servers_in_jobs_result.get('newServerCount'),
                'totalAfterNew': servers_in_jobs_result.get('totalAfterNew'),
                'maxServers': servers_in_jobs_result.get('maxServers')
            })
        
        # 4. Validate server replication states
        replication_result = validate_server_replication_states(region, all_server_ids)
        if not replication_result.get('valid'):
            return response(400, {
                'error': 'UNHEALTHY_SERVER_REPLICATION',
                'message': replication_result.get('message'),
                'unhealthyServers': replication_result.get('unhealthyServers'),
                'healthyCount': replication_result.get('healthyCount'),
                'unhealthyCount': replication_result.get('unhealthyCount')
            })
        
        print(f"✅ DRS service limits validation passed for execution {plan_id}")
```

### Phase 3: Add API Endpoint for Quota Status

#### 3.1 Add GET /drs/quotas Endpoint

**File**: `lambda/index.py`
**Add to lambda_handler routing**:

```python
        elif path.startswith('/drs/quotas'):
            return handle_drs_quotas(query_parameters)
```

**New Handler Function**:

```python
def handle_drs_quotas(query_params: Dict) -> Dict:
    """Get DRS account quotas and current usage"""
    try:
        region = query_params.get('region', 'us-east-1')
        
        # Get account capacity
        capacity = get_drs_account_capacity(region)
        
        # Get concurrent jobs info
        jobs_info = validate_concurrent_jobs(region)
        
        # Get servers in active jobs
        servers_in_jobs = validate_servers_in_all_jobs(region, 0)
        
        return response(200, {
            'region': region,
            'limits': DRS_LIMITS,
            'capacity': capacity,
            'concurrentJobs': {
                'current': jobs_info.get('currentJobs'),
                'max': jobs_info.get('maxJobs'),
                'available': jobs_info.get('availableSlots')
            },
            'serversInJobs': {
                'current': servers_in_jobs.get('currentServersInJobs'),
                'max': servers_in_jobs.get('maxServers')
            }
        })
        
    except Exception as e:
        print(f"Error getting DRS quotas: {e}")
        return response(500, {'error': str(e)})
```

### Phase 4: Frontend Changes

#### 4.1 Add DRS Quota Service

**File**: `frontend/src/services/drsQuotaService.ts` (new file)

```typescript
import { apiClient } from './api';

export interface DRSLimits {
  MAX_SERVERS_PER_JOB: number;
  MAX_CONCURRENT_JOBS: number;
  MAX_SERVERS_IN_ALL_JOBS: number;
  MAX_REPLICATING_SERVERS: number;
  MAX_SOURCE_SERVERS: number;
}

export interface DRSQuotaStatus {
  region: string;
  limits: DRSLimits;
  capacity: {
    totalSourceServers: number;
    replicatingServers: number;
    maxReplicatingServers: number;
    availableReplicatingSlots: number;
    status: 'OK' | 'INFO' | 'WARNING' | 'CRITICAL';
    message: string;
  };
  concurrentJobs: {
    current: number;
    max: number;
    available: number;
  };
  serversInJobs: {
    current: number;
    max: number;
  };
}

export const getDRSQuotas = async (region: string): Promise<DRSQuotaStatus> => {
  const response = await apiClient.get(`/drs/quotas?region=${region}`);
  return response.data;
};
```

#### 4.2 Add Wave Size Validation in RecoveryPlanDialog

**File**: `frontend/src/components/RecoveryPlanDialog.tsx`
**Add validation**:

```typescript
const MAX_SERVERS_PER_WAVE = 100;

// In wave configuration validation
const validateWaveSize = (serverIds: string[]): string | null => {
  if (serverIds.length > MAX_SERVERS_PER_WAVE) {
    return `Wave cannot exceed ${MAX_SERVERS_PER_WAVE} servers (DRS limit). Current: ${serverIds.length}`;
  }
  return null;
};
```

#### 4.3 Add Quota Status Component

**File**: `frontend/src/components/DRSQuotaStatus.tsx` (new file)

```typescript
import React from 'react';
import { Box, ProgressBar, StatusIndicator, SpaceBetween } from '@cloudscape-design/components';
import { DRSQuotaStatus } from '../services/drsQuotaService';

interface Props {
  quotas: DRSQuotaStatus;
}

export const DRSQuotaStatusPanel: React.FC<Props> = ({ quotas }) => {
  const getStatusType = (status: string) => {
    switch (status) {
      case 'CRITICAL': return 'error';
      case 'WARNING': return 'warning';
      case 'INFO': return 'info';
      default: return 'success';
    }
  };

  return (
    <SpaceBetween size="m">
      <Box>
        <StatusIndicator type={getStatusType(quotas.capacity.status)}>
          {quotas.capacity.message}
        </StatusIndicator>
      </Box>
      
      <Box>
        <Box variant="awsui-key-label">Replicating Servers</Box>
        <ProgressBar
          value={(quotas.capacity.replicatingServers / quotas.capacity.maxReplicatingServers) * 100}
          description={`${quotas.capacity.replicatingServers} / ${quotas.capacity.maxReplicatingServers}`}
          status={quotas.capacity.status === 'CRITICAL' ? 'error' : 'in-progress'}
        />
      </Box>
      
      <Box>
        <Box variant="awsui-key-label">Concurrent Jobs</Box>
        <ProgressBar
          value={(quotas.concurrentJobs.current / quotas.concurrentJobs.max) * 100}
          description={`${quotas.concurrentJobs.current} / ${quotas.concurrentJobs.max}`}
        />
      </Box>
      
      <Box>
        <Box variant="awsui-key-label">Servers in Active Jobs</Box>
        <ProgressBar
          value={(quotas.serversInJobs.current / quotas.serversInJobs.max) * 100}
          description={`${quotas.serversInJobs.current} / ${quotas.serversInJobs.max}`}
        />
      </Box>
    </SpaceBetween>
  );
};
```

### Phase 5: Error Handling in Frontend

#### 5.1 Update Execution Error Handling

**File**: `frontend/src/pages/RecoveryPlansPage.tsx`
**Update error handling for new error types**:

```typescript
const handleExecutionError = (error: any) => {
  const errorCode = error.response?.data?.error;
  
  switch (errorCode) {
    case 'WAVE_SIZE_LIMIT_EXCEEDED':
      showError(`Wave size limit exceeded. Maximum ${error.response.data.limit} servers per wave.`);
      break;
    case 'CONCURRENT_JOBS_LIMIT_EXCEEDED':
      showError(`DRS concurrent jobs limit reached (${error.response.data.currentJobs}/${error.response.data.maxJobs}). Wait for active jobs to complete.`);
      break;
    case 'SERVERS_IN_JOBS_LIMIT_EXCEEDED':
      showError(`Would exceed max servers in active jobs (${error.response.data.totalAfterNew}/${error.response.data.maxServers}).`);
      break;
    case 'UNHEALTHY_SERVER_REPLICATION':
      const unhealthy = error.response.data.unhealthyServers;
      showError(`${unhealthy.length} server(s) have unhealthy replication state and cannot be recovered.`);
      break;
    default:
      showError(error.response?.data?.message || 'Execution failed');
  }
};
```

## Testing Plan

### Unit Tests

1. `test_validate_wave_sizes()` - Test wave size validation
2. `test_validate_concurrent_jobs()` - Test concurrent jobs check
3. `test_validate_servers_in_all_jobs()` - Test servers in jobs limit
4. `test_validate_server_replication_states()` - Test replication state validation
5. `test_get_drs_account_capacity()` - Test capacity check

### Integration Tests

1. Test execution blocked when wave exceeds 100 servers
2. Test execution blocked when 20 concurrent jobs active
3. Test execution blocked when 500 servers in active jobs
4. Test execution blocked when servers have unhealthy replication
5. Test successful execution when all limits pass

### E2E Tests

1. Create recovery plan with >100 servers in wave - expect validation error
2. Start execution when at job limit - expect 429 response
3. Verify quota status endpoint returns correct data
4. Verify frontend displays quota warnings appropriately

## Rollout Plan

### Phase 1: Backend (Week 1)
- [ ] Add DRS_LIMITS constants
- [ ] Implement validation functions
- [ ] Integrate into execute_recovery_plan()
- [ ] Add /drs/quotas endpoint
- [ ] Deploy to test environment
- [ ] Run integration tests

### Phase 2: Frontend (Week 2)
- [ ] Add DRS quota service
- [ ] Add wave size validation in RecoveryPlanDialog
- [ ] Add DRSQuotaStatus component
- [ ] Update error handling
- [ ] Deploy to test environment
- [ ] Run E2E tests

### Phase 3: Production (Week 3)
- [ ] Deploy backend to production
- [ ] Deploy frontend to production
- [ ] Monitor for issues
- [ ] Update documentation

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| DRS API rate limiting | Implement caching for quota checks (5-minute TTL) |
| API errors blocking execution | Return valid=True with warning on API errors |
| Performance impact | Run validations in parallel where possible |
| False positives | Log all validation decisions for debugging |

## Success Metrics

1. **Zero execution failures** due to DRS service limits
2. **100% validation coverage** of all DRS quotas
3. **<500ms latency** added to execution start
4. **Clear error messages** for all limit violations

## References

- [AWS DRS Service Limits Research](../research/AWS_DRS_SERVICE_LIMITS_AND_CAPABILITIES_RESEARCH.md)
- [AWS DRS Service Quotas](https://docs.aws.amazon.com/general/latest/gr/drs.html)
- [AWS DRS API Reference](https://docs.aws.amazon.com/drs/latest/APIReference/Welcome.html)
