# Pre-Provisioned DR Instances with AllowLaunchingIntoThisInstance

**Confluence Title**: Pre-Provisioned DR Instances with AllowLaunchingIntoThisInstance - Implementation Guide  
**Description**: Implementation guide for AWS DRS AllowLaunchingIntoThisInstance capability, enabling cost-optimized disaster recovery through pre-provisioned EC2 instances with minimal storage. Covers instance identity preservation, cost optimization strategies, and implementation roadmap.

**JIRA Ticket**: [AWSM-1119](https://healthedge.atlassian.net/browse/AWSM-1119)  
**Epic**: [AWSM-1112 - DRS Integration and EC2 Recovery](https://healthedge.atlassian.net/browse/AWSM-1112)  
**Status**: 🟡 **PARTIALLY IMPLEMENTED**  
**Priority**: High  
**Business Impact**: Cost optimization through pre-provisioned instances with minimal storage

---

## Executive Summary

AllowLaunchingIntoThisInstance capability enables DRS to launch recovery workloads into pre-provisioned EC2 instances, preserving instance identity (instance ID, private IP, network configuration) while optimizing costs by running instances with minimal or no attached storage until recovery is needed.

**Current Status**: DRS launch configuration management is implemented via Protection Groups, but AllowLaunchingIntoThisInstance-specific logic (target instance discovery, validation, configuration) is not yet implemented.

**Key Achievement Target**: Enable 15-30 minute RTO with pre-provisioned instances while reducing DR infrastructure costs by 60-80% through minimal storage configuration.

---

## Acceptance Criteria Status

### 🟡 Criterion 1: AllowLaunchingIntoThisInstance Configuration
**Requirement**: *Given* pre-provisioned DR instances, *When* configuring DRS, *Then* AllowLaunchingIntoThisInstance capability is enabled.

**Status**: 🟡 **PARTIALLY IMPLEMENTED**

**What's Implemented**:
- DRS launch configuration management via `apply_launch_config_to_servers()` function
- Protection Group schema supports `launchConfig` with DRS settings
- DRS API integration for `update_launch_configuration()`

**What's Missing**:
- `launchIntoInstanceProperties` configuration in DRS API calls
- Target instance discovery by Name tag matching
- AWSDRS tag validation on target instances
- Target instance state validation (must be stopped)

**Implementation Location**:
- Current: `infra/orchestration/drs-orchestration/lambda/api-handler/index.py` (lines 9885-10100)
- Needs: Enhancement to `apply_launch_config_to_servers()` function

**Code Gap**:
```python
# MISSING: AllowLaunchingIntoThisInstance configuration
drs_update = {"sourceServerID": server_id}

# Need to add:
if launch_config.get("allowLaunchingIntoThisInstance"):
    target_instance_id = find_target_instance_by_name(
        source_server_name=get_server_name(server_id),
        target_region=region
    )
    
    validate_target_instance(target_instance_id, region)
    
    drs_update["launchIntoInstanceProperties"] = {
        "launchIntoEC2InstanceID": target_instance_id
    }
```

---

### 🟡 Criterion 2: Instance Identity Preservation
**Requirement**: *Given* DRS recovery, *When* launching into pre-provisioned instance, *Then* instance retains instance ID and network configuration.

**Status**: 🟡 **DESIGN COMPLETE, NOT IMPLEMENTED**

**Design**:
- DRS automatically preserves instance ID when using AllowLaunchingIntoThisInstance
- Network configuration (private IP, security groups, subnet) preserved by DRS
- No additional code required - DRS handles this natively

**Validation Needed**:
- Post-recovery validation to confirm instance ID unchanged
- Network connectivity tests to verify IP preservation
- Application health checks to confirm service availability

**Implementation Location**:
- Validation logic needed in orchestration Lambda
- Post-recovery health checks in Step Functions workflow

---

### ❌ Criterion 3: Cost Optimization with Minimal Storage
**Requirement**: *Given* pre-provisioned instances, *When* not in use, *Then* instances run with minimal or no attached storage.

**Status**: ❌ **NOT IMPLEMENTED**

**What's Missing**:
- Documentation for pre-provisioning instances with minimal storage
- Guidance on EBS volume configuration (root volume only, minimal size)
- Cost analysis comparing minimal storage vs. full replication
- Runbook procedures for pre-provisioning instances

**Design Considerations**:
- Root volume only (8-16 GB) for OS and DRS agent
- No data volumes attached until recovery
- Instance in stopped state to minimize compute costs
- DRS replication volumes stored separately in DRS staging area

**Cost Impact**:
- Standard approach: Full instance with all volumes (100% cost)
- Minimal storage approach: Root volume only (10-20% storage cost)
- Stopped instance: No compute cost until recovery
- Total savings: 60-80% reduction in DR infrastructure costs

---

## Definition of Done - Implementation Checklist

### ❌ 1. AllowLaunchingIntoThisInstance Configuration Implemented
**Status**: ❌ **NOT STARTED**

**Required Changes**:

1. **Add target instance discovery function**:
```python
def find_target_instance_by_name(
    source_server_name: str,
    target_region: str,
    source_region: str = None
) -> str:
    """
    Find target instance in DR region by matching Name tag.
    
    Args:
        source_server_name: Name tag of source server
        target_region: DR region to search
        source_region: Optional source region for cross-region matching
        
    Returns:
        Target instance ID
        
    Raises:
        ValueError: If no matching instance found or multiple matches
    """
    ec2 = boto3.client('ec2', region_name=target_region)
    
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Name', 'Values': [source_server_name]},
            {'Name': 'tag:AWSDRS', 'Values': ['AllowLaunchingIntoThisInstance']}
        ]
    )
    
    instances = []
    for reservation in response['Reservations']:
        instances.extend(reservation['Instances'])
    
    if len(instances) == 0:
        raise ValueError(
            f"No target instance found with Name={source_server_name} "
            f"and AWSDRS=AllowLaunchingIntoThisInstance in {target_region}"
        )
    
    if len(instances) > 1:
        raise ValueError(
            f"Multiple target instances found with Name={source_server_name} "
            f"in {target_region}. Ensure unique naming."
        )
    
    return instances[0]['InstanceId']
```

2. **Add target instance validation function**:
```python
def validate_target_instance(instance_id: str, region: str) -> None:
    """
    Validate target instance meets AllowLaunchingIntoThisInstance requirements.
    
    Args:
        instance_id: Target instance ID
        region: AWS region
        
    Raises:
        ValueError: If instance doesn't meet requirements
    """
    ec2 = boto3.client('ec2', region_name=region)
    
    response = ec2.describe_instances(InstanceIds=[instance_id])
    instance = response['Reservations'][0]['Instances'][0]
    
    # Verify AWSDRS tag
    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
    if tags.get('AWSDRS') != 'AllowLaunchingIntoThisInstance':
        raise ValueError(
            f"Instance {instance_id} missing required tag "
            f"AWSDRS=AllowLaunchingIntoThisInstance"
        )
    
    # Verify instance is stopped
    state = instance['State']['Name']
    if state != 'stopped':
        raise ValueError(
            f"Instance {instance_id} must be stopped (current state: {state})"
        )
    
    # Verify minimal storage configuration (optional warning)
    volumes = instance.get('BlockDeviceMappings', [])
    if len(volumes) > 1:
        print(
            f"Warning: Instance {instance_id} has {len(volumes)} volumes. "
            f"Consider using minimal storage (root volume only) for cost optimization."
        )
```

3. **Enhance `apply_launch_config_to_servers()` function**:
```python
# Add to existing function after line 9970
if launch_config.get("allowLaunchingIntoThisInstance"):
    # Get source server name for target matching
    source_server_name = get_source_server_name(server_id, region)
    
    # Find and validate target instance
    target_instance_id = find_target_instance_by_name(
        source_server_name=source_server_name,
        target_region=region
    )
    
    validate_target_instance(target_instance_id, region)
    
    # Configure AllowLaunchingIntoThisInstance
    drs_update["launchIntoInstanceProperties"] = {
        "launchIntoEC2InstanceID": target_instance_id
    }
    
    # Disable conflicting settings
    drs_update["copyPrivateIp"] = False  # Target instance keeps its IP
    drs_update["targetInstanceTypeRightSizingMethod"] = "NONE"  # Use target instance type
```

**Files to Modify**:
- `infra/orchestration/drs-orchestration/lambda/api-handler/index.py`

**Testing Required**:
- Unit tests for target instance discovery
- Unit tests for target instance validation
- Integration test with real DRS source servers and target instances
- End-to-end test: configure → recover → validate instance ID preserved

---

### ❌ 2. Pre-Provisioned Instance Setup Documented
**Status**: ❌ **NOT STARTED**

**Required Documentation**:

1. **Pre-Provisioning Runbook** (`docs/runbooks/pre-provision-dr-instances.md`):
   - Step-by-step instance creation procedure
   - Minimal storage configuration (root volume only, 8-16 GB)
   - Required tags: `Name`, `AWSDRS=AllowLaunchingIntoThisInstance`
   - Network configuration (subnet, security groups)
   - Instance state management (stopped until recovery)

2. **Cost Optimization Guide** (`docs/guides/dr-cost-optimization.md`):
   - Cost comparison: full replication vs. minimal storage
   - Storage sizing recommendations
   - Instance type selection for pre-provisioned instances
   - Monitoring and alerting for cost anomalies

3. **Troubleshooting Guide** (`docs/troubleshooting/allowlaunchingintothisinstance.md`):
   - Common configuration errors
   - Target instance validation failures
   - Name tag matching issues
   - Recovery failures and remediation

---

### ❌ 3. Recovery into Pre-Provisioned Instances Tested
**Status**: ❌ **NOT STARTED**

**Test Scenarios**:

1. **Happy Path Test**:
   - Pre-provision target instance with minimal storage
   - Configure DRS source server with AllowLaunchingIntoThisInstance
   - Execute recovery
   - Validate: instance ID unchanged, IP preserved, application functional

2. **Name Tag Matching Test**:
   - Multiple instances with similar names
   - Verify unique matching or error on ambiguity
   - Test case-insensitive matching

3. **Target Instance Validation Test**:
   - Missing AWSDRS tag → error
   - Instance running (not stopped) → error
   - Instance in different subnet → warning or error

4. **Failback Test**:
   - Recover to DR region (failover)
   - Recover back to primary region (failback)
   - Validate: original instance ID restored

**Test Files to Create**:
- `tests/integration/test_allowlaunchingintothisinstance.py`
- `tests/e2e/test_dr_with_preprovisioned_instances.py`

---

### ❌ 4. Cost Optimization Validated
**Status**: ❌ **NOT STARTED**

**Validation Metrics**:

| Metric | Standard Approach | Minimal Storage Approach | Savings |
|--------|-------------------|--------------------------|---------|
| Storage Cost (per instance) | $100/month | $10-20/month | 80-90% |
| Compute Cost (stopped) | $0 | $0 | N/A |
| Total DR Infrastructure | $100K/month | $20K/month | 80% |

**Validation Steps**:
1. Deploy 10 test instances with full storage
2. Deploy 10 test instances with minimal storage
3. Measure monthly costs over 30 days
4. Compare recovery times (should be similar)
5. Document cost savings and RTO impact

---

### ❌ 5. Runbook Includes Pre-Provisioning Procedures
**Status**: ❌ **NOT STARTED**

**Runbook Sections Required**:

1. **Pre-Provisioning Checklist**:
   - [ ] Create EC2 instance in DR region
   - [ ] Configure minimal storage (root volume only)
   - [ ] Apply required tags (Name, AWSDRS)
   - [ ] Configure network (subnet, security groups)
   - [ ] Stop instance
   - [ ] Validate with `validate_target_instance()` function

2. **Recovery Procedure**:
   - [ ] Verify target instance is stopped
   - [ ] Execute DRS recovery
   - [ ] Monitor recovery job status
   - [ ] Validate instance ID preserved
   - [ ] Perform application health checks

3. **Failback Procedure**:
   - [ ] Stop recovered instance in DR region
   - [ ] Execute DRS failback to primary region
   - [ ] Validate original instance ID restored
   - [ ] Resume normal operations

**Runbook Location**: `docs/runbooks/drs-allowlaunchingintothisinstance.md`

---

## Current Implementation Status

### What's Working

1. **DRS Launch Configuration Management**:
   - Protection Groups support `launchConfig` with DRS settings
   - `apply_launch_config_to_servers()` updates DRS configuration
   - DRS API integration functional

2. **EC2 Launch Template Management**:
   - Subnet, security groups, instance type configuration
   - Launch template versioning and tracking

3. **Cross-Account Operations**:
   - STS AssumeRole for multi-account DR
   - IAM roles configured for DRS operations

### What's Missing

1. **AllowLaunchingIntoThisInstance Logic**:
   - Target instance discovery by Name tag
   - Target instance validation (AWSDRS tag, stopped state)
   - `launchIntoInstanceProperties` configuration

2. **Pre-Provisioning Guidance**:
   - Runbooks for instance pre-provisioning
   - Cost optimization documentation
   - Troubleshooting guides

3. **Testing**:
   - Integration tests with pre-provisioned instances
   - End-to-end recovery validation
   - Cost optimization validation

---

## Implementation Priority

### Phase 1: Core Functionality (2 weeks)
1. Implement target instance discovery function
2. Implement target instance validation function
3. Enhance `apply_launch_config_to_servers()` with AllowLaunchingIntoThisInstance logic
4. Unit tests for discovery and validation

### Phase 2: Integration Testing (1 week)
1. Integration tests with real DRS source servers
2. End-to-end recovery test with pre-provisioned instances
3. Failback testing

### Phase 3: Documentation (1 week)
1. Pre-provisioning runbook
2. Cost optimization guide
3. Troubleshooting guide

### Phase 4: Cost Validation (1 week)
1. Deploy test instances with minimal storage
2. Measure cost savings over 30 days
3. Document findings and recommendations

---

## Related Documentation

- [AWSM-1111: DRS Orchestration Module](../AWSM-1111/IMPLEMENTATION.md) - Core DRS integration
- [AWSM-1115: DRS Launch Settings Analysis](../AWSM-1115/LAUNCH-SETTINGS-ANALYSIS.md) - Launch configuration details
- [AWSM-1116: DRS Readiness Validation](../AWSM-1116/IMPLEMENTATION.md) - Pre-recovery validation
- [ADR-003: AllowLaunchingIntoThisInstance Pattern](../../../docs/architecture/ADR-003-allowlaunchingintothisinstance-pattern.md) - Architecture decision

---

## Repository Information

**Repository**: [he.platform.devops.aws.dr-orchestration](https://code.aws.dev/personal_projects/alias_d/duvvip/he.platform.devops.aws.dr-orchestration)  
**Branch**: feature/drs-orchestration-engine  
**Implementation File**: `infra/orchestration/drs-orchestration/lambda/api-handler/index.py`
