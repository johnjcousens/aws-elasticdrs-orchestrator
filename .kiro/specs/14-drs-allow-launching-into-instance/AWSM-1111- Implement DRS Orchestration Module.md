# AWSM-1111: DRS Orchestration Module

## User Story

As a DR Operations Engineer, I want integration with AWS DRS service for failback operations, so that I can return workloads to the original source instances in the primary region after a disaster recovery event.

## Acceptance Criteria

* EC2 instances can be recovered using AWS DRS service
* DRS recovery jobs are created and monitored
* Launch configurations can be applied before recovery
* Recovery job status is tracked and reported
* Instance IDs and status are captured after recovery
* Cross-account DRS operations are supported
* Failback operations can launch into original source instances (stopped in primary region)

## Implementation Status

**Basic DRS Integration**: Implemented  
**AllowLaunchingIntoThisInstance Pattern for Failback**: Not Implemented (Future Enhancement)

---

## What's Actually Implemented

The codebase contains basic AWS DRS integration for EC2 instance recovery. The AllowLaunchingIntoThisInstance pattern described in this document is a future enhancement that has not been implemented.

### Implemented Features

#### 1. DRS Recovery Job Creation

**Location**: `lambda/orchestration-stepfunctions/index.py` (line 777)

```python
# Start DRS recovery job
response = drs_client.start_recovery(
    isDrill=is_drill,
    sourceServers=source_servers
)
job_id = response["job"]["jobID"]
```

**GitHub**: https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/orchestration-stepfunctions/index.py#L777

#### 2. DRS Launch Configuration Updates

**Location**: `lambda/orchestration-stepfunctions/index.py` (line 242)

```python
# Update DRS launch settings
drs_client.update_launch_configuration(**drs_update)
```

Supports configuration of:
- `copyPrivateIp`: Preserve source server private IP
- `copyTags`: Copy source server tags to recovery instance
- `licensing`: OS licensing configuration
- `targetInstanceTypeRightSizingMethod`: Instance sizing strategy
- `launchDisposition`: Launch behavior (STARTED/STOPPED)

**GitHub**: https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/orchestration-stepfunctions/index.py#L242

#### 3. Tag-Based Server Discovery

**Location**: `lambda/orchestration-stepfunctions/index.py` (line 744+)

Resolves DRS source servers by querying for servers matching specified tags. Enables dynamic server discovery without maintaining static server lists.

**GitHub**: https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/orchestration-stepfunctions/index.py#L744

#### 4. DRS Job Status Monitoring

**Location**: `lambda/execution-handler/index.py`

Polls DRS job status and tracks individual server launch states. Updates execution history with recovery progress.

**GitHub**: https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/execution-handler/index.py

#### 5. Cross-Account DRS Operations

**Location**: `lambda/shared/cross_account.py`

Creates DRS clients with cross-account IAM role assumption for hub-and-spoke architecture.

```python
def create_drs_client(region: str, account_context: Optional[Dict] = None):
    """Create DRS client with optional cross-account role assumption"""
```

**GitHub**: https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/shared/cross_account.py

---

## What's NOT Implemented (Future Enhancements)

### AllowLaunchingIntoThisInstance Pattern for Failback

The `AWSDRS=AllowLaunchingIntoThisInstance` tag pattern for failback operations is NOT implemented in the codebase. This is a future enhancement.

**Use Case**: Failback to Original Instance After DR Event

After failing over to the DR region, this feature enables returning workloads to the **original source instances** in the primary region instead of creating new instances.

**Workflow**:
```
1. DR Event Occurs → Failover to DR region (creates new recovery instances)
2. Primary region restored → Original source instances are stopped
3. Failback initiated → DRS launches into original stopped instances
4. Result: Workloads running on original instances with original IPs/metadata
```

**What This Pattern Would Do**:

1. Identify original source instances (now stopped) in primary region
2. Tag them with `AWSDRS=AllowLaunchingIntoThisInstance`
3. Configure DRS to launch into these specific instances
4. Replace EBS volumes with recovered data from DR region
5. Start instances with recovered data
6. Preserve original instance ID, IP address, and network configuration

**Why It's Not Implemented**:

- No code exists for EC2 instance discovery by `AWSDRS` tag
- No code exists for `launchIntoInstanceProperties` configuration
- No code exists for Name tag matching between DR instances and original source instances
- No code exists for failback orchestration logic

**Implementation Would Require**:

```python
# FUTURE ENHANCEMENT - NOT YET IMPLEMENTED

# 1. After DR event, identify original source instances (now stopped)
response = ec2_client.describe_instances(
    Filters=[
        {'Name': 'tag:Name', 'Values': [server_hostname]},
        {'Name': 'instance-state-name', 'Values': ['stopped']},
        {'Name': 'tag:OriginalSourceInstance', 'Values': ['true']}
    ]
)

# 2. Tag for failback
ec2_client.create_tags(
    Resources=[original_instance_id],
    Tags=[
        {'Key': 'AWSDRS', 'Value': 'AllowLaunchingIntoThisInstance'}
    ]
)

# 3. Configure DRS to launch into original instance
drs_client.update_launch_configuration(
    sourceServerID=dr_source_server_id,  # DR region source server
    launchIntoInstanceProperties={
        'launchIntoEC2InstanceID': original_instance_id  # Primary region instance
    }
)

# 4. Start failback recovery
drs_client.start_recovery(
    sourceServers=[{'sourceServerID': dr_source_server_id}],
    isDrill=False  # Production failback
)
```

**Key Benefits of Failback to Original Instance**:
- Preserves original instance ID (no application reconfiguration needed)
- Maintains original private IP address (no DNS changes)
- Keeps original security groups and network interfaces
- Faster than creating new instances
- Reduces operational complexity

---

## Shared Utilities Used

The DRS orchestration implementation uses these shared utility modules:

### 1. `lambda/shared/cross_account.py`

**Purpose**: Cross-account IAM role assumption for hub-and-spoke architecture

**Key Functions**:
- `create_drs_client(region, account_context)`: Creates DRS client with optional cross-account role assumption
- `determine_target_account_context(plan)`: Determines which account contains DRS servers
- `get_current_account_id()`: Gets current AWS account ID via STS

**Usage**:
```python
from shared.cross_account import create_drs_client, determine_target_account_context

# Determine target account from recovery plan
account_context = determine_target_account_context(recovery_plan)

# Create DRS client for target account
drs_client = create_drs_client(region="us-east-1", account_context=account_context)
```

**GitHub**: https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/shared/cross_account.py

### 2. `lambda/shared/drs_utils.py`

**Purpose**: DRS API response normalization and data transformation

**Key Functions**:
- `normalize_drs_response(drs_data)`: Converts DRS PascalCase fields to camelCase
- `extract_recovery_instance_details(drs_instance)`: Extracts normalized instance details
- `transform_drs_server_for_frontend(server)`: Transforms DRS server to frontend format
- `enrich_server_data(servers, drs_client, ec2_client)`: Enriches server data with DRS details

**Usage**:
```python
from shared.drs_utils import normalize_drs_response, enrich_server_data

# Normalize DRS API response
normalized = normalize_drs_response(drs_response)

# Enrich server data with DRS source server details
enriched_servers = enrich_server_data(participating_servers, drs_client, ec2_client)
```

**GitHub**: https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/shared/drs_utils.py

### 3. `lambda/shared/conflict_detection.py`

**Purpose**: Detects server conflicts between executions and active DRS jobs

**Key Functions**:
- `check_server_conflicts(plan, account_context)`: Checks for server conflicts
- `query_drs_servers_by_tags(region, tags, account_context)`: Queries DRS servers by tags
- `get_active_executions_for_plan(plan_id)`: Gets active executions for a plan

**Usage**:
```python
from shared.conflict_detection import check_server_conflicts, query_drs_servers_by_tags

# Check for conflicts before starting execution
conflicts = check_server_conflicts(recovery_plan, account_context)

# Query DRS servers matching tags
servers = query_drs_servers_by_tags(region, {"Environment": "prod"}, account_context)
```

**GitHub**: https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/shared/conflict_detection.py

### 4. `lambda/shared/drs_limits.py`

**Purpose**: DRS service limit validation

**Key Functions**:
- `validate_wave_sizes(plan)`: Validates wave sizes (max 100 servers per wave)
- `validate_concurrent_jobs(region)`: Validates concurrent jobs (max 20)
- `validate_servers_in_all_jobs(region, new_server_count)`: Validates servers in jobs (max 500)
- `validate_server_replication_states(region, server_ids)`: Validates replication health

**Usage**:
```python
from shared.drs_limits import validate_wave_sizes, validate_concurrent_jobs

# Validate wave sizes before execution
errors = validate_wave_sizes(recovery_plan)

# Validate concurrent jobs
result = validate_concurrent_jobs(region="us-east-1")
```

**GitHub**: https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/shared/drs_limits.py

### 5. `lambda/shared/account_utils.py`

**Purpose**: Account management utilities

**Key Functions**:
- `construct_role_arn(account_id)`: Constructs standardized role ARN
- `get_target_accounts()`: Gets list of registered target accounts
- `validate_target_account(account_id)`: Validates target account access

**GitHub**: https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/shared/account_utils.py

### 6. `lambda/shared/config_merge.py`

**Purpose**: Per-server launch configuration overrides

**Key Functions**:
- `get_effective_launch_config(protection_group, server_id)`: Merges group defaults with per-server overrides

**Usage**:
```python
from shared.config_merge import get_effective_launch_config

# Get effective config for server (group defaults + per-server overrides)
effective_config = get_effective_launch_config(protection_group, server_id)
```

**GitHub**: https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/shared/config_merge.py

---

## DRS API Integration

The platform implements standard DRS API operations for recovery orchestration. For complete API call sequences, status progressions, and response structures, see:

**DRS Execution Walkthrough**: https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/docs/guides/DRS_EXECUTION_WALKTHROUGH.md

### Implemented DRS API Calls

- `start_recovery()` - Creates DRS recovery jobs
- `update_launch_configuration()` - Updates launch settings before recovery
- `describe_source_servers()` - Queries source servers for tag-based discovery
- `describe_jobs()` - Monitors job status and progress

**Implementation Locations**:
- Recovery job creation: https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/orchestration-stepfunctions/index.py#L777
- Launch configuration: https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/orchestration-stepfunctions/index.py#L242
- Server discovery: https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/orchestration-stepfunctions/index.py#L744

---

## Architecture Pattern

### Wave-Based Execution

DRS recovery follows a wave-based execution model with sequential waves and parallel execution within each wave. For complete architecture details, see:

**Wave-Based Orchestration**: https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/archive/docs/HealthEdge/Cloud%20Migration/Disaster%20Recovery/7-Implementation%20%26%20Runbooks/Enterprise%20DR%20Orchestration%20Platform%20Design%201.0%20--/AWSM-1103-Enterprise-Wave-Orchestration.md

### Cross-Account Hub-and-Spoke

DRS operations support cross-account architecture where the hub account orchestrates recovery across multiple spoke accounts.

**Implementation**: https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/lambda/shared/cross_account.py

---

## Future Enhancements

### 1. AllowLaunchingIntoThisInstance Pattern

Launch DRS recovery into pre-provisioned EC2 instances to preserve instance identity.

**Benefits**:
- Maintains instance ID, metadata, and network configuration
- Faster recovery (no instance launch time)
- Cost efficiency (reuses existing instances)

**Implementation Required**:
- EC2 instance discovery by `AWSDRS` tag
- Name tag matching between primary and DR instances
- `launchIntoInstanceProperties` configuration
- Failback operation support

### 2. Failback Operations

Return to primary region after DR event.

**Implementation Required**:
- Reverse replication direction
- Launch into original source instances
- Validate data consistency

### 3. Enhanced Monitoring

Real-time DRS job progress tracking.

**Implementation Required**:
- CloudWatch metrics for DRS operations
- SNS notifications for job status changes
- Dashboard for recovery progress

---

## Testing Considerations

### Unit Tests

Test DRS API integration with mocked boto3 clients:

```python
from unittest.mock import patch

with patch('boto3.client') as mock_client:
    mock_drs = mock_client.return_value
    mock_drs.start_recovery.return_value = {
        "job": {"jobID": "drsjob-123"}
    }
    
    result = start_wave_recovery(state, wave_number=0)
    assert result["job_id"] == "drsjob-123"
```

### Integration Tests

Test with actual DRS service:

```python
# Create test source server
# Configure launch settings
# Start drill recovery
# Monitor job status
# Validate recovery instance
# Terminate recovery instance
```

---

## Related Documentation

- [DRS Service Limits](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/docs/reference/DRS_SERVICE_LIMITS_AND_CAPABILITIES.md)
- [Cross-Account Setup](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/docs/guides/DRS_CROSS_ACCOUNT_SETUP_VERIFICATION.md)
- [Wave-Based Orchestration](https://code.aws.dev/personal_projects/alias_j/jocousen/aws-elasticdrs-orchestrator/blob/main/docs/analysis/AWSM-1103-Enterprise-Wave-Orchestration.md)

**Technical Approach**:

* Pre-provisioned instances identified by matching Name tags between regions
* DRS launch configuration updated with `launchIntoInstanceProperties.launchIntoEC2InstanceID`
* AllowLaunchingIntoThisInstance preserves IP address last octet and instance identity
* Target instance must be stopped before recovery
* Archive code shows this pattern working in enterprise DR orchestration

**Implementation Plan**:


```py
# PLANNED CODE - NOT YET IMPLEMENTED
# File: lambda/shared/drs_client.py

def configure_allow_launching_into_instance(
    source_server_id: str,
    target_instance_id: str,
    target_subnet_id: str,
    target_security_groups: List[str]
) -> Dict:
    """
    Configure DRS to use AllowLaunchingIntoThisInstance pattern.
    
    NOTE: This function is PLANNED but NOT YET IMPLEMENTED.
    """
    # Implementation details in research document
    pass
```


**Reference**: See research document Phase 2 for detailed implementation plan.

---

### 📋 Criterion 3: Name Tag Matching for Primary-DR Pairs

**Requirement**: *Given* primary-DR instance pairs, *When* identifying target instances, *Then* Name tags are matched between primary and DR region instances.

**Status**: 🔴 **NOT IMPLEMENTED**

**Technical Approach**:

* Name tag matching algorithm can find corresponding instances across regions
* Naming convention: `{customer}-{environment}-{workload}-{role}` (e.g., `acme-prod-web-app01`)
* Fuzzy matching can handle minor naming variations (case-insensitive, whitespace-tolerant)
* 1:1 mapping validation ensures no duplicate matches
* Archive code shows this pattern working successfully

**Implementation Plan**:


```py
# PLANNED CODE - NOT YET IMPLEMENTED
# File: lambda/shared/instance_matcher.py

def match_primary_dr_instances(
    primary_instances: List[Dict],
    dr_instances: List[Dict]
) -> Dict[str, str]:
    """
    Match primary region instances to DR region instances by Name tag.
    
    NOTE: This function is PLANNED but NOT YET IMPLEMENTED.
    """
    # Implementation details in research document
    pass
```


**Reference**: See research document for name matching algorithm details.

---

### 📋 Criterion 4: AllowLaunchingIntoThisInstance for Failback

**Requirement**: *Given* failback operation, *When* returning to primary region, *Then* AllowLaunchingIntoThisInstance is used to launch into original source instances.

**Status**: 🔴 **NOT IMPLEMENTED**

**Technical Approach**:

* Failback reverses the failover process: DR → Primary
* Original source instances (now stopped in primary region) become targets
* DRS launch configuration updated to launch into original instances
* Instance identity can be preserved during round-trip (failover + failback)
* Metadata tracking required to ensure correct instance pairing for failback

**Implementation Plan**: See research document Phase 2 for failback implementation details.

---

### 📋 Criterion 5: DRS Recovery Job Monitoring

**Requirement**: *Given* DRS recovery job, *When* job is in progress, *Then* job status is monitored and reported.

**Status**: 🔴 **NOT IMPLEMENTED**

**Technical Approach**:

* Polling mechanism should check job status every 30 seconds
* Job states: PENDING → STARTED → COMPLETED / FAILED
* CloudWatch metrics can track job duration and success rate
* SNS notifications for job completion or failure
* Step Functions wait state can handle long-running jobs (up to 2 hours)

**Implementation Plan**: Detailed implementation code samples provided in "Detailed Implementation Plan" section below.

---

### 📋 Criterion 6: Instance ID and Status Capture

**Requirement**: *Given* DRS recovery completion, *When* instances are launched, *Then* instance IDs and status are captured for validation.

**Status**: 🔴 **NOT IMPLEMENTED**

**Technical Approach**:

* Recovery instance IDs can be captured from DRS API response
* Instance status validation: running, network accessible, application healthy
* Metadata should be stored in DynamoDB: instance ID, IP address, launch time, validation status
* Validation should include: EC2 status checks, network connectivity, application health checks

**Implementation Plan**: Detailed implementation code samples provided in "Detailed Implementation Plan" section below.

---

Definition of Done - Implementation Checklist
---------------------------------------------

### 📋 1. DRS API Integration with AllowLaunchingIntoThisInstance

**Status**: 🔴 **NOT STARTED**

**Planned Implementation**:

* DRS API wrapper with `start_recovery`, `update_launch_configuration`, `describe_recovery_instances`
* AllowLaunchingIntoThisInstance configuration via `launchIntoInstanceProperties`
* Support for failover (primary → DR) and failback (DR → primary)
* IP address preservation with `copyPrivateIp=True`
* Tag copying with `copyTags=True`

**Planned Code Location**:

* DRS Client: `lambda/shared/drs_client.py` (to be created)
* Launch Configuration: `lambda/shared/drs_client.py` (to be created)

**Planned Verification**:


```bash
# Test DRS API integration (NOT YET IMPLEMENTED)
pytest tests/unit/test_drs_api_integration.py -v

# Expected: 18 tests covering DRS API operations
```


**Reference**: See research document Section 3.2 for detailed API integration plan.

---

### 📋 2. Name Tag Matching Logic

**Status**: 🔴 **NOT STARTED**

**Planned Implementation**:

* Name tag matching algorithm with normalization (lowercase, strip whitespace)
* 1:1 mapping validation between primary and DR instances
* Fuzzy matching for minor naming variations
* Unmatched instance logging and alerting

**Planned Code Location**:

* Instance Matcher: `lambda/shared/instance_matcher.py` (to be created)
* Matching Tests: `tests/unit/test_instance_matching.py` (to be created)

**Planned Verification**:


```bash
# Test name tag matching (NOT YET IMPLEMENTED)
pytest tests/unit/test_instance_matching.py -v

# Expected: 12 tests covering name matching scenarios
```


**Reference**: See research document Section 3.3 for name matching algorithm.

---

### 3. Recovery Job Creation for Failover and Failback

**Planned Implementation**:

* Failover job creation: primary region instances → DR region targets
* Failback job creation: DR region instances → original primary instances
* Batch processing (up to 20 servers per job)
* Job metadata tracking in DynamoDB

**Planned Code Location**:

* Job Creation: `lambda/orchestration-stepfunctions/index.py` (to be created)
* Failback Logic: `lambda/orchestration-stepfunctions/index.py` (to be created)

**Planned Verification**:

```bash
# Test recovery job creation
pytest tests/integration/test_drs_recovery_jobs.py -v

# Expected: 15 tests covering job creation scenarios
```

**Reference**: See research document Section 4 for job creation workflow.

---

### 4. Job Status Monitoring

**Planned Implementation**:

* Polling mechanism with 30-second intervals
* Job state tracking: PENDING → STARTED → COMPLETED / FAILED
* CloudWatch metrics: job duration, success rate, failure count
* SNS notifications on completion/failure
* Step Functions wait state for long-running jobs

**Planned Code Location**:

* Job Monitor: `lambda/shared/drs_job_monitor.py` (to be created)
* Metrics Publisher: `lambda/shared/cloudwatch_metrics.py` (to be created)

**Planned Verification**:

```bash
# Test job monitoring
pytest tests/integration/test_drs_job_monitoring.py -v

# Expected: 10 tests covering monitoring scenarios
```

**Reference**: See research document Section 5 for monitoring design.

---

### 5. Error Handling for DRS API Failures

**Planned Implementation**:

* Exponential backoff retry for rate limits (see AWSM-1112 rate limit ticket)
* Specific error handling for DRS API errors: InvalidParameterException, ResourceNotFoundException
* Validation errors logged with detailed context
* Failed operations stored in DynamoDB for retry
* SNS alerts for critical failures

**Planned Code Location**:

* Error Handler: `lambda/shared/drs_error_handler.py` (to be created)
* Retry Logic: `lambda/shared/drs_client.py` (to be created)

**Planned Verification**:

```bash
# Test error handling
pytest tests/unit/test_drs_error_handling.py -v

# Expected: 14 tests covering error scenarios
```

**Reference**: See research document Section 6 for error handling strategy.

---

### 6. Integration Tests with DRS Service

**Planned Test Coverage**:

* Unit tests: 59 tests covering DRS API integration, name matching, job creation
* Integration tests: 37 tests with real DRS API calls and pre-provisioned instances
* End-to-end tests: 8 tests validating complete failover/failback cycles
* Performance tests: 3 tests with 10, 50, and 100 instance recoveries

**Planned Test Suite**:

```
tests/unit/test_drs_api_integration.py ............ 18 tests (to be created)
tests/unit/test_instance_matching.py ............ 12 tests (to be created)
tests/unit/test_drs_error_handling.py ........... 14 tests (to be created)
tests/unit/test_allow_launching_into_instance.py . 15 tests (to be created)
tests/integration/test_drs_recovery_jobs.py ..... 15 tests (to be created)
tests/integration/test_drs_job_monitoring.py .... 10 tests (to be created)
tests/integration/test_failover_failback.py ..... 12 tests (to be created)
tests/e2e/test_complete_dr_cycle.py ............. 8 tests (to be created)

Total: 0/104 tests exist (104 planned)
```

**Planned Integration Test Scenarios**:

* Failover with 10 pre-provisioned instances
* Failback to original instances
* Name tag matching with 100 instance pairs
* Job monitoring with concurrent recoveries
* Error handling with simulated API failures

**Reference**: See research document Section 7 for test plan details.

---

DRS Launch Configuration Architecture
-------------------------------------

DRS uses a two-level configuration system. Understanding both levels is essential for AllowLaunchingIntoThisInstance implementation.

### Two-Level Configuration System

**Level 1: DRS Launch Configuration** (API-Managed)

* Managed through DRS APIs (`update_launch_configuration`)
* High-level recovery settings
* **AllowLaunchingIntoThisInstance is configured at this level**

**Level 2: EC2 Launch Template** (Customer-Editable)

* Managed through EC2 APIs or console
* Low-level instance settings
* DRS will NOT override customer changes

### DRS Launch Configuration Settings

**Settings Managed via DRS API**:

| Setting | API Field | Values | Purpose |
| --- | --- | --- | --- |
| **Launch Into Instance** | `launchIntoInstanceProperties.launchIntoEC2InstanceID` | EC2 Instance ID | Launch into existing instance |
| **Launch Disposition** | `launchDisposition` | `STOPPED`, `STARTED` | Auto-start after recovery |
| **Copy Private IP** | `copyPrivateIp` | `true`, `false` | Copy source IP to recovery |
| **Copy Tags** | `copyTags` | `true`, `false` | Copy source tags to recovery |
| **Right Sizing** | `targetInstanceTypeRightSizingMethod` | `NONE`, `BASIC`, `IN_AWS` | Instance type selection |
| **Licensing** | `licensing.osByol` | `true`, `false` | Bring your own license |

**Configuration Example**:


```py
# Configure AllowLaunchingIntoThisInstance
drs_client.update_launch_configuration(
    sourceServerID='s-1234567890abcdef0',
    launchIntoInstanceProperties={
        'launchIntoEC2InstanceID': 'i-target-instance-id'
    },
    targetInstanceTypeRightSizingMethod='NONE',  # Use existing instance type
    copyPrivateIp=False,  # Keep existing IP
    copyTags=True,  # Sync tags
    launchDisposition='STARTED'  # Start after recovery
)
```


### EC2 Launch Template Settings

**Customer Can Safely Modify** (Based on AWS Configuration Synchronizer):

| Setting | Purpose | Example |
| --- | --- | --- |
| **IamInstanceProfile** | Instance IAM role | Application permissions |
| **SecurityGroupIds** | Security groups | Network security |
| **TagSpecifications** | Instance/volume tags | Organization/billing |
| **Monitoring** | CloudWatch monitoring | `{"Enabled": true}` |
| **EbsOptimized** | EBS optimization | `true`/`false` |
| **DisableApiTermination** | Termination protection | Production safety |
| **MetadataOptions** | Instance metadata | Security hardening |
| **NetworkInterfaces.SubnetId** | Recovery subnet | Network placement |

**DRS Manages (Do NOT Modify)**:

| Setting | Why DRS Manages |
| --- | --- |
| **ImageId** | DRS creates recovery-specific AMIs |
| **UserData** | DRS may inject recovery scripts |
| **BlockDeviceMappings** | DRS manages disk mappings from source |
| **NetworkInterfaces.PrivateIpAddress** | DRS manages IP assignment |

### AllowLaunchingIntoThisInstance Configuration Pattern

**Two-Step Configuration Process**:


```py
# Step 1: Disable conflicting DRS settings
drs_client.update_launch_configuration(
    sourceServerID='s-1234567890abcdef0',
    copyTags=False,  # Tags managed separately
    copyPrivateIp=False,  # Preserve target instance IP
    targetInstanceTypeRightSizingMethod='NONE',  # Use existing instance type
    launchDisposition='STOPPED'  # Controlled recovery
)

# Step 2: Configure launch-into-instance
drs_client.update_launch_configuration(
    sourceServerID='s-1234567890abcdef0',
    launchIntoInstanceProperties={
        'launchIntoEC2InstanceID': 'i-target-instance-id'
    }
)
```


**Why Two Steps**:

* Prevents conflicts between DRS settings and pre-provisioned instance configuration
* Ensures DRS doesn't try to modify target instance properties
* Based on working SSM automation pattern

### Launch Template Validation

**Validate Target Instance Configuration**:


```py
def validate_target_instance_launch_template(instance_id: str) -> bool:
    """Validate target instance launch template is compatible"""
    
    # Get instance details
    ec2_response = ec2_client.describe_instances(InstanceIds=[instance_id])
    instance = ec2_response['Reservations'][0]['Instances'][0]
    
    # Verify AWSDRS tag
    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
    if tags.get('AWSDRS') != 'AllowLaunchingIntoThisInstance':
        raise ValueError("Missing AWSDRS=AllowLaunchingIntoThisInstance tag")
    
    # Verify instance is stopped
    if instance['State']['Name'] != 'stopped':
        raise ValueError("Target instance must be stopped")
    
    # Get launch template (if exists)
    launch_template_id = instance.get('LaunchTemplateId')
    if launch_template_id:
        template_response = ec2_client.describe_launch_template_versions(
            LaunchTemplateId=launch_template_id,
            Versions=['$Latest']
        )
        
        template_data = template_response['LaunchTemplateVersions'][0]['LaunchTemplateData']
        
        # Verify no DRS-managed fields are set
        if template_data.get('ImageId'):
            print("⚠️  Warning: ImageId set in launch template (DRS will override)")
        
        if template_data.get('UserData'):
            print("⚠️  Warning: UserData set in launch template (DRS may override)")
    
    return True
```


### HRP Implementation Patterns (Adapted from AWS Labs)

**Reference**: AWS DRS Settings Tool provides production-tested patterns adapted for HRP's manifest-driven, Module Factory architecture.

**Key Patterns Adapted for HRP**:

1. **Module Factory Adapter Pattern** (Replaces Object-Oriented Settings Classes):


```py
# HRP Pattern: DRS adapter following Module Factory with 4-phase lifecycle
class DRSAdapter(TechnologyAdapter):
    """DRS adapter for AllowLaunchingIntoThisInstance pattern"""
    
    def instantiate(self, resources: List[Dict]) -> Dict:
        """Phase 1: Configure AllowLaunchingIntoThisInstance from manifest"""
        for resource in resources:
            manifest = resource.get('manifest', {})
            
            # Manifest-driven configuration (not CSV)
            launch_config = {
                'sourceServerID': resource['sourceServerID'],
                'launchIntoInstanceProperties': {
                    'launchIntoEC2InstanceID': manifest['targetInstanceId']
                },
                'copyPrivateIp': manifest.get('copyPrivateIp', False),
                'copyTags': manifest.get('copyTags', True),
                'targetInstanceTypeRightSizingMethod': 'NONE',
                'launchDisposition': 'STOPPED'
            }
            
            self._update_launch_configuration(launch_config)
    
    def activate(self, resources: List[Dict]) -> Dict:
        """Phase 2: Start recovery jobs"""
        pass
    
    def cleanup(self, resources: List[Dict]) -> Dict:
        """Phase 3: Cleanup temporary resources"""
        pass
    
    def replicate(self, resources: List[Dict]) -> Dict:
        """Phase 4: Re-establish replication"""
        pass
```


2. **Manifest Validation + Clean API Calls** (Replaces Delete None Pattern):


```py
# HRP Pattern: Manifest validation upstream, adapter receives clean data
class DRSAdapter(TechnologyAdapter):
    
    def _build_launch_config(self, manifest: Dict) -> Dict:
        """Build DRS launch configuration from validated manifest"""
        config = {
            'sourceServerID': manifest['sourceServerID'],
            'launchIntoInstanceProperties': {
                'launchIntoEC2InstanceID': manifest['targetInstanceId']
            }
        }
        
        # Only add optional fields if present in manifest
        if 'copyPrivateIp' in manifest:
            config['copyPrivateIp'] = manifest['copyPrivateIp']
        
        if 'copyTags' in manifest:
            config['copyTags'] = manifest['copyTags']
        
        if 'launchDisposition' in manifest:
            config['launchDisposition'] = manifest['launchDisposition']
        
        return config  # Already clean - no None values
```


3. **DynamoDB State Tracking** (Replaces Change Detection Pattern):


```py
# HRP Pattern: DynamoDB-based state management for idempotency
class DRSAdapter(TechnologyAdapter):
    
    def instantiate(self, resources: List[Dict]) -> Dict:
        """Configure with idempotency via DynamoDB state"""
        for resource in resources:
            # Check DynamoDB for last known configuration
            current_state = self._get_resource_state(resource['sourceServerID'])
            desired_state = self._build_launch_config(resource['manifest'])
            
            # Only update if configuration changed
            if current_state != desired_state:
                self._update_launch_configuration(desired_state)
                
                # Store new state in DynamoDB
                self._save_resource_state(
                    resource['sourceServerID'],
                    desired_state,
                    status='configured'
                )
            else:
                logger.info(f"Configuration unchanged for {resource['sourceServerID']}")
```


4. **Cross-Account Role Assumption** (Replaces Multi-Account Session Management):


```py
# HRP Pattern: STS AssumeRole with IAM cross-account roles
class DRSAdapter(TechnologyAdapter):
    
    def _get_cross_account_client(self, account_id: str, service: str):
        """Assume cross-account role for target account"""
        role_arn = f"arn:aws:iam::{account_id}:role/DROrchestrationCrossAccountRole"
        
        response = self.sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=f'DROrchestration-{service}',
            DurationSeconds=3600
        )
        
        credentials = response['Credentials']
        
        return boto3.client(
            service,
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )
    
    def instantiate(self, resources: List[Dict]) -> Dict:
        """Use cross-account clients for DRS operations"""
        for resource in resources:
            account_id = resource['accountId']
            
            # Get DRS client for target account
            drs_client = self._get_cross_account_client(account_id, 'drs')
            
            # Configure AllowLaunchingIntoThisInstance
            drs_client.update_launch_configuration(...)
```


5. **Wave-Based Orchestration** (Replaces Bulk Configuration Management):


```py
# HRP Pattern: Wave-based with Step Functions + parallel Lambda execution
class DRSAdapter(TechnologyAdapter):
    
    def instantiate(self, resources: List[Dict]) -> Dict:
        """Process resources by wave with parallel execution"""
        results = []
        
        # Group by wave (from dr:wave tag)
        waves = self._group_by_wave(resources)
        
        for wave_num, wave_resources in waves.items():
            logger.info(f"Processing Wave {wave_num}: {len(wave_resources)} resources")
            
            # Parallel execution within wave (up to 20 concurrent)
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [
                    executor.submit(self._configure_resource, resource)
                    for resource in wave_resources
                ]
                
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Configuration failed: {e}")
                        results.append({'status': 'failed', 'error': str(e)})
        
        return {
            'totalResources': len(resources),
            'successful': len([r for r in results if r['status'] == 'success']),
            'failed': len([r for r in results if r['status'] == 'failed']),
            'results': results
        }
```


6. **Tag-Driven Validation** (Replaces Settings Validation Pattern):


```py
# HRP Pattern: Tag-driven validation during discovery phase
class DRSAdapter(TechnologyAdapter):
    
    def _validate_resource(self, resource: Dict) -> bool:
        """Validate resource meets AllowLaunchingIntoThisInstance requirements"""
        
        # Tag validation (already filtered by Resource Explorer)
        required_tags = ['dr:enabled', 'dr:recovery-strategy', 'AWSDRS']
        for tag in required_tags:
            if tag not in resource.get('tags', {}):
                raise ValueError(f"Missing required tag: {tag}")
        
        # Validate AWSDRS tag value
        if resource['tags']['AWSDRS'] != 'AllowLaunchingIntoThisInstance':
            raise ValueError("Invalid AWSDRS tag value")
        
        # Validate target instance state
        target_instance_id = resource['manifest']['targetInstanceId']
        ec2_client = self._get_cross_account_client(resource['accountId'], 'ec2')
        
        response = ec2_client.describe_instances(InstanceIds=[target_instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        
        if instance['State']['Name'] != 'stopped':
            raise ValueError(f"Target instance must be stopped: {target_instance_id}")
        
        # Validate DRS replication state
        drs_client = self._get_cross_account_client(resource['accountId'], 'drs')
        
        response = drs_client.describe_source_servers(
            filters={'sourceServerIDs': [resource['sourceServerID']]}
        )
        
        replication_state = response['items'][0]['dataReplicationInfo']['dataReplicationState']
        if replication_state != 'CONTINUOUS':
            raise ValueError(f"Replication not ready: {replication_state}")
        
        return True
```


### HRP vs AWS Labs Pattern Comparison

| Pattern | AWS Labs (CSV-driven) | HRP (Manifest-driven) |
| --- | --- | --- |
| **Configuration Source** | CSV files | Tag-driven discovery + DynamoDB manifests |
| **Architecture** | Standalone scripts | Module Factory adapters (4-phase lifecycle) |
| **State Management** | In-memory object comparison | DynamoDB state tracking |
| **Multi-Account** | AWS CLI profiles | STS AssumeRole with IAM cross-account roles |
| **Orchestration** | Sequential processing | Wave-based with Step Functions + parallel Lambda |
| **Validation** | Manual validation functions | Tag-driven discovery filters + adapter validation |
| **Execution Model** | Batch script | Event-driven orchestration (CLI → Step Functions → Lambda) |

### Configuration Best Practices

**For AllowLaunchingIntoThisInstance**:

1. **Use NONE for Right Sizing**: Let target instance define the instance type

   
```py
targetInstanceTypeRightSizingMethod='NONE'
```

2. **Disable IP Copying**: Preserve target instance's existing IP

   
```py
copyPrivateIp=False
```

3. **Control Launch Disposition**: Use STOPPED for validation before starting

   
```py
launchDisposition='STOPPED'
```

4. **Tag Management**: Sync tags separately via existing tag sync capability

   
```py
copyTags=True  # Or False if using separate tag sync
```

5. **Launch Template**: Ensure target instance launch template doesn't conflict with DRS-managed fields
6. **Change Detection**: Compare current vs desired settings before API calls (AWS Labs pattern)
7. **Validation First**: Validate all prerequisites before configuration (AWS Labs pattern)
8. **Clean API Calls**: Remove None values from parameters (AWS Labs pattern)

### Configuration Validation Checklist

Before configuring AllowLaunchingIntoThisInstance:

* [ ] Target instance has `AWSDRS=AllowLaunchingIntoThisInstance` tag
* [ ] Target instance is in `stopped` state
* [ ] Target instance Name tag matches source server hostname
* [ ] Launch template (if exists) doesn't set ImageId or UserData
* [ ] Security groups are appropriate for recovery workload
* [ ] IAM instance profile has required permissions
* [ ] Subnet is in correct availability zone
* [ ] EBS volumes are properly configured

---

DRS Recovery Process Integration
--------------------------------

AllowLaunchingIntoThisInstance modifies the standard DRS recovery process.

### Standard DRS Recovery Flow (Without AllowLaunchingIntoThisInstance)


```
1. Pre-Recovery: Validate replication state = CONTINUOUS
2. Start Recovery: drs.start_recovery(isDrill=False)
3. DRS Creates: New EC2 instance from latest snapshot
4. DRS Launches: Instance with new instance ID, new IP
5. Result: Brand new instance (RTO: 2-4 hours)
```


### AllowLaunchingIntoThisInstance Recovery Flow (Modified)


```
1. Pre-Recovery: Validate replication state = CONTINUOUS
2. Configure Target: drs.update_launch_configuration(
     launchIntoInstanceProperties={'launchIntoEC2InstanceID': 'i-target'}
   )
3. Start Recovery: drs.start_recovery(isDrill=False)
4. DRS Stops: Target instance (if running)
5. DRS Replaces: EBS volumes on target instance
6. DRS Starts: Same instance with recovered data
7. Result: Existing instance preserved (RTO: 15-30 minutes)
```


### Key Differences

| Aspect | Standard Recovery | AllowLaunchingIntoThisInstance |
| --- | --- | --- |
| Instance ID | New instance ID | Preserves existing instance ID |
| Private IP | New IP address | Preserves existing IP address |
| Network Config | New ENI, security groups | Preserves ENI, security groups |
| RTO | 2-4 hours | 15-30 minutes |
| DNS Changes | Required | Not required |
| App Reconfig | Required | Not required |

### IAM Permission Requirement

When Lambda calls `drs:StartRecovery`, DRS uses the calling role's IAM permissions to perform EC2 operations, not the DRS service-linked role.

**Required Permissions for AllowLaunchingIntoThisInstance**:


```json
{
  "Effect": "Allow",
  "Action": [
    "ec2:StopInstances",
    "ec2:StartInstances",
    "ec2:DetachVolume",
    "ec2:AttachVolume",
    "ec2:DeleteVolume",
    "ec2:CreateVolume",
    "ec2:ModifyInstanceAttribute"
  ],
  "Resource": "*",
  "Condition": {
    "StringEquals": {
      "ec2:ResourceTag/AWSDRS": "AllowLaunchingIntoThisInstance"
    }
  }
}
```


### Failback Process with AllowLaunchingIntoThisInstance

**Failback Scenario**: After DR event, return workloads from DR region to original instances in primary region

**Standard Failback** (without AllowLaunchingIntoThisInstance):

```
1. Recovery instance running in DR region (new instance)
2. Reverse replication: DR → Primary (creates new staging)
3. Failback recovery: Creates NEW instance in primary region
4. Result: Yet another new instance (total: 3 instances created)
5. Original instance remains stopped and unused
```

**AllowLaunchingIntoThisInstance Failback** (preserves original):

```
1. Recovery instance running in DR region (new instance from failover)
2. Reverse replication: DR → Primary (to original source instance)
3. Configure failback target: Original source instance ID (stopped)
4. Failback recovery: Launches into ORIGINAL source instance
5. Result: Original instance restored (no new instances created)
```

**Key Advantage**: Returns to the exact same instance that was running before the DR event, preserving instance ID, IP address, and all metadata.


### Failback API Sequence


```py
# Phase 1: Initiate reverse replication
response = drs_client.reverse_replication(
    recoveryInstanceID='i-dr-region-instance'
)

# Phase 2: Monitor reverse replication
while True:
    response = drs_client.describe_recovery_instances(
        filters={'recoveryInstanceIDs': ['i-dr-region-instance']}
    )
    
    failback = response['items'][0].get('failback', {})
    state = failback.get('failbackReplicationState')
    
    if state == 'CONTINUOUS':
        lag = failback.get('failbackLagDuration')
        if parse_duration(lag) < 60:  # Less than 60 seconds
            break
    
    time.sleep(60)

# Phase 3: Configure failback to original instance
drs_client.update_launch_configuration(
    sourceServerID='s-dr-region-source',
    launchIntoInstanceProperties={
        'launchIntoEC2InstanceID': 'i-original-primary-instance'
    }
)

# Phase 4: Execute failback
response = drs_client.start_recovery(
    sourceServers=[{'sourceServerID': 's-dr-region-source'}],
    isDrill=False
)

# Phase 5: Finalize failback
drs_client.disconnect_recovery_instance(
    recoveryInstanceID='i-dr-region-instance'
)
```


### Recovery Job Monitoring

**Job Status Progression**:


```
PENDING (0-30s) → STARTED (30s-5m) → COMPLETED (5-15m)
```


**Per-Server Launch Status**:


```
PENDING → IN_PROGRESS → LAUNCHED
```


**Complete Response Structures**:

**Initial Response** (T+0s):


```json
{
  "job": {
    "jobID": "job-1234567890abcdef",
    "type": "LAUNCH",
    "initiatedBy": "START_RECOVERY",
    "status": "PENDING",
    "participatingServers": [{
      "sourceServerID": "s-1234567890abcdef0",
      "launchStatus": "PENDING"
    }]
  }
}
```


**In Progress** (T+3m):


```json
{
  "job": {
    "jobID": "job-1234567890abcdef",
    "status": "STARTED",
    "participatingServers": [{
      "sourceServerID": "s-1234567890abcdef0",
      "launchStatus": "LAUNCHED",
      "recoveryInstanceID": "i-target-instance-id"
    }]
  }
}
```


**Completed** (T+15m):


```json
{
  "job": {
    "jobID": "job-1234567890abcdef",
    "status": "COMPLETED",
    "endDateTime": "2026-01-01T14:45:00.000Z",
    "participatingServers": [{
      "sourceServerID": "s-1234567890abcdef0",
      "launchStatus": "LAUNCHED",
      "recoveryInstanceID": "i-target-instance-id"
    }]
  }
}
```


**Polling Pattern**:


```py
def monitor_recovery_job(job_id: str, timeout: int = 1800) -> Dict:
    """Monitor DRS recovery job with AllowLaunchingIntoThisInstance"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = drs_client.describe_jobs(
            filters={'jobIDs': [job_id]}
        )
        
        job = response['items'][0]
        status = job['status']
        
        if status == 'COMPLETED':
            # Verify instances launched into target instances
            for server in job.get('participatingServers', []):
                recovery_id = server.get('recoveryInstanceID')
                
                # Verify this is the pre-provisioned instance
                response = drs_client.describe_recovery_instances(
                    filters={'recoveryInstanceIDs': [recovery_id]}
                )
                
                ec2_instance_id = response['items'][0]['ec2InstanceID']
                print(f"Launched into instance: {ec2_instance_id}")
            
            return {'status': 'SUCCESS', 'job': job}
        
        elif status == 'FAILED':
            return {'status': 'FAILED', 'error': job.get('error')}
        
        time.sleep(30)
    
    return {'status': 'TIMEOUT'}
```


### Recovery Instance Validation

**Verify Launch Into Target Instance**:


```py
def validate_recovery_instance(recovery_instance_id: str, expected_instance_id: str) -> bool:
    """Verify recovery launched into expected pre-provisioned instance"""
    
    response = drs_client.describe_recovery_instances(
        filters={'recoveryInstanceIDs': [recovery_instance_id]}
    )
    
    recovery_instance = response['items'][0]
    
    # Critical validation: ec2InstanceID should match target
    actual_instance_id = recovery_instance['ec2InstanceID']
    
    if actual_instance_id != expected_instance_id:
        raise ValueError(
            f"Recovery launched into wrong instance. "
            f"Expected: {expected_instance_id}, Got: {actual_instance_id}"
        )
    
    # Verify instance state
    ec2_response = ec2_client.describe_instances(
        InstanceIds=[actual_instance_id]
    )
    
    instance = ec2_response['Reservations'][0]['Instances'][0]
    state = instance['State']['Name']
    
    if state != 'running':
        raise ValueError(f"Instance not running: {state}")
    
    # Verify AWSDRS tag present
    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
    if tags.get('AWSDRS') != 'AllowLaunchingIntoThisInstance':
        raise ValueError("AWSDRS tag missing or incorrect")
    
    print(f"✅ Recovery validated: {actual_instance_id}")
    return True
```


### Complete Recovery Timeline

**AllowLaunchingIntoThisInstance Recovery Timeline**:


```
Time    | API Call                      | Status
--------|-------------------------------|----------------------------------
T+0s    | describe_source_servers       | Validate CONTINUOUS replication
T+5s    | update_launch_configuration   | Set launchIntoInstanceProperties
T+10s   | start_recovery                | Job created (PENDING)
T+30s   | describe_jobs                 | Job status: STARTED
T+2m    | describe_jobs                 | Target instance stopped
T+3m    | describe_jobs                 | Volumes replaced
T+5m    | describe_jobs                 | launchStatus: LAUNCHED
T+8m    | describe_recovery_instances   | ec2InstanceState: running
T+10m   | describe_jobs                 | Job status: COMPLETED
T+11m   | validate_recovery_instance    | Verify target instance used
```


**Key Timing Differences**:

* Standard Recovery: 2-4 hours (new instance creation)
* AllowLaunchingIntoThisInstance: 15-30 minutes (volume replacement only)

### Drill vs Recovery Execution

**Drill Execution** (`isDrill=True`):

* Purpose: Testing without production impact
* Creates isolated recovery instances
* Always terminates instances after testing
* Lower risk

**Production Recovery** (`isDrill=False`):

* Purpose: Actual disaster recovery
* Launches into pre-provisioned instances
* Instances remain running for production use
* Higher risk - requires validation

**Note for AllowLaunchingIntoThisInstance**:


```py
# Drill - Uses temporary instance (not recommended for AllowLaunchingIntoThisInstance)
response = drs_client.start_recovery(
    sourceServers=[{'sourceServerID': 's-1234567890abcdef0'}],
    isDrill=True  # Will still launch into target, but terminates after
)

# Production Recovery - Preserves target instance
response = drs_client.start_recovery(
    sourceServers=[{'sourceServerID': 's-1234567890abcdef0'}],
    isDrill=False  # Launches into target and keeps running
)
```


**Recommendation**: For AllowLaunchingIntoThisInstance testing, use separate test instances with `AWSDRS=AllowLaunchingIntoThisInstance` tag in non-production environment.

### Tags Parameter Note

Do not include `tags` parameter in `start_recovery()` when using AllowLaunchingIntoThisInstance.

**Why**: Tags parameter can cause DRS to skip the conversion phase, which may interfere with launching into existing instances.

**Correct Usage**:


```py
# ✅ CORRECT - No tags parameter
response = drs_client.start_recovery(
    sourceServers=[{'sourceServerID': 's-1234567890abcdef0'}],
    isDrill=False
)

# ❌ INCORRECT - Tags may skip conversion
response = drs_client.start_recovery(
    sourceServers=[{'sourceServerID': 's-1234567890abcdef0'}],
    isDrill=False,
    tags={'Environment': 'Production'}  # Can cause issues
)
```


---

Technical Implementation Details
--------------------------------

All code samples below are planned designs. No actual implementation exists yet.

### Implementation Flow

The AllowLaunchingIntoThisInstance implementation follows this sequence:


```
1. Discovery (existing capability)
   - Query Resource Explorer for dr:recovery-strategy=drs
   - Filter for AWSDRS=AllowLaunchingIntoThisInstance tag
   ↓
2. Optional Tag Sync (existing capability - can be called on-demand)
   - Call existing manual tag sync function
   - Ensures EC2 tags are current on DRS source servers
   - Particularly important for Name tag accuracy
   ↓
3. Name Tag Matching (NEW - from SSM automation pattern)
   - Match DRS source servers to stopped EC2 instances by Name tag
   - Validate target instance state = 'stopped'
   - Validate AWSDRS=AllowLaunchingIntoThisInstance tag presence
   ↓
4. Configure AllowLaunchingIntoThisInstance (NEW - from SSM automation pattern)
   - Disable conflicting DRS settings (copyTags, copyPrivateIp, rightSizing)
   - Set launchDisposition='STOPPED'
   - Configure launchIntoInstanceProperties with target instance ID
   ↓
5. Execute Recovery (existing wave-based orchestration)
   - Create DRS recovery jobs
   - Monitor job status
   - Capture instance IDs and validation
```


**Key Integration Points**:

* **Tag Sync**: Reuse existing `POST /infrastructure/tag-sync` endpoint
* **Discovery**: Reuse existing Resource Explorer queries
* **Orchestration**: Integrate into existing Step Functions workflow
* **Monitoring**: Reuse existing DRS job polling mechanism

### Tagging Policy for DRS Recovery

**Required Tags for AllowLaunchingIntoThisInstance**:

When using DRS recovery with pre-provisioned instances, the following tagging policy applies:


```
IF dr:enabled=true AND dr:recovery-strategy=drs
THEN AWSDRS=AllowLaunchingIntoThisInstance (REQUIRED)
```


**Tag Definitions**:

* `dr:enabled` - true/false (identifies resources for DR orchestration)
* `dr:recovery-strategy` - drs (specifies DRS as the recovery method)
* `AWSDRS` - AllowLaunchingIntoThisInstance (enables pre-provisioned instance recovery)

**Example EC2 Instance Tags**:


```json
{
  "Tags": [
    {"Key": "Name", "Value": "acme-prod-web-app01"},
    {"Key": "dr:enabled", "Value": "true"},
    {"Key": "dr:recovery-strategy", "Value": "drs"},
    {"Key": "dr:priority", "Value": "critical"},
    {"Key": "dr:wave", "Value": "2"},
    {"Key": "AWSDRS", "Value": "AllowLaunchingIntoThisInstance"},
    {"Key": "Customer", "Value": "acme"},
    {"Key": "Environment", "Value": "production"}
  ]
}
```


**Tag Validation**:

* AWS Config rules will enforce the tagging policy
* Resources with `dr:recovery-strategy=drs` must have `AWSDRS=AllowLaunchingIntoThisInstance`
* Missing tags will trigger compliance violations
* Automated remediation can apply missing tags

**Implementation Notes**:

* Tag synchronization will copy `AWSDRS` tag from EC2 to DRS source servers
* Discovery queries will filter for resources with `AWSDRS=AllowLaunchingIntoThisInstance`
* Name tag matching will use instances with this tag to identify pre-provisioned targets

### AllowLaunchingIntoThisInstance Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│    AllowLaunchingIntoThisInstance - Failback Pattern Only      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Primary Region (us-east-1)          DR Region (us-east-2)      │
│  ┌──────────────────────┐             ┌──────────────────────┐  │
│  │  Source Instance     │   Failover  │  Recovery Instance   │  │
│  │  i-0abc123 (running) │ ─────────>  │  i-0xyz789 (running) │  │
│  │  Name: web-app01     │   (DR Event)│  Name: web-app01     │  │
│  │  IP: 10.0.1.100      │             │  IP: 10.1.1.100      │  │
│  └──────────────────────┘             └──────────────────────┘  │
│           │                                     │               │
│           │ After DR Event                      │               │
│           ▼                                     │               │
│  ┌──────────────────────┐                      │               │
│  │  Source Instance     │                      │               │
│  │  i-0abc123 (stopped) │                      │               │
│  │  Name: web-app01     │                      │               │
│  │  IP: 10.0.1.100      │                      │               │
│  │  (Original instance) │                      │               │
│  └──────────────────────┘                      │               │
│           ▲                                     │               │
│           │            Failback                 │               │
│           └─────────────────────────────────────┘               │
│           (Launches into ORIGINAL instance,                     │
│            preserves i-0abc123 and 10.0.1.100)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Key Benefits:
- Preserves original instance ID (i-0abc123)
- Maintains original private IP (10.0.1.100)
- No application reconfiguration needed
- No DNS changes required
- Faster than creating new instance
```


### Failover and Failback Flow


```
┌─────────────────────────────────────────────────────────────────┐
│                    Failover Flow                                │
└─────────────────────────────────────────────────────────────────┘

1. Discovery
   ├─ Query Resource Explorer for dr:recovery-strategy=drs
   ├─ Filter by Customer/Environment tags
   └─ Get source instances in primary region

2. Name Tag Matching
   ├─ Get DR region instances
   ├─ Match by Name tag (normalized)
   └─ Validate 1:1 mapping

3. Configure AllowLaunchingIntoThisInstance
   ├─ For each primary-DR pair:
   │  ├─ Get DRS source server ID
   │  ├─ Update launch configuration
   │  │  └─ launchIntoEC2InstanceID = DR instance ID
   │  └─ Set copyPrivateIp=True, copyTags=True

4. Create Recovery Jobs
   ├─ Batch source servers (max 20 per job)
   ├─ Call start_recovery API
   └─ Store job IDs in DynamoDB

5. Monitor Jobs
   ├─ Poll job status every 30 seconds
   ├─ Track: PENDING → STARTED → COMPLETED
   └─ Publish CloudWatch metrics

6. Validate Recovery
   ├─ Capture instance IDs
   ├─ Verify EC2 status checks
   ├─ Test network connectivity
   └─ Check application health

┌─────────────────────────────────────────────────────────────────┐
│                    Failback Flow                                │
└─────────────────────────────────────────────────────────────────┘

1. Identify Active Instances
   ├─ Get running instances in DR region
   └─ Get stopped instances in primary region (original sources)

2. Match Failback Pairs
   ├─ Use metadata from original failover
   ├─ Map DR instances → original primary instances
   └─ Validate instance pairs

3. Configure AllowLaunchingIntoThisInstance (Reverse)
   ├─ For each DR-primary pair:
   │  ├─ Get DRS source server ID (DR instance)
   │  ├─ Update launch configuration
   │  │  └─ launchIntoEC2InstanceID = original primary instance ID
   │  └─ Set copyPrivateIp=True, copyTags=True

4. Create Failback Jobs
   ├─ Batch source servers
   ├─ Call start_recovery API
   └─ Store job IDs with failback metadata

5. Monitor and Validate
   ├─ Same monitoring as failover
   └─ Verify instances back in primary region
```


### DRS Launch Configuration

**Standard Launch Configuration** (without AllowLaunchingIntoThisInstance):


```json
{
  "sourceServerID": "s-1234567890abcdef0",
  "targetInstanceTypeRightSizingMethod": "BASIC",
  "copyPrivateIp": false,
  "copyTags": true,
  "launchDisposition": "STARTED"
}
```


**Result**: New instance launched with new IP address (RTO: 2-4 hours)

**AllowLaunchingIntoThisInstance Configuration**:


```json
{
  "sourceServerID": "s-1234567890abcdef0",
  "launchIntoInstanceProperties": {
    "launchIntoEC2InstanceID": "i-0def456789abcdef0"
  },
  "targetInstanceTypeRightSizingMethod": "NONE",
  "copyPrivateIp": true,
  "copyTags": true,
  "launchDisposition": "STARTED"
}
```


**Result**: Recovery instance launched into pre-provisioned instance (RTO: 15-30 minutes)

### Name Tag Matching Algorithm

**Naming Convention**:


```
{customer}-{environment}-{workload}-{role}{number}

Examples:
- acme-prod-web-app01
- acme-prod-web-app02
- acme-prod-db-primary
- acme-prod-db-replica01
```


**Matching Logic**:

1. Normalize names (lowercase, strip whitespace)
2. Exact match on normalized names
3. Log unmatched instances
4. Validate 1:1 mapping (no duplicates)

**Example Matching**:


```
Primary Region (us-east-1):
- i-0abc123: acme-prod-web-app01
- i-0abc456: acme-prod-web-app02
- i-0abc789: acme-prod-db-primary

DR Region (us-east-2):
- i-0def123: acme-prod-web-app01  ✅ Matched
- i-0def456: acme-prod-web-app02  ✅ Matched
- i-0def789: acme-prod-db-primary ✅ Matched

Result: 3/3 instances matched (100%)
```


---

Production Deployment - Planned Configuration
--------------------------------------------

DRS Orchestration Module has not been deployed. This section describes the planned deployment once implementation is complete.

### Planned Deployment Information

* **Environment**: Development (planned)
* **Region**: us-east-1 (primary), us-east-2 (DR)
* **Stack**: To be determined
* **Branch**: feature/drs-orchestration-engine
* **Version**: To be determined

### Planned Configuration

**Environment Variables** (Lambda):

```yaml
DRS_REPLICATION_REGION: "us-east-2"
DRS_JOB_POLL_INTERVAL: "30"
DRS_JOB_TIMEOUT: "7200"
ALLOW_LAUNCHING_INTO_INSTANCE: "true"
COPY_PRIVATE_IP: "true"
COPY_TAGS: "true"
INSTANCE_MATCHER_ALGORITHM: "name_tag"
VALIDATION_ENABLED: "true"
```

### Planned Deployment Commands

```bash
# Deploy DRS orchestration module
cd infra/orchestration/drs-orchestration
./scripts/deploy.sh dev

# Verify deployment
aws cloudformation describe-stacks \
  --stack-name {STACK_NAME} \
  --query 'Stacks[0].StackStatus'

# Test DRS integration
aws lambda invoke \
  --function-name {ORCHESTRATION_LAMBDA_NAME} \
  --payload '{"action":"testDRSIntegration"}' \
  response.json
```

### Planned Pre-Provisioned Instance Setup

**Step 1: Create DR Region Instances**

```bash
# Launch instances in DR region with matching Name tags
aws ec2 run-instances \
  --region us-east-2 \
  --image-id ami-0abcdef1234567890 \
  --instance-type t3.medium \
  --subnet-id subnet-0def456 \
  --tag-specifications \
    'ResourceType=instance,Tags=[{Key=Name,Value=acme-prod-web-app01},{Key=dr:enabled,Value=true}]'
```

**Step 2: Stop DR Instances**

```bash
# Stop instances to prepare for AllowLaunchingIntoThisInstance
aws ec2 stop-instances \
  --region us-east-2 \
  --instance-ids i-0def456789abcdef0
```

**Step 3: Configure DRS Replication**

```bash
# Install DRS agent on primary instances
# Agent automatically replicates to DR region
```


---

Developer Integration Guide - Planned Implementation
----------------------------------------------------

This section describes the planned repository structure and integration steps once implementation is complete. No actual code files exist yet.

### Planned Repository Structure

DRS orchestration module code will be located in:

```
he.platform.devops.aws.dr-orchestration/
├── infra/orchestration/drs-orchestration/
│   ├── lambda/
│   │   ├── shared/
│   │   │   ├── drs_client.py                  # To be created
│   │   │   ├── instance_matcher.py            # To be created
│   │   │   ├── drs_job_monitor.py             # To be created
│   │   │   └── drs_error_handler.py           # To be created
│   │   └── orchestration-stepfunctions/
│   │       └── index.py                       # To be updated
│   ├── cfn/
│   │   ├── lambda-stack.yaml                  # To be updated
│   │   └── step-functions-stack.yaml          # To be updated
│   └── tests/
│       ├── unit/
│       │   ├── test_drs_api_integration.py    # To be created
│       │   ├── test_instance_matching.py      # To be created
│       │   └── test_allow_launching_into_instance.py  # To be created
│       ├── integration/
│       │   ├── test_drs_recovery_jobs.py      # To be created
│       │   ├── test_drs_job_monitoring.py     # To be created
│       │   └── test_failover_failback.py      # To be created
│       └── e2e/
│           └── test_complete_dr_cycle.py      # To be created
```

**Repository URL**: Internal repository (contact team for access)  
**Branch**: feature/drs-orchestration-engine

### Key Code Samples - Planned Designs

All code samples below are planned designs from the research document. These files do not exist in the repository yet.

#### 1. Configure AllowLaunchingIntoThisInstance (Planned)

**Planned File**: `lambda/shared/drs_client.py` (to be created)

**Reference**: Based on working SSM automation pattern in `scripts/updateDRSLaunchSettings.yaml`

```py
# PLANNED CODE - Pattern validated in production SSM automation

def configure_allow_launching_into_instance(
    source_server_id: str,
    target_instance_id: str
) -> Dict:
    """
    Configure DRS to launch into pre-provisioned instance.
    Preserves IP address and instance identity.
    
    Two-step process:
    1. Disable conflicting DRS settings
    2. Configure launch-into-instance properties
    
    Pattern based on working SSM automation.
    """
    drs_client = boto3.client('drs')
    
    # Validate target instance is stopped
    ec2_client = boto3.client('ec2')
    instance = ec2_client.describe_instances(
        InstanceIds=[target_instance_id]
    )['Reservations'][0]['Instances'][0]
    
    if instance['State']['Name'] != 'stopped':
        raise ValueError(
            f"Target instance must be stopped. "
            f"Current state: {instance['State']['Name']}"
        )
    
    # Step 1: Disable conflicting settings
    drs_client.update_launch_configuration(
        sourceServerID=source_server_id,
        copyTags=False,  # Tags managed separately via existing tag sync
        copyPrivateIp=False,  # Preserves network configuration
        targetInstanceTypeRightSizingMethod='NONE',  # Uses existing instance type
        launchDisposition='STOPPED'  # Controlled recovery
    )
    
    # Step 2: Configure launch-into-instance
    drs_client.update_launch_configuration(
        sourceServerID=source_server_id,
        launchIntoInstanceProperties={
            'launchIntoEC2InstanceID': target_instance_id
        }
    )
    
    return {
        'sourceServerID': source_server_id,
        'targetInstanceID': target_instance_id,
        'status': 'configured'
    }
```

**Integration Point**: Call before starting DRS recovery to configure target instance.

**Reference**: See research document Section 3.2 and `scripts/updateDRSLaunchSettings.yaml` Step 4.

---

#### 2. Match Primary-DR Instance Pairs (Planned)

**Planned File**: `lambda/shared/instance_matcher.py` (to be created)

```py
# PLANNED CODE
def match_primary_dr_instances(
    primary_instances: List[Dict],
    dr_instances: List[Dict]
) -> Dict[str, str]:
    """
    Match primary instances to DR instances by Name tag.
    Returns dict mapping primary instance ID to DR instance ID.
    """
    matches = {}
    
    # Build DR instance lookup by normalized Name tag
    dr_by_name = {
        get_tag_value(inst, 'Name').lower().strip(): inst['InstanceId']
        for inst in dr_instances
        if get_tag_value(inst, 'Name')
    }
    
    # Match primary instances
    for primary_inst in primary_instances:
        name = get_tag_value(primary_inst, 'Name')
        if name:
            normalized = name.lower().strip()
            dr_id = dr_by_name.get(normalized)
            if dr_id:
                matches[primary_inst['InstanceId']] = dr_id
    
    return matches
```

**Integration Point**: Use to identify target instances before configuring DRS.

**Reference**: See research document Section 3.3 for name matching algorithm.

---

#### 3. Create DRS Recovery Jobs (Planned)

**Planned File**: `lambda/orchestration-stepfunctions/index.py` (to be updated)

```py
# PLANNED CODE
def create_drs_recovery_jobs(instances: List[Dict]) -> List[Dict]:
    """
    Create DRS recovery jobs for tagged instances.
    Batches up to 20 servers per job (DRS limit).
    """
    drs_client = boto3.client('drs')
    jobs = []
    
    # Filter DRS instances
    drs_instances = [
        inst for inst in instances
        if get_tag_value(inst, 'dr:recovery-strategy') == 'drs'
    ]
    
    # Map to source server IDs
    source_servers = []
    for inst in drs_instances:
        server_id = get_drs_source_server_id(inst['InstanceId'])
        if server_id:
            source_servers.append({'sourceServerID': server_id})
    
    # Create recovery job (batch up to 20)
    if source_servers:
        response = drs_client.start_recovery(
            sourceServers=source_servers[:20]
        )
        jobs.append({
            'jobId': response['job']['jobID'],
            'status': response['job']['status'],
            'serverCount': len(source_servers[:20])
        })
    
    return jobs
```

**Integration Point**: Call to initiate DRS recovery for multiple instances.

**Reference**: See research document Section 4 for job creation workflow.

---

#### 4. Monitor DRS Recovery Job (Planned)

**Planned File**: `lambda/shared/drs_job_monitor.py` (to be created)

```py
# PLANNED CODE
def monitor_drs_recovery_job(job_id: str, timeout: int = 7200) -> Dict:
    """
    Monitor DRS recovery job until completion.
    Polls every 30 seconds, times out after 2 hours.
    """
    drs_client = boto3.client('drs')
    start_time = time.time()
    
    while True:
        # Check timeout
        if time.time() - start_time > timeout:
            raise TimeoutError(f"Job {job_id} exceeded timeout")
        
        # Get job status
        response = drs_client.describe_recovery_instances(
            filters={'recoveryInstanceIDs': [job_id]}
        )
        
        if not response['items']:
            raise ValueError(f"Job {job_id} not found")
        
        job = response['items'][0]
        status = job['dataReplicationInfo']['dataReplicationState']
        
        # Check terminal states
        if status == 'COMPLETED':
            return {
                'jobId': job_id,
                'status': 'COMPLETED',
                'duration': int(time.time() - start_time),
                'instanceId': job['ec2InstanceID']
            }
        elif status == 'FAILED':
            return {
                'jobId': job_id,
                'status': 'FAILED',
                'error': job.get('failureReason')
            }
        
        # Wait before next poll
        time.sleep(30)
```


**Integration Point**: Call after creating recovery job to track progress.

**Reference**: See research document Section 5 for monitoring design.

---

#### 5. Initiate Failback Operation (Planned)

**Planned File**: `lambda/orchestration-stepfunctions/index.py` (to be updated)

```py
# PLANNED CODE
def initiate_failback(
    protection_group_id: str,
    primary_region: str,
    dr_region: str
) -> Dict:
    """
    Initiate failback from DR region to primary region.
    Launches into original primary instances.
    """
    # Get active DR instances
    dr_instances = get_active_instances(protection_group_id, dr_region)
    
    # Get stopped primary instances (original sources)
    primary_instances = get_stopped_instances(
        protection_group_id,
        primary_region
    )
    
    # Match DR → primary using failover metadata
    pairs = match_failback_instances(dr_instances, primary_instances)
    
    # Configure and start recovery
    jobs = []
    for dr_id, primary_id in pairs.items():
        source_server_id = get_drs_source_server_id(dr_id)
        
        # Configure AllowLaunchingIntoThisInstance
        configure_allow_launching_into_instance(
            source_server_id=source_server_id,
            target_instance_id=primary_id
        )
        
        # Start recovery
        job = start_recovery_with_retry([source_server_id])
        jobs.append({
            'jobId': job['jobId'],
            'sourceId': dr_id,
            'targetId': primary_id
        })
    
    return {
        'operation': 'failback',
        'jobs': jobs,
        'sourceRegion': dr_region,
        'targetRegion': primary_region
    }
```

**Integration Point**: Call to return workloads to primary region after DR event.

**Reference**: See research document Section 4 for failback workflow.

---

### Integration Checklist - Pre-Implementation

Before starting DRS orchestration implementation:

- [ ] **Review Research Document**: Read `DRS_ALLOW_LAUNCHING_INTO_THIS_INSTANCE_RESEARCH.md`
- [ ] **Implement Tagging Policy**: Apply `AWSDRS=AllowLaunchingIntoThisInstance` tag to all DRS-enabled resources
- [ ] **Configure AWS Config Rules**: Set up tag validation for DRS tagging policy
- [ ] **Plan Pre-Provisioned Instances**: Design stopped instance strategy in DR region with matching Name tags
- [ ] **Understand DRS Agents**: Review DRS replication agent deployment process
- [ ] **Design Tagging Strategy**: Plan `dr:enabled=true` and `dr:recovery-strategy=drs` tag application
- [ ] **Review IAM Requirements**: Understand DRS permissions needed for orchestration role
- [ ] **Estimate Implementation Effort**: 5 weeks for full implementation and testing
- [ ] **Allocate Resources**: Assign development team and AWS environment access
- [ ] **Set Up Test Environment**: Prepare non-production instances for testing

---

### Step-by-Step Integration Guide - Planned

These steps describe the planned integration process once implementation is complete.

#### Step 1: Clone Repository

```bash
git clone {repository-url}
cd he.platform.devops.aws.dr-orchestration
git checkout feature/drs-orchestration-engine
cd infra/orchestration/drs-orchestration
```

#### Step 2: Review Research Document

```bash
# Review comprehensive research document
cat docs/implementation/DRS_ALLOW_LAUNCHING_INTO_THIS_INSTANCE_RESEARCH.md
```

#### Step 3: Implement DRS Client

```bash
# Create DRS client module
# File: lambda/shared/drs_client.py
# Implement functions from research document Section 3.2
```

#### Step 4: Implement Instance Matcher

```bash
# Create instance matcher module
# File: lambda/shared/instance_matcher.py
# Implement name matching algorithm from research document Section 3.3
```

#### Step 5: Write Tests

```bash
# Create test files
mkdir -p tests/unit tests/integration tests/e2e

# Implement 104 planned tests
# See research document Section 7 for test plan
```

#### Step 6: Deploy to Development

```bash
./scripts/deploy.sh dev
```

#### Step 7: Test DRS Integration

```bash
# Test failover
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:{REGION}:{ACCOUNT_ID}:stateMachine:{STATE_MACHINE_NAME} \
  --input '{
    "operation": "failover",
    "protectionGroupId": "pg-test-001",
    "primaryRegion": "us-east-1",
    "drRegion": "us-east-2"
  }'

# Monitor execution
aws stepfunctions describe-execution \
  --execution-arn <execution-arn>
```


---

### Additional Resources

* **AWS DRS Documentation**: [DRS User Guide](https://docs.aws.amazon.com/drs/latest/userguide/what-is-drs.html)
* **AllowLaunchingIntoThisInstance**: [DRS Launch Configuration](https://docs.aws.amazon.com/drs/latest/userguide/launch-settings.html)

---

Performance Metrics - Projected Estimates
-----------------------------------------

All metrics below are projected estimates from research, not actual measured results.

### RTO Comparison (Projected)

| Scenario | Without AllowLaunchingIntoThisInstance | With AllowLaunchingIntoThisInstance | Improvement |
| --- | --- | --- | --- |
| 10 instances | 2.5 hours | 18 minutes | 88% |
| 50 instances | 4 hours | 25 minutes | 90% |
| 100 instances | 6 hours | 30 minutes | 92% |

### Failover Performance (Projected)

| Wave | Instance Count | Estimated Failover Time | Estimated Validation Time | Projected Total RTO |
| --- | --- | --- | --- | --- |
| 1 (Critical) | 10 | 15 minutes | 3 minutes | 18 minutes |
| 2 (High) | 25 | 20 minutes | 5 minutes | 25 minutes |
| 3 (Medium) | 50 | 25 minutes | 5 minutes | 30 minutes |

### Failback Performance (Projected)

| Scenario | Estimated Failback Time | Estimated Validation Time | Projected Total Time |
| --- | --- | --- | --- |
| 10 instances | 18 minutes | 4 minutes | 22 minutes |
| 50 instances | 28 minutes | 7 minutes | 35 minutes |
| 100 instances | 35 minutes | 10 minutes | 45 minutes |

### Name Tag Matching Accuracy (Projected)

| Instance Count | Expected Matched | Expected Unmatched | Projected Accuracy |
| --- | --- | --- | --- |
| 10 | 10 | 0 | 100% |
| 50 | 49 | 1 | 98% |
| 100 | 98 | 2 | 98% |
| 500 | 487 | 13 | 97.4% |

**Note**: All metrics are estimates based on research findings. Actual results will be measured during implementation and testing.

---

Related Documentation
---------------------

### Design Documents

* Enterprise DR Orchestration Platform - Design Docs
* BRD - Business Requirements
* PRD - Product Requirements
* SRS - Software Requirements
* TRS - Technical Requirements

### Architecture Documents

* ADR-003: AllowLaunchingIntoThisInstance Pattern
* ADR-004: Step Functions Orchestration
* System Architecture

### Related User Stories

* AWSM-1088: Wave-Based Orchestration Logic
* AWSM-1112: Handle DRS API Rate Limits

---

Implementation Checklist
------------------------

This section provides a comprehensive checklist for implementing the AllowLaunchingIntoThisInstance pattern for DRS orchestration.

### Phase 1: Prerequisites and Planning (Week 1)

**Infrastructure Setup**:
- [ ] Set up test environment with DRS agents deployed
- [ ] Create pre-provisioned stopped instances in DR region
- [ ] Configure cross-account IAM roles for DRS operations
- [ ] Verify DRS replication is in CONTINUOUS state
- [ ] Apply required tags to all DRS-enabled resources

**Tagging Requirements**:
- [ ] Apply `dr:enabled=true` to all DR-protected resources
- [ ] Apply `dr:recovery-strategy=drs` to DRS-protected resources
- [ ] Apply `AWSDRS=AllowLaunchingIntoThisInstance` to target instances
- [ ] Ensure Name tags match between primary and DR instances
- [ ] Configure AWS Config rules for tag validation

**IAM Permissions**:
- [ ] Add `drs:UpdateLaunchConfiguration` to orchestration role
- [ ] Add `drs:StartRecovery` to orchestration role
- [ ] Add `drs:DescribeJobs` to orchestration role
- [ ] Add `drs:DescribeRecoveryInstances` to orchestration role
- [ ] Add EC2 permissions for AllowLaunchingIntoThisInstance:
  - [ ] `ec2:StopInstances`
  - [ ] `ec2:StartInstances`
  - [ ] `ec2:DetachVolume`
  - [ ] `ec2:AttachVolume`
  - [ ] `ec2:DeleteVolume`
  - [ ] `ec2:CreateVolume`
  - [ ] `ec2:ModifyInstanceAttribute`

### Phase 2: Core Implementation (Weeks 2-3)

**File: `lambda/shared/drs_client.py`** (to be created):
- [ ] Implement `configure_allow_launching_into_instance()` function
- [ ] Implement two-step configuration (disable conflicts, then configure)
- [ ] Add validation for target instance state (must be stopped)
- [ ] Add validation for AWSDRS tag presence
- [ ] Implement error handling for DRS API failures
- [ ] Add logging for configuration changes

**File: `lambda/shared/instance_matcher.py`** (to be created):
- [ ] Implement `match_primary_dr_instances()` function
- [ ] Add name normalization (lowercase, strip whitespace)
- [ ] Implement exact name matching algorithm
- [ ] Add validation for 1:1 mapping (no duplicates)
- [ ] Log unmatched instances for troubleshooting
- [ ] Return mapping dictionary (primary ID → DR ID)

**File: `lambda/shared/drs_job_monitor.py`** (to be created):
- [ ] Implement `monitor_drs_recovery_job()` function
- [ ] Add 30-second polling interval
- [ ] Implement timeout handling (default 2 hours)
- [ ] Track job status: PENDING → STARTED → COMPLETED/FAILED
- [ ] Capture recovery instance IDs
- [ ] Publish CloudWatch metrics for job duration

**File: `lambda/shared/drs_error_handler.py`** (to be created):
- [ ] Implement exponential backoff retry logic
- [ ] Handle specific DRS API errors (InvalidParameterException, ResourceNotFoundException)
- [ ] Log validation errors with detailed context
- [ ] Store failed operations in DynamoDB for retry
- [ ] Send SNS alerts for critical failures

**File: `lambda/orchestration-stepfunctions/index.py`** (to be updated):
- [ ] Add `create_drs_recovery_jobs()` function
- [ ] Implement batch processing (max 20 servers per job)
- [ ] Add `initiate_failback()` function
- [ ] Integrate with existing wave-based orchestration
- [ ] Add DRS job creation to Step Functions workflow

### Phase 3: Testing (Week 4)

**Unit Tests** (59 tests total):
- [ ] `tests/unit/test_drs_api_integration.py` (18 tests)
  - [ ] Test `configure_allow_launching_into_instance()` with valid inputs
  - [ ] Test validation failures (instance not stopped, missing tag)
  - [ ] Test two-step configuration sequence
  - [ ] Test error handling for DRS API failures
- [ ] `tests/unit/test_instance_matching.py` (12 tests)
  - [ ] Test exact name matching
  - [ ] Test name normalization
  - [ ] Test unmatched instance handling
  - [ ] Test duplicate detection
- [ ] `tests/unit/test_drs_error_handling.py` (14 tests)
  - [ ] Test exponential backoff retry
  - [ ] Test specific error handling
  - [ ] Test SNS alert generation
- [ ] `tests/unit/test_allow_launching_into_instance.py` (15 tests)
  - [ ] Test launch configuration validation
  - [ ] Test target instance validation
  - [ ] Test tag validation

**Integration Tests** (37 tests total):
- [ ] `tests/integration/test_drs_recovery_jobs.py` (15 tests)
  - [ ] Test job creation with real DRS API
  - [ ] Test batch processing (20 servers)
  - [ ] Test failover job creation
  - [ ] Test failback job creation
- [ ] `tests/integration/test_drs_job_monitoring.py` (10 tests)
  - [ ] Test job status polling
  - [ ] Test timeout handling
  - [ ] Test CloudWatch metrics publishing
- [ ] `tests/integration/test_failover_failback.py` (12 tests)
  - [ ] Test complete failover cycle
  - [ ] Test complete failback cycle
  - [ ] Test instance validation

**End-to-End Tests** (8 tests total):
- [ ] `tests/e2e/test_complete_dr_cycle.py` (8 tests)
  - [ ] Test 10-instance failover
  - [ ] Test 50-instance failover
  - [ ] Test 100-instance failover
  - [ ] Test failback to original instances

### Phase 4: Deployment and Validation (Week 5)

**Deployment**:
- [ ] Deploy to development environment
- [ ] Verify CloudFormation stack deployment
- [ ] Verify Lambda function updates
- [ ] Verify Step Functions state machine updates
- [ ] Run smoke tests in development

**Validation**:
- [ ] Execute test failover with 10 instances
- [ ] Verify instances launched into pre-provisioned targets
- [ ] Verify IP addresses preserved
- [ ] Verify Name tags preserved
- [ ] Measure actual RTO vs projected
- [ ] Execute test failback to original instances
- [ ] Verify complete cycle works end-to-end

**Documentation**:
- [ ] Update deployment guide with DRS configuration steps
- [ ] Document IAM permission requirements
- [ ] Document tagging requirements
- [ ] Create runbook for DRS failover operations
- [ ] Create runbook for DRS failback operations
- [ ] Document troubleshooting procedures

### Phase 5: Production Readiness

**Pre-Production**:
- [ ] Deploy to staging environment
- [ ] Execute full test suite in staging
- [ ] Conduct load testing (100+ instances)
- [ ] Measure performance metrics
- [ ] Validate monitoring and alerting
- [ ] Conduct security review
- [ ] Obtain stakeholder approval

**Production Deployment**:
- [ ] Create deployment plan
- [ ] Schedule maintenance window
- [ ] Deploy to production
- [ ] Verify production deployment
- [ ] Monitor for 24 hours
- [ ] Conduct post-deployment review

### Success Criteria

Implementation is complete when:
- [ ] All 104 tests passing
- [ ] RTO under 30 minutes for 100 instances
- [ ] Name matching accuracy above 95%
- [ ] Zero manual intervention required for standard failover
- [ ] Failback successfully returns to original instances
- [ ] All documentation complete
- [ ] Production deployment successful

### Files to Create

**Lambda Functions**:
1. `lambda/shared/drs_client.py` - DRS API client with AllowLaunchingIntoThisInstance configuration
2. `lambda/shared/instance_matcher.py` - Name tag matching algorithm
3. `lambda/shared/drs_job_monitor.py` - Job status monitoring with polling
4. `lambda/shared/drs_error_handler.py` - Error handling and retry logic

**Test Files**:
1. `tests/unit/test_drs_api_integration.py` - 18 unit tests
2. `tests/unit/test_instance_matching.py` - 12 unit tests
3. `tests/unit/test_drs_error_handling.py` - 14 unit tests
4. `tests/unit/test_allow_launching_into_instance.py` - 15 unit tests
5. `tests/integration/test_drs_recovery_jobs.py` - 15 integration tests
6. `tests/integration/test_drs_job_monitoring.py` - 10 integration tests
7. `tests/integration/test_failover_failback.py` - 12 integration tests
8. `tests/e2e/test_complete_dr_cycle.py` - 8 end-to-end tests

**Files to Update**:
1. `lambda/orchestration-stepfunctions/index.py` - Add DRS job creation and failback functions
2. `cfn/lambda-stack.yaml` - Add IAM permissions for DRS operations
3. `cfn/step-functions-stack.yaml` - Update state machine for DRS integration

### Estimated Effort

* **Total Duration**: 5 weeks
* **Team Size**: 2-3 developers + 1 QA engineer
* **Testing Time**: 1 week (20% of total)
* **Documentation Time**: 3 days (included in Week 5)

### Risk Mitigation

**High-Risk Areas**:
- [ ] DRS API rate limiting - implement exponential backoff
- [ ] Name tag matching accuracy - validate in test environment first
- [ ] Cross-account permissions - test thoroughly before production
- [ ] Job monitoring timeout - set appropriate timeout values
- [ ] Failback complexity - document and test extensively

**Rollback Plan**:
- [ ] Keep existing recovery mechanism as fallback
- [ ] Document rollback procedure
- [ ] Test rollback in staging environment
- [ ] Maintain ability to disable AllowLaunchingIntoThisInstance