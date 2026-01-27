# DRS Orchestration Module - AllowLaunchingIntoThisInstance Implementation

**Confluence Title**: DRS Orchestration Module - AllowLaunchingIntoThisInstance Pattern Implementation  
**Description**: Implementation guide for AWS DRS integration with AllowLaunchingIntoThisInstance pattern for pre-provisioned instance recovery. Includes research findings, acceptance criteria, implementation plan, and integration patterns adapted from AWS Labs DRS Settings Tool for HRP's manifest-driven Module Factory architecture.

**JIRA Ticket**: [AWSM-1111](https://healthedge.atlassian.net/browse/AWSM-1111)  
**Epic**: [AWSM-1112 - DRS Integration and EC2 Recovery](https://healthedge.atlassian.net/browse/AWSM-1112)  
**Status**: ❌ **NOT IMPLEMENTED**  
**Implementation Branch**: [feature/drs-orchestration-engine](https://code.aws.dev/personal_projects/alias_d/duvvip/he.platform.devops.aws.dr-orchestration/-/tree/feature/drs-orchestration-engine)

---

## Overview

This document outlines the implementation plan for AWS DRS integration with AllowLaunchingIntoThisInstance pattern for failover and failback operations.

**Implementation Status**: Research and planning phase complete. No implementation code exists yet. All code samples in this document are planned designs.

---

## Feature Overview

### What AllowLaunchingIntoThisInstance Does

The `AWSDRS=AllowLaunchingIntoThisInstance` tag tells DRS to **launch into an existing EC2 instance** rather than creating a new one. When DRS performs recovery:

1. **Finds the tagged instance** in the target region
2. **Stops the instance** if it's running
3. **Replaces the EBS volumes** with recovery volumes from DRS
4. **Starts the instance** with the recovered data
5. **Preserves the instance metadata** (private IP, security groups, etc.)

### Key Benefits

- **Instance Identity Preservation**: Maintains instance ID, metadata, and network configuration
- **Network Configuration**: Security groups, subnets, and network interfaces remain unchanged
- **Cost Efficiency**: Reuses existing instances instead of creating new ones
- **Faster Recovery**: No instance launch time, just volume replacement
- **Compliance**: Maintains pre-approved instance configurations

---

## Research Findings & Acceptance Criteria

### Archive Implementation Analysis

From the enterprise DR orchestration archive (`archive/dr-orchestration-artifacts/src/modulefactory/modules/drs.py`), the working pattern is:

```python
# Find pre-provisioned instance with AWSDRS tag
response = ec2_client.describe_instances(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [server_hostname]  # Match by hostname
        },
        {
            'Name': 'tag:AWSDRS',
            'Values': ['AllowLaunchingIntoThisInstance']
        }
    ]
)

# Update DRS launch configuration to target this instance
drs_client.update_launch_configuration(
    launchIntoInstanceProperties={
        'launchIntoEC2InstanceID': target_instance_id
    },
    sourceServerID=source_server_id
)

# Start recovery - DRS will launch into the specified instance
drs_client.start_recovery(
    sourceServers=[{'sourceServerID': source_server_id}],
    isDrill=is_drill
)
```

### DRS API Integration Points

**Key DRS APIs**:
- `update_launch_configuration()` - Configure target instance
- `get_launch_configuration()` - Retrieve current settings
- `start_recovery()` - Execute recovery into target instance

**Launch Configuration Structure**:
```python
{
    'launchIntoInstanceProperties': {
        'launchIntoEC2InstanceID': 'i-1234567890abcdef0'
    },
    'targetInstanceTypeRightSizingMethod': 'NONE',  # Use existing instance type
    'copyPrivateIp': False,  # Keep existing IP
    'copyTags': True,  # Sync tags
    'launchDisposition': 'STARTED'  # Start after recovery
}
```

---

## Acceptance Criteria & Implementation Status

### 📋 Criterion 1: DRS Recovery Jobs for Tagged Instances
**Requirement**: *Given* EC2 instances tagged with dr:recovery-strategy=drs, *When* initiating recovery, *Then* DRS recovery jobs are created for tagged instances.

**Status**: 🔴 **NOT IMPLEMENTED**

**Tagging Policy**: Resources must have `AWSDRS=AllowLaunchingIntoThisInstance` tag when `dr:recovery-strategy=drs`

**Technical Approach**:
- Resource Explorer can query instances with `dr:recovery-strategy=drs` tag
- Additional filter for `AWSDRS=AllowLaunchingIntoThisInstance` identifies pre-provisioned recovery targets
- DRS source server IDs can be mapped from EC2 instance IDs
- Recovery jobs created via `start_recovery` API with source server list
- Batch processing supports up to 20 concurrent recovery jobs (DRS limit)

**Implementation Plan**:
```python
# PLANNED CODE - NOT YET IMPLEMENTED
# File: lambda/orchestration-stepfunctions/index.py

def create_drs_recovery_jobs(instances: List[Dict]) -> List[Dict]:
    """
    Create DRS recovery jobs for instances tagged with dr:recovery-strategy=drs
    and AWSDRS=AllowLaunchingIntoThisInstance.
    
    NOTE: This function is PLANNED but NOT YET IMPLEMENTED.
    """
    # Filter for DRS instances with AllowLaunchingIntoThisInstance tag
    drs_instances = [
        inst for inst in instances
        if get_tag_value(inst, 'dr:recovery-strategy') == 'drs'
        and get_tag_value(inst, 'AWSDRS') == 'AllowLaunchingIntoThisInstance'
    ]
    # Implementation details in research document
    pass
```

**Reference**: See `infra/orchestration/drs-orchestration/docs/implementation/DRS_ALLOW_LAUNCHING_INTO_THIS_INSTANCE_RESEARCH.md` for detailed implementation plan.

---

### 📋 Criterion 2: AllowLaunchingIntoThisInstance for Failover
**Requirement**: *Given* pre-provisioned DR region instances, *When* initiating failover, *Then* AllowLaunchingIntoThisInstance is used to launch into pre-provisioned instances.

**Status**: 🔴 **NOT IMPLEMENTED**

**Technical Approach**:
- Pre-provisioned instances identified by matching Name tags between regions
- DRS launch configuration updated with `launchIntoInstanceProperties.launchIntoEC2InstanceID`
- AllowLaunchingIntoThisInstance preserves IP address last octet and instance identity
- Target instance must be stopped before recovery
- Archive code shows this pattern working in enterprise DR orchestration

**Implementation Plan**:
```python
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
- Name tag matching algorithm can find corresponding instances across regions
- Naming convention: `{customer}-{environment}-{workload}-{role}` (e.g., `acme-prod-web-app01`)
- Fuzzy matching can handle minor naming variations (case-insensitive, whitespace-tolerant)
- 1:1 mapping validation ensures no duplicate matches
- Archive code shows this pattern working successfully

**Implementation Plan**:
```python
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
- Failback reverses the failover process: DR → Primary
- Original source instances (now stopped in primary region) become targets
- DRS launch configuration updated to launch into original instances
- Instance identity can be preserved during round-trip (failover + failback)
- Metadata tracking required to ensure correct instance pairing for failback

**Implementation Plan**: See research document Phase 2 for failback implementation details.

---

### 📋 Criterion 5: DRS Recovery Job Monitoring
**Requirement**: *Given* DRS recovery job, *When* job is in progress, *Then* job status is monitored and reported.

**Status**: 🔴 **NOT IMPLEMENTED**

**Technical Approach**:
- Polling mechanism should check job status every 30 seconds
- Job states: PENDING → STARTED → COMPLETED / FAILED
- CloudWatch metrics can track job duration and success rate
- SNS notifications for job completion or failure
- Step Functions wait state can handle long-running jobs (up to 2 hours)

**Implementation Plan**: Detailed implementation code samples provided in "Detailed Implementation Plan" section below.

---

### 📋 Criterion 6: Instance ID and Status Capture
**Requirement**: *Given* DRS recovery completion, *When* instances are launched, *Then* instance IDs and status are captured for validation.

**Status**: 🔴 **NOT IMPLEMENTED**

**Technical Approach**:
- Recovery instance IDs can be captured from DRS API response
- Instance status validation: running, network accessible, application healthy
- Metadata should be stored in DynamoDB: instance ID, IP address, launch time, validation status
- Validation should include: EC2 status checks, network connectivity, application health checks

**Implementation Plan**: Detailed implementation code samples provided in "Detailed Implementation Plan" section below.

---

## Definition of Done - Implementation Checklist

### 📋 1. DRS API Integration with AllowLaunchingIntoThisInstance
**Status**: 🔴 **NOT STARTED**

**Planned Implementation**:
- DRS API wrapper with `start_recovery`, `update_launch_configuration`, `describe_recovery_instances`
- AllowLaunchingIntoThisInstance configuration via `launchIntoInstanceProperties`
- Support for failover (primary → DR) and failback (DR → primary)
- IP address preservation with `copyPrivateIp=True`
- Tag copying with `copyTags=True`

**Planned Code Location**:
- DRS Client: `lambda/shared/drs_client.py` (to be created)
- Launch Configuration: `lambda/shared/drs_client.py` (to be created)

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
- Name tag matching algorithm with normalization (lowercase, strip whitespace)
- 1:1 mapping validation between primary and DR instances
- Fuzzy matching for minor naming variations
- Unmatched instance logging and alerting

**Planned Code Location**:
- Instance Matcher: `lambda/shared/instance_matcher.py` (to be created)
- Matching Tests: `tests/unit/test_instance_matching.py` (to be created)

**Planned Verification**:
```bash
# Test name tag matching (NOT YET IMPLEMENTED)
pytest tests/unit/test_instance_matching.py -v

# Expected: 12 tests covering name matching scenarios
```

**Reference**: See research document Section 3.3 for name matching algorithm.

---

### 📋 3. Recovery Job Creation for Failover and Failback
**Status**: 🔴 **NOT STARTED**

**Planned Implementation**:
- Failover job creation: primary region instances → DR region targets
- Failback job creation: DR region instances → original primary instances
- Batch processing (up to 20 servers per job)
- Job metadata tracking in DynamoDB

**Planned Code Location**:
- Job Creation: `lambda/orchestration-stepfunctions/index.py` (to be created)
- Failback Logic: `lambda/orchestration-stepfunctions/index.py` (to be created)

**Planned Verification**:
```bash
# Test recovery job creation (NOT YET IMPLEMENTED)
pytest tests/integration/test_drs_recovery_jobs.py -v

# Expected: 15 tests covering job creation scenarios
```

**Reference**: See research document Section 4 for job creation workflow.

---

### 📋 4. Job Status Monitoring
**Status**: 🔴 **NOT STARTED**

**Planned Implementation**:
- Polling mechanism with 30-second intervals
- Job state tracking: PENDING → STARTED → COMPLETED / FAILED
- CloudWatch metrics: job duration, success rate, failure count
- SNS notifications on completion/failure
- Step Functions wait state for long-running jobs

**Planned Code Location**:
- Job Monitor: `lambda/shared/drs_job_monitor.py` (to be created)
- Metrics Publisher: `lambda/shared/cloudwatch_metrics.py` (to be created)

**Planned Verification**:
```bash
# Test job monitoring (NOT YET IMPLEMENTED)
pytest tests/integration/test_drs_job_monitoring.py -v

# Expected: 10 tests covering monitoring scenarios
```

**Reference**: See research document Section 5 for monitoring design.

---

### 📋 5. Error Handling for DRS API Failures
**Status**: 🔴 **NOT STARTED**

**Planned Implementation**:
- Exponential backoff retry for rate limits (see AWSM-1112 rate limit ticket)
- Specific error handling for DRS API errors: InvalidParameterException, ResourceNotFoundException
- Validation errors logged with detailed context
- Failed operations stored in DynamoDB for retry
- SNS alerts for critical failures

**Planned Code Location**:
- Error Handler: `lambda/shared/drs_error_handler.py` (to be created)
- Retry Logic: `lambda/shared/drs_client.py` (to be created)

**Planned Verification**:
```bash
# Test error handling (NOT YET IMPLEMENTED)
pytest tests/unit/test_drs_error_handling.py -v

# Expected: 14 tests covering error scenarios
```

**Reference**: See research document Section 6 for error handling strategy.

---

### 📋 6. Integration Tests with DRS Service
**Status**: 🔴 **NOT STARTED**

**Planned Test Coverage**:
- Unit tests: 59 tests covering DRS API integration, name matching, job creation
- Integration tests: 37 tests with real DRS API calls and pre-provisioned instances
- End-to-end tests: 8 tests validating complete failover/failback cycles
- Performance tests: 3 tests with 10, 50, and 100 instance recoveries

**Planned Test Suite**:
```
tests/unit/test_drs_api_integration.py ............ 18 tests (NOT CREATED)
tests/unit/test_instance_matching.py ............ 12 tests (NOT CREATED)
tests/unit/test_drs_error_handling.py ........... 14 tests (NOT CREATED)
tests/unit/test_allow_launching_into_instance.py . 15 tests (NOT CREATED)
tests/integration/test_drs_recovery_jobs.py ..... 15 tests (NOT CREATED)
tests/integration/test_drs_job_monitoring.py .... 10 tests (NOT CREATED)
tests/integration/test_failover_failback.py ..... 12 tests (NOT CREATED)
tests/e2e/test_complete_dr_cycle.py ............. 8 tests (NOT CREATED)

Total: 0/104 tests exist (104 planned)
```

**Planned Integration Test Scenarios**:
- Failover with 10 pre-provisioned instances (target RTO: 18 minutes)
- Failback to original instances (target RTO: 22 minutes)
- Name tag matching with 100 instance pairs
- Job monitoring with concurrent recoveries
- Error handling with simulated API failures

**Reference**: See research document Section 7 for test plan details.

---

## DRS Launch Configuration Architecture

DRS uses a two-level configuration system. Understanding both levels is essential for AllowLaunchingIntoThisInstance implementation.

### Two-Level Configuration System

**Level 1: DRS Launch Configuration** (API-Managed)
- Managed through DRS APIs (`update_launch_configuration`)
- High-level recovery settings
- **AllowLaunchingIntoThisInstance is configured at this level**

**Level 2: EC2 Launch Template** (Customer-Editable)
- Managed through EC2 APIs or console
- Low-level instance settings
- DRS will NOT override customer changes

### DRS Launch Configuration Settings

**Settings Managed via DRS API**:

| Setting | API Field | Values | Purpose |
|---------|-----------|--------|---------|
| **Launch Into Instance** | `launchIntoInstanceProperties.launchIntoEC2InstanceID` | EC2 Instance ID | Launch into existing instance |
| **Launch Disposition** | `launchDisposition` | `STOPPED`, `STARTED` | Auto-start after recovery |
| **Copy Private IP** | `copyPrivateIp` | `true`, `false` | Copy source IP to recovery |
| **Copy Tags** | `copyTags` | `true`, `false` | Copy source tags to recovery |
| **Right Sizing** | `targetInstanceTypeRightSizingMethod` | `NONE`, `BASIC`, `IN_AWS` | Instance type selection |
| **Licensing** | `licensing.osByol` | `true`, `false` | Bring your own license |

**Configuration Example**:
```python
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
|---------|---------|---------|
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
|---------|-----------------|
| **ImageId** | DRS creates recovery-specific AMIs |
| **UserData** | DRS may inject recovery scripts |
| **BlockDeviceMappings** | DRS manages disk mappings from source |
| **NetworkInterfaces.PrivateIpAddress** | DRS manages IP assignment |

### AllowLaunchingIntoThisInstance Configuration Pattern

**Two-Step Configuration Process**:

```python
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
- Prevents conflicts between DRS settings and pre-provisioned instance configuration
- Ensures DRS doesn't try to modify target instance properties
- Based on working SSM automation pattern

### Launch Template Validation

**Validate Target Instance Configuration**:
```python
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
```python
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
```python
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
```python
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
```python
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
```python
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
```python
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
|---------|----------------------|----------------------|
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
   ```python
   targetInstanceTypeRightSizingMethod='NONE'
   ```

2. **Disable IP Copying**: Preserve target instance's existing IP
   ```python
   copyPrivateIp=False
   ```

3. **Control Launch Disposition**: Use STOPPED for validation before starting
   ```python
   launchDisposition='STOPPED'
   ```

4. **Tag Management**: Sync tags separately via existing tag sync capability
   ```python
   copyTags=True  # Or False if using separate tag sync
   ```

5. **Launch Template**: Ensure target instance launch template doesn't conflict with DRS-managed fields

6. **Change Detection**: Compare current vs desired settings before API calls (AWS Labs pattern)

7. **Validation First**: Validate all prerequisites before configuration (AWS Labs pattern)

8. **Clean API Calls**: Remove None values from parameters (AWS Labs pattern)

### Configuration Validation Checklist

Before configuring AllowLaunchingIntoThisInstance:

- [ ] Target instance has `AWSDRS=AllowLaunchingIntoThisInstance` tag
- [ ] Target instance is in `stopped` state
- [ ] Target instance Name tag matches source server hostname
- [ ] Launch template (if exists) doesn't set ImageId or UserData
- [ ] Security groups are appropriate for recovery workload
- [ ] IAM instance profile has required permissions
- [ ] Subnet is in correct availability zone
- [ ] EBS volumes are properly configured

---

## DRS Recovery Process Integration

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
|--------|------------------|--------------------------------|
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

**Failback Scenario**: After DR event, return workloads from DR region to primary region

**Standard Failback** (without AllowLaunchingIntoThisInstance):
```
1. Recovery instance running in DR region (new instance)
2. Reverse replication: DR → Primary (creates new staging)
3. Failback recovery: Creates new instance in primary region
4. Result: Yet another new instance (total: 3 instances created)
```

**AllowLaunchingIntoThisInstance Failback** (preserves original):
```
1. Recovery instance running in DR region (pre-provisioned instance)
2. Reverse replication: DR → Primary (to original source instance)
3. Configure failback target: Original source instance ID
4. Failback recovery: Launches into original source instance
5. Result: Original instance restored (total: 0 new instances)
```

### Failback API Sequence

```python
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
```python
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
```python
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
- Standard Recovery: 2-4 hours (new instance creation)
- AllowLaunchingIntoThisInstance: 15-30 minutes (volume replacement only)

### Drill vs Recovery Execution

**Drill Execution** (`isDrill=True`):
- Purpose: Testing without production impact
- Creates isolated recovery instances
- Always terminates instances after testing
- Lower risk

**Production Recovery** (`isDrill=False`):
- Purpose: Actual disaster recovery
- Launches into pre-provisioned instances
- Instances remain running for production use
- Higher risk - requires validation

**Note for AllowLaunchingIntoThisInstance**:
```python
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
```python
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

## Technical Implementation Details

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
- **Tag Sync**: Reuse existing `POST /infrastructure/tag-sync` endpoint
- **Discovery**: Reuse existing Resource Explorer queries
- **Orchestration**: Integrate into existing Step Functions workflow
- **Monitoring**: Reuse existing DRS job polling mechanism

### Tagging Policy for DRS Recovery

**Required Tags for AllowLaunchingIntoThisInstance**:

When using DRS recovery with pre-provisioned instances, the following tagging policy applies:

```
IF dr:enabled=true AND dr:recovery-strategy=drs
THEN AWSDRS=AllowLaunchingIntoThisInstance (REQUIRED)
```

**Tag Definitions**:
- `dr:enabled` - true/false (identifies resources for DR orchestration)
- `dr:recovery-strategy` - drs (specifies DRS as the recovery method)
- `AWSDRS` - AllowLaunchingIntoThisInstance (enables pre-provisioned instance recovery)

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
- AWS Config rules will enforce the tagging policy
- Resources with `dr:recovery-strategy=drs` must have `AWSDRS=AllowLaunchingIntoThisInstance`
- Missing tags will trigger compliance violations
- Automated remediation can apply missing tags

**Implementation Notes**:
- Tag synchronization will copy `AWSDRS` tag from EC2 to DRS source servers
- Discovery queries will filter for resources with `AWSDRS=AllowLaunchingIntoThisInstance`
- Name tag matching will use instances with this tag to identify pre-provisioned targets

### AllowLaunchingIntoThisInstance Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│         AllowLaunchingIntoThisInstance Pattern                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Primary Region (us-east-1)          DR Region (us-east-2)      │
│  ┌──────────────────────┐            ┌──────────────────────┐  │
│  │  Source Instance     │            │  Target Instance     │  │
│  │  i-0abc123 (running) │            │  i-0def456 (stopped) │  │
│  │  Name: web-app01     │───────────▶│  Name: web-app01     │  │
│  │  IP: 10.0.1.100      │  DRS       │  IP: 10.1.1.100      │  │
│  │                      │ Replication │                      │  │
│  └──────────────────────┘            └──────────────────────┘  │
│           │                                     │                │
│           │ Failover Initiated                  │                │
│           ▼                                     ▼                │
│  ┌──────────────────────┐            ┌──────────────────────┐  │
│  │  Source Instance     │            │  Recovery Instance   │  │
│  │  i-0abc123 (stopped) │            │  i-0def456 (running) │  │
│  │  Name: web-app01     │            │  Name: web-app01     │  │
│  │  IP: 10.0.1.100      │            │  IP: 10.1.1.100      │  │
│  │                      │            │  (Launched into      │  │
│  │                      │            │   pre-provisioned    │  │
│  │                      │            │   instance)          │  │
│  └──────────────────────┘            └──────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

Key Benefits:
- Preserves IP address last octet (10.0.1.100 → 10.1.1.100)
- Maintains instance identity (Name tag, metadata)
- Reduces RTO: 15-30 minutes vs. 2-4 hours for new instance launch
- No DNS changes required (IP preserved)
- Application configuration unchanged
```

### Failover and Failback Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Failover Flow                                 │
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
│                    Failback Flow                                 │
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

## Production Deployment - NOT YET DEPLOYED

DRS Orchestration Module has not been deployed. This section describes the planned deployment once implementation is complete.

### Planned Deployment Information
- **Environment**: Development (planned)
- **Region**: us-east-1 (primary), us-east-2 (DR)
- **Account**: {ACCOUNT_ID}
- **Stack**: {STACK_NAME}
- **Branch**: feature/drs-orchestration-engine
- **Version**: TBD (not yet released)

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
# Deploy DRS orchestration module (NOT YET IMPLEMENTED)
cd infra/orchestration/drs-orchestration
./scripts/deploy.sh dev

# Verify deployment (NOT YET AVAILABLE)
aws cloudformation describe-stacks \
  --stack-name {STACK_NAME} \
  --query 'Stacks[0].StackStatus'

# Test DRS integration (NOT YET AVAILABLE)
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

## Developer Integration Guide - PLANNED IMPLEMENTATION

**⚠️ NOTE**: This section describes the **planned repository structure and integration steps** once implementation is complete. No actual code files exist yet.

### Planned Repository Structure

DRS orchestration module code will be located in:

```
he.platform.devops.aws.dr-orchestration/
├── infra/orchestration/drs-orchestration/
│   ├── lambda/
│   │   ├── shared/
│   │   │   ├── drs_client.py                  # TO BE CREATED
│   │   │   ├── instance_matcher.py            # TO BE CREATED
│   │   │   ├── drs_job_monitor.py             # TO BE CREATED
│   │   │   └── drs_error_handler.py           # TO BE CREATED
│   │   └── orchestration-stepfunctions/
│   │       └── index.py                       # TO BE UPDATED
│   ├── cfn/
│   │   ├── lambda-stack.yaml                  # TO BE UPDATED
│   │   └── step-functions-stack.yaml          # TO BE UPDATED
│   └── tests/
│       ├── unit/
│       │   ├── test_drs_api_integration.py    # TO BE CREATED
│       │   ├── test_instance_matching.py      # TO BE CREATED
│       │   └── test_allow_launching_into_instance.py  # TO BE CREATED
│       ├── integration/
│       │   ├── test_drs_recovery_jobs.py      # TO BE CREATED
│       │   ├── test_drs_job_monitoring.py     # TO BE CREATED
│       │   └── test_failover_failback.py      # TO BE CREATED
│       └── e2e/
│           └── test_complete_dr_cycle.py      # TO BE CREATED
```

**Repository URL**: [https://code.aws.dev/personal_projects/alias_d/duvvip/he.platform.devops.aws.dr-orchestration](https://code.aws.dev/personal_projects/alias_d/duvvip/he.platform.devops.aws.dr-orchestration)  
**Branch**: [feature/drs-orchestration-engine](https://code.aws.dev/personal_projects/alias_d/duvvip/he.platform.devops.aws.dr-orchestration/-/tree/feature/drs-orchestration-engine)

### Key Code Samples - PLANNED DESIGNS

All code samples below are planned designs from the research document. These files do not exist in the repository yet.

#### 1. Configure AllowLaunchingIntoThisInstance (PLANNED)

**Planned File**: `lambda/shared/drs_client.py` (TO BE CREATED)

**Reference**: Based on working SSM automation pattern in `scripts/updateDRSLaunchSettings.yaml`

```python
# PLANNED CODE - NOT YET IMPLEMENTED
# Pattern validated in production SSM automation

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
    
    NOTE: This function is PLANNED but NOT YET IMPLEMENTED.
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

#### 2. Match Primary-DR Instance Pairs (PLANNED)

**Planned File**: `lambda/shared/instance_matcher.py` (TO BE CREATED)

```python
# PLANNED CODE - NOT YET IMPLEMENTED
def match_primary_dr_instances(
    primary_instances: List[Dict],
    dr_instances: List[Dict]
) -> Dict[str, str]:
    """
    Match primary instances to DR instances by Name tag.
    Returns dict mapping primary instance ID to DR instance ID.
    
    NOTE: This function is PLANNED but NOT YET IMPLEMENTED.
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

#### 3. Create DRS Recovery Jobs (PLANNED)

**Planned File**: `lambda/orchestration-stepfunctions/index.py` (TO BE UPDATED)

```python
# PLANNED CODE - NOT YET IMPLEMENTED
def create_drs_recovery_jobs(instances: List[Dict]) -> List[Dict]:
    """
    Create DRS recovery jobs for tagged instances.
    Batches up to 20 servers per job (DRS limit).
    
    NOTE: This function is PLANNED but NOT YET IMPLEMENTED.
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

#### 4. Monitor DRS Recovery Job (PLANNED)

**Planned File**: `lambda/shared/drs_job_monitor.py` (TO BE CREATED)

```python
# PLANNED CODE - NOT YET IMPLEMENTED
def monitor_drs_recovery_job(job_id: str, timeout: int = 7200) -> Dict:
    """
    Monitor DRS recovery job until completion.
    Polls every 30 seconds, times out after 2 hours.
    
    NOTE: This function is PLANNED but NOT YET IMPLEMENTED.
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

#### 5. Initiate Failback Operation (PLANNED)

**Planned File**: `lambda/orchestration-stepfunctions/index.py` (TO BE UPDATED)

```python
# PLANNED CODE - NOT YET IMPLEMENTED
def initiate_failback(
    protection_group_id: str,
    primary_region: str,
    dr_region: str
) -> Dict:
    """
    Initiate failback from DR region to primary region.
    Launches into original primary instances.
    
    NOTE: This function is PLANNED but NOT YET IMPLEMENTED.
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
```

**Integration Point**: Call to return workloads to primary region after DR event.

---

### Integration Checklist - Pre-Implementation

Before starting DRS orchestration implementation:

- [ ] **Review Research Document**: Read [`DRS_ALLOW_LAUNCHING_INTO_THIS_INSTANCE_RESEARCH.md`](../../infra/orchestration/drs-orchestration/docs/implementation/DRS_ALLOW_LAUNCHING_INTO_THIS_INSTANCE_RESEARCH.md)
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

### Step-by-Step Integration Guide - PLANNED

**⚠️ NOTE**: These steps describe the **planned integration process** once implementation is complete.

#### Step 1: Clone Repository

```bash
git clone https://code.aws.dev/personal_projects/alias_d/duvvip/he.platform.devops.aws.dr-orchestration.git
cd he.platform.devops.aws.dr-orchestration
git checkout feature/drs-orchestration-engine
cd infra/orchestration/drs-orchestration
```

#### Step 2: Review Research Document

```bash
# Review comprehensive research document
cat docs/implementation/DRS_ALLOW_LAUNCHING_INTO_THIS_INSTANCE_RESEARCH.md
```

#### Step 3: Implement DRS Client (NOT YET DONE)

```bash
# Create DRS client module
# File: lambda/shared/drs_client.py
# Implement functions from research document Section 3.2
```

#### Step 4: Implement Instance Matcher (NOT YET DONE)

```bash
# Create instance matcher module
# File: lambda/shared/instance_matcher.py
# Implement name matching algorithm from research document Section 3.3
```

#### Step 5: Write Tests (NOT YET DONE)

```bash
# Create test files
mkdir -p tests/unit tests/integration tests/e2e

# Implement 104 planned tests
# See research document Section 7 for test plan
```

#### Step 6: Deploy to Development (NOT YET AVAILABLE)

```bash
./scripts/deploy.sh dev
```

#### Step 7: Test DRS Integration (NOT YET AVAILABLE)

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

- **README**: [Main README](https://code.aws.dev/personal_projects/alias_d/duvvip/he.platform.devops.aws.dr-orchestration/-/blob/feature/drs-orchestration-engine/infra/orchestration/drs-orchestration/README.md)
- **CHANGELOG**: [Version History](https://code.aws.dev/personal_projects/alias_d/duvvip/he.platform.devops.aws.dr-orchestration/-/blob/feature/drs-orchestration-engine/infra/orchestration/drs-orchestration/CHANGELOG.md)
- **AWS DRS Documentation**: [DRS User Guide](https://docs.aws.amazon.com/drs/latest/userguide/what-is-drs.html)
- **AllowLaunchingIntoThisInstance**: [DRS Launch Configuration](https://docs.aws.amazon.com/drs/latest/userguide/launch-settings.html)

---

## Performance Metrics - PROJECTED ESTIMATES

**⚠️ NOTE**: All metrics below are **PROJECTED ESTIMATES** from research, not actual measured results.

### RTO Comparison (Projected)

| Scenario | Without AllowLaunchingIntoThisInstance | With AllowLaunchingIntoThisInstance | Improvement |
|----------|---------------------------------------|-------------------------------------|-------------|
| 10 instances | 2.5 hours | 18 minutes | 88% |
| 50 instances | 4 hours | 25 minutes | 90% |
| 100 instances | 6 hours | 30 minutes | 92% |

### Failover Performance (Projected)

| Wave | Instance Count | Estimated Failover Time | Estimated Validation Time | Projected Total RTO |
|------|---------------|------------------------|---------------------------|---------------------|
| 1 (Critical) | 10 | 15 minutes | 3 minutes | 18 minutes |
| 2 (High) | 25 | 20 minutes | 5 minutes | 25 minutes |
| 3 (Medium) | 50 | 25 minutes | 5 minutes | 30 minutes |

### Failback Performance (Projected)

| Scenario | Estimated Failback Time | Estimated Validation Time | Projected Total Time |
|----------|------------------------|---------------------------|----------------------|
| 10 instances | 18 minutes | 4 minutes | 22 minutes |
| 50 instances | 28 minutes | 7 minutes | 35 minutes |
| 100 instances | 35 minutes | 10 minutes | 45 minutes |

### Name Tag Matching Accuracy (Projected)

| Instance Count | Expected Matched | Expected Unmatched | Projected Accuracy |
|---------------|------------------|--------------------|--------------------|
| 10 | 10 | 0 | 100% |
| 50 | 49 | 1 | 98% |
| 100 | 98 | 2 | 98% |
| 500 | 487 | 13 | 97.4% |

### Business Impact (Projected)

| Metric | Current State | Projected After Implementation | Expected Improvement |
|--------|---------------|-------------------------------|----------------------|
| Critical Workload RTO | 24+ hours | 15-30 minutes | 95% |
| IP Address Preservation | 0% | 100% | 100% |
| Instance Identity Preservation | 0% | 100% | 100% |
| DNS Changes Required | Yes | No | 100% |
| Application Reconfiguration | Required | Not Required | 100% |
| Manual Intervention | 80% of operations | 5% of operations | 94% |

**Note**: All metrics are estimates based on research findings and archive code analysis. Actual results will be measured during implementation and testing.

---

## Related Documentation

### Design Documents
- [Enterprise DR Orchestration Platform - Design Docs](../../docs/HRP/DESIGN-DOCS/README.md)
- [BRD - Business Requirements](../../docs/HRP/DESIGN-DOCS/00-BRD-Enterprise-DR-Orchestration-Platform.md)
- [PRD - Product Requirements](../../docs/HRP/DESIGN-DOCS/01-PRD-Enterprise-DR-Orchestration-Platform.md)
- [SRS - Software Requirements](../../docs/HRP/DESIGN-DOCS/02-SRS-Enterprise-DR-Orchestration-Platform.md)
- [TRS - Technical Requirements](../../docs/HRP/DESIGN-DOCS/03-TRS-Enterprise-DR-Orchestration-Platform.md)

### Architecture Documents
- [ADR-003: AllowLaunchingIntoThisInstance Pattern](../../docs/architecture/ADR-003-allowlaunchingintothisinstance-pattern.md)
- [ADR-004: Step Functions Orchestration](../../docs/architecture/ADR-004-step-functions-orchestration.md)
- [System Architecture](../../docs/architecture/system-architecture.md)

### Related User Stories
- [AWSM-1088: Wave-Based Orchestration Logic](./AWSM-1088-Wave-Based-Orchestration-Implementation.md)
- [AWSM-1112: Handle DRS API Rate Limits](./AWSM-1112-DRS-API-Rate-Limit-Handling.md)

---

## Conclusion

DRS Orchestration Module research has been **completed** with comprehensive implementation planning documented in [`DRS_ALLOW_LAUNCHING_INTO_THIS_INSTANCE_RESEARCH.md`](../../infra/orchestration/drs-orchestration/docs/implementation/DRS_ALLOW_LAUNCHING_INTO_THIS_INSTANCE_RESEARCH.md).

**Current Status**: 🔴 **NOT STARTED** - Research Complete, Implementation Pending

**Research Achievements**:
- ✅ AllowLaunchingIntoThisInstance pattern validated from archive code
- ✅ Name tag matching algorithm designed (98%+ projected accuracy)
- ✅ Recovery job creation workflow planned for failover and failback
- ✅ Job status monitoring design with 30-second polling
- ✅ Comprehensive error handling strategy for DRS API failures
- ✅ 104 test cases planned (unit, integration, end-to-end)

**Projected Business Impact** (Once Implemented):
- 95% RTO improvement for critical workloads (24+ hours → 15-30 minutes)
- 100% IP address and instance identity preservation
- 100% elimination of DNS changes and application reconfiguration
- 94% reduction in manual intervention (80% → 5%)

**Implementation Requirements**:
- **Team**: 2-3 developers + 1 QA engineer
- **Prerequisites**: DRS agents deployed, pre-provisioned instances, IAM roles configured
- **Testing**: 104 test cases across unit, integration, and end-to-end scenarios

**Next Steps**:
1. **IMMEDIATE**: Allocate development resources (2-3 developers) - **HIGHEST PRIORITY**
2. Set up test environment with DRS agents and pre-provisioned instances
3. Implement DRS client module (`lambda/shared/drs_client.py`)
4. Implement instance matcher (`lambda/shared/instance_matcher.py`)
5. Write and execute 104 planned tests
6. Deploy to development environment
7. Conduct integration testing with real DRS service
8. Production deployment

**Priority Justification**:
- **Business Critical**: 95% RTO improvement is the highest-impact capability
- **Customer Demand**: Directly addresses primary customer pain point (long recovery times)
- **Risk Mitigation**: Reduces business risk exposure by $9M+ annually
- **Foundation**: Enables future disaster recovery enhancements

**Reference Documentation**:
- **Primary**: [`DRS_ALLOW_LAUNCHING_INTO_THIS_INSTANCE_RESEARCH.md`](../../infra/orchestration/drs-orchestration/docs/implementation/DRS_ALLOW_LAUNCHING_INTO_THIS_INSTANCE_RESEARCH.md)
- **Related**: [AWSM-1088: Wave-Based Orchestration](./AWSM-1088-Wave-Based-Orchestration-Implementation.md)
- **Related**: [AWSM-1112: DRS API Rate Limits](./AWSM-1112-DRS-API-Rate-Limit-Handling.md)

---

**Ticket Status**: � **HIGHEST PRIORITY - RESEARCH COMPLETE - IMMEDIATE IMPLEMENTATION REQUIRED**

**Research Completed By**: AWS DRS Orchestration Team  
**Research Reviewed By**: Technical Lead  
**Implementation Approval**: **URGENT** - Resource Allocation Required Immediately  
**Business Sponsor**: Product Owner (95% RTO improvement justification)
