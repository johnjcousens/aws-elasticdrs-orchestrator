# DRS Utils Analysis

## Current State

**File**: `infra/orchestration/drs-orchestration/lambda/shared/drs_utils.py`

### Existing Functions

1. **`normalize_drs_response()`**
   - Converts PascalCase DRS fields to camelCase
   - Handles nested objects and lists recursively
   - Has explicit mappings for common fields
   - Includes fix for AWS inconsistency (sourceServerID vs SourceServerID)

2. **`extract_recovery_instance_details()`**
   - Extracts key fields from DRS recovery instance
   - Returns normalized dict with: instanceId, recoveryInstanceId, sourceServerId, launchTime, etc.
   - Uses `normalize_drs_response()` internally

3. **`build_drs_filter()`**
   - Builds filter objects for DRS API queries
   - Supports filtering by source server IDs or recovery instance IDs

### Current Field Mappings

```python
field_map = {
    "RecoveryInstanceID": "recoveryInstanceId",
    "SourceServerID": "sourceServerId",
    "sourceServerID": "sourceServerId",      # AWS inconsistency fix
    "recoveryInstanceID": "recoveryInstanceId",  # AWS inconsistency fix
    "JobID": "jobId",
    "LaunchTime": "launchTime",
    "InstanceID": "instanceId",
    "InstanceType": "instanceType",
    "PrivateIpAddress": "privateIpAddress",
    "PublicIpAddress": "publicIpAddress",
    "LaunchStatus": "launchStatus",
    "launchStatus": "launchStatus",          # Already camelCase
    "LifeCycle": "lifeCycle",
    "LastLaunchResult": "lastLaunchResult",
}
```

## Required Enhancements for Multi-Wave Fix

### 1. EC2 Instance Enrichment Function

**Need**: Function to query EC2 and enrich server data with instance details

```python
def enrich_with_ec2_details(server_data: Dict, ec2_client) -> Dict:
    """
    Enrich server data with EC2 instance details.
    
    Queries EC2 DescribeInstances API and adds:
    - privateIp (from EC2 PrivateIpAddress)
    - hostname (from EC2 PrivateDnsName)
    - instanceType (from EC2 InstanceType)
    - instanceState (from EC2 State)
    
    Args:
        server_data: Server dict with at least instanceId
        ec2_client: boto3 EC2 client
        
    Returns:
        Enriched server data dict
    """
```

**Why**: Requirements FR-3.2, FR-3.4 - Need to query EC2 for instance details

### 2. DRS Job Status Enrichment Function

**Need**: Function to query DRS job status and extract participating servers

```python
def get_drs_job_details(job_id: str, drs_client) -> Dict:
    """
    Get DRS job details including participating servers.
    
    Queries DRS DescribeRecoveryInstances API and returns:
    - jobId
    - status
    - participatingServers (list)
    - startTime
    - endTime
    
    Args:
        job_id: DRS job ID
        drs_client: boto3 DRS client
        
    Returns:
        Normalized job details dict
    """
```

**Why**: Requirements FR-2.6, FR-3.1 - Need to query DRS for current job status

### 3. Server Data Normalization Function

**Need**: Function to normalize server data from multiple sources (DRS + EC2)

```python
def normalize_server_data(
    drs_server: Dict,
    ec2_instance: Dict = None
) -> Dict:
    """
    Normalize server data from DRS and EC2 sources.
    
    Combines data from:
    - DRS: sourceServerId, serverName, launchStatus, launchTime
    - EC2: instanceId, privateIp, hostname, instanceType
    
    Args:
        drs_server: DRS ParticipatingServer object
        ec2_instance: EC2 Instance object (optional)
        
    Returns:
        Normalized server dict for DynamoDB storage
    """
```

**Why**: Requirements FR-2.8, FR-3.5 - Need to combine and normalize data from multiple sources

### 4. Batch EC2 Query Function

**Need**: Function to query multiple EC2 instances efficiently

```python
def batch_describe_ec2_instances(
    instance_ids: List[str],
    ec2_client
) -> Dict[str, Dict]:
    """
    Query multiple EC2 instances in a single API call.
    
    Returns dict mapping instanceId -> instance details.
    Handles pagination and API throttling.
    
    Args:
        instance_ids: List of EC2 instance IDs
        ec2_client: boto3 EC2 client
        
    Returns:
        Dict mapping instanceId to normalized instance details
    """
```

**Why**: Requirements FR-3.6, FR-3.7 - Need to minimize API calls and handle throttling

### 5. Additional Field Mappings Needed

Add to `field_map`:

```python
# EC2-specific fields
"PrivateDnsName": "privateDnsName",
"PrivateIpAddress": "privateIpAddress",
"State": "state",
"StateReason": "stateReason",

# DRS Job fields
"ParticipatingServers": "participatingServers",
"StartDateTime": "startTime",
"EndDateTime": "endTime",
"Status": "status",

# Server name fields
"Hostname": "hostname",
"Tags": "tags",
```

## Strengths of Current Implementation

1. ✅ **Handles AWS Inconsistencies**: Already has fixes for sourceServerID vs SourceServerID
2. ✅ **Recursive Normalization**: Handles nested objects and lists
3. ✅ **Explicit Mappings**: Clear field mappings for common fields
4. ✅ **Fallback Logic**: Generic PascalCase to camelCase conversion
5. ✅ **Type Safety**: Uses type hints throughout
6. ✅ **Well Documented**: Clear docstrings and examples

## Gaps for New Requirements

1. ❌ **No EC2 Integration**: No functions to query or normalize EC2 data
2. ❌ **No Batch Operations**: No support for batch EC2 queries
3. ❌ **No Caching**: No caching mechanism for EC2 data (FR-3.7)
4. ❌ **No Throttling Handling**: No retry logic for API throttling (FR-3.6)
5. ❌ **No Server Name Extraction**: No logic to extract server name from tags or hostname
6. ❌ **Limited DRS Job Support**: No function to get full job details with participating servers

## Recommended Additions

### High Priority (Required for Multi-Wave Fix)

1. `enrich_with_ec2_details()` - Query EC2 for instance details
2. `normalize_server_data()` - Combine DRS + EC2 data
3. `batch_describe_ec2_instances()` - Efficient batch EC2 queries
4. Add EC2 field mappings to `field_map`

### Medium Priority (Performance & Reliability)

5. `get_drs_job_details()` - Query DRS job status
6. Add retry logic with exponential backoff for API calls
7. Add simple in-memory cache for EC2 data (TTL: 60 seconds)

### Low Priority (Nice to Have)

8. `extract_server_name()` - Extract server name from tags or hostname
9. Add CloudWatch metrics for API call counts
10. Add validation for required fields

## Implementation Strategy

### Phase 1: Core Enrichment Functions
- Add `enrich_with_ec2_details()`
- Add `normalize_server_data()`
- Add EC2 field mappings
- Update `extract_recovery_instance_details()` to use new functions

### Phase 2: Batch Operations
- Add `batch_describe_ec2_instances()`
- Add simple caching mechanism
- Add retry logic for throttling

### Phase 3: DRS Job Support
- Add `get_drs_job_details()`
- Add DRS job field mappings
- Update polling logic to use new function

## Testing Considerations

1. **Unit Tests**: Test each new function with mock DRS/EC2 responses
2. **Integration Tests**: Test with real AWS APIs in dev environment
3. **Edge Cases**:
   - Missing EC2 instances (not yet launched)
   - API throttling scenarios
   - Partial data (some fields missing)
   - Invalid instance IDs
   - Empty responses

## Backward Compatibility

All new functions are additive - no breaking changes to existing functions:
- ✅ `normalize_drs_response()` - No changes needed
- ✅ `extract_recovery_instance_details()` - Can be enhanced without breaking
- ✅ `build_drs_filter()` - No changes needed

Existing code will continue to work unchanged.

## Related Requirements

- **FR-2.6**: Poll operation SHALL enrich server data with current DRS state
- **FR-2.7**: Poll operation SHALL enrich server data with EC2 instance details
- **FR-2.8**: Poll operation SHALL normalize all DRS response data
- **FR-3.1**: Enrichment SHALL query DRS DescribeRecoveryInstances API
- **FR-3.2**: Enrichment SHALL query EC2 DescribeInstances API
- **FR-3.3**: Enrichment SHALL extract DRS fields
- **FR-3.4**: Enrichment SHALL extract EC2 fields
- **FR-3.5**: Enrichment SHALL normalize PascalCase to camelCase
- **FR-3.6**: Enrichment SHALL handle API throttling
- **FR-3.7**: Enrichment SHALL cache EC2 data
- **FR-3.8**: Enrichment SHALL update server data on every poll cycle

## Conclusion

The current `drs_utils.py` provides a solid foundation for normalization. We need to add:
1. EC2 integration functions
2. Batch query capabilities
3. Caching and throttling handling
4. Additional field mappings

All additions can be made without breaking existing functionality.
