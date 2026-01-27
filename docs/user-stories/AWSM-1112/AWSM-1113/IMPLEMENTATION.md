# DRS Drill Mode for Risk-Free DR Testing

**Confluence Title**: DRS Drill Mode Implementation - Isolated DR Testing Without Production Impact  
**Description**: Implementation guide for AWS DRS drill mode capability, enabling risk-free disaster recovery testing through isolated test networks and automatic cleanup. Covers drill mode configuration, test network architecture, and automated resource cleanup strategies.

**JIRA Ticket**: [AWSM-1113](https://healthedge.atlassian.net/browse/AWSM-1113)  
**Epic**: [AWSM-1112 - DRS Integration and EC2 Recovery](https://healthedge.atlassian.net/browse/AWSM-1112)  
**Status**: 🟡 **PARTIALLY IMPLEMENTED**  
**Priority**: Medium  
**Business Impact**: Risk-free DR testing without production impact

---

## Executive Summary

DRS Drill Mode enables isolated DR testing by launching recovery instances in a separate test network, allowing validation of DR capabilities without impacting production workloads. Drill instances are automatically terminated after testing, ensuring no resource waste.

**Current Status**: Drill mode parameter (`isDrill`) is implemented and passed to DRS API. Missing: isolated test network configuration and automatic cleanup logic.

**Key Achievement Target**: Enable quarterly DR testing with zero production impact and automatic cleanup.

---

## Acceptance Criteria Status

### ✅ Criterion 1: Drill Mode Parameter
**Requirement**: *Given* test operation request, *When* initiating DRS recovery, *Then* drill mode is used instead of recovery mode.

**Status**: ✅ **IMPLEMENTED**

**What's Implemented**:
- ✅ `isDrill` parameter in Step Functions orchestration workflow
- ✅ `isDrill` parameter passed to `start_drs_recovery()` function
- ✅ DRS API call includes `isDrill=is_drill` parameter
- ✅ Drill mode tracked in execution state
- ✅ **Terminate recovery instances after drill** via `terminate_recovery_instances()` function
- ✅ **DRS TerminateRecoveryInstances API integration** with proper job tracking
- ✅ **Cross-account termination support** using account context from recovery plan
- ✅ **Multi-region termination** with regional DRS client creation

**Implementation Location**:
- Step Functions: `lambda/orchestration-stepfunctions/index.py` (lines 269, 276, 529, 587)
- DRS Recovery: `lambda/api-handler/index.py` (line 4860)
- Terminate Instances: `lambda/api-handler/index.py` (lines 6954-7470)

**Code Evidence**:
```python
# Step Functions orchestration
is_drill = event.get("isDrill", True)
print(f"Total waves: {len(waves)}, isDrill: {is_drill}")

# DRS API call
response = drs_client.start_recovery(
    sourceServers=[{"sourceServerID": server_id}], 
    isDrill=is_drill
)

# Terminate recovery instances after drill
def terminate_recovery_instances(execution_id: str) -> Dict:
    """Terminate all recovery instances from an execution.
    
    Uses DRS TerminateRecoveryInstances API to properly clean up
    recovery instances and create TERMINATE jobs in DRS console.
    """
    # Collects recovery instances from DRS jobs
    # Calls drs_client.terminate_recovery_instances()
    # Tracks termination jobs and updates execution record
```

**API Endpoint**:
```bash
# Terminate recovery instances after drill
POST /executions/{executionId}/terminate-instances
```

**What's Missing**:
- Drill-specific network configuration (uses production network)
- Drill mode flag in Protection Group configuration
- UI/API parameter for drill vs. recovery mode selection
- Automatic termination trigger after drill completion (currently manual via API)

---

### ❌ Criterion 2: Isolated Test Network
**Requirement**: *Given* drill mode execution, *When* instances are launched, *Then* instances are launched in isolated test network.

**Status**: ❌ **NOT IMPLEMENTED**

**What's Missing**:
- Test network configuration (VPC, subnets, security groups)
- Drill-specific launch template configuration
- Network isolation validation
- Test network documentation

**Design Considerations**:
- Separate VPC or isolated subnets for drill instances
- No connectivity to production resources
- Internet access for testing (optional)
- DNS resolution for application testing

**Implementation Approach**:
```python
def configure_drill_network(launch_config: Dict) -> Dict:
    """Configure isolated test network for drill mode."""
    drill_config = launch_config.copy()
    
    # Override with drill-specific network settings
    drill_config['subnetId'] = get_drill_subnet(launch_config['subnetId'])
    drill_config['securityGroupIds'] = get_drill_security_groups()
    
    return drill_config
```

---

### 🟡 Criterion 3: Automatic Cleanup
**Requirement**: *Given* drill completion, *When* test is finished, *Then* drill instances are automatically terminated.

**Status**: 🟡 **PARTIALLY IMPLEMENTED** (Manual termination available, automatic trigger not implemented)

**What's Implemented**:
- ✅ **Manual termination via API endpoint**: `POST /executions/{executionId}/terminate-instances`
- ✅ **DRS TerminateRecoveryInstances API integration** (lines 6954-7470)
- ✅ **Cross-account termination support** using recovery plan account context
- ✅ **Multi-region termination** with regional DRS client creation
- ✅ **Job tracking** for termination operations in DRS console
- ✅ **Execution record updates** with termination status and timestamps

**Implementation Details**:
```python
# File: lambda/api-handler/index.py (lines 6954-7470)
def terminate_recovery_instances(execution_id: str) -> Dict:
    """Terminate all recovery instances from an execution.
    
    This will:
    1. Find all recovery instances created by this execution (from DRS jobs)
    2. Call DRS TerminateRecoveryInstances API
    3. Track termination jobs in DRS console
    4. Update execution record with termination status
    
    Supports cross-account executions by using the same account context
    as the original execution.
    """
    # Collects recovery instances from DRS jobs
    # Groups by region for batch termination
    # Calls drs_client.terminate_recovery_instances()
    # Updates execution with instancesTerminated flag
```

**API Usage**:
```bash
# Terminate recovery instances after drill
curl -X POST https://api.example.com/executions/{executionId}/terminate-instances \
  -H "Authorization: Bearer $TOKEN"

# Response
{
  "executionId": "exec-123",
  "message": "Initiated termination of 10 recovery instances via DRS",
  "terminated": [...],
  "jobs": [{"jobId": "job-456", "region": "us-east-1", "type": "TERMINATE"}],
  "totalTerminated": 10
}
```

**What's Missing**:
- Automatic termination trigger after drill completion
- Cleanup timeout configuration (e.g., 4 hours)
- Manual cleanup override for extended testing
- Scheduled cleanup for abandoned drill instances

---

## Definition of Done - Implementation Checklist

### ✅ 1. Drill Mode Parameter Added
**Status**: ✅ **COMPLETE**

See Criterion 1 above for implementation details.

**Still Needed**:

1. **Add drill mode to Protection Group schema**:
```python
# DynamoDB Protection Group schema enhancement
{
    "groupId": "pg-abc123",
    "groupName": "Production Web Servers",
    "drillMode": {
        "enabled": True,
        "autoCleanupHours": 4,
        "testNetwork": {
            "vpcId": "vpc-drill-123",
            "subnetId": "subnet-drill-123",
            "securityGroupIds": ["sg-drill-123"]
        }
    }
}
```

2. **Add drill mode parameter to DRS API calls**:
```python
def start_drs_recovery(
    source_server_ids: List[str],
    is_drill: bool = False,
    region: str = None
) -> Dict:
    """Start DRS recovery with optional drill mode."""
    drs = boto3.client('drs', region_name=region)
    
    response = drs.start_recovery(
        sourceServers=[
            {'sourceServerID': sid} for sid in source_server_ids
        ],
        isDrill=is_drill,
        tags={'ExecutionMode': 'drill' if is_drill else 'recovery'}
    )
    
    return response
```

3. **Add drill mode to API Gateway endpoints**:
```python
# POST /protection-groups/{groupId}/recover
{
    "operation": "recovery",  # or "drill"
    "waves": [1, 2, 3],
    "drillMode": {
        "enabled": True,
        "autoCleanupHours": 4
    }
}
```

**Files to Modify**:
- `infra/orchestration/drs-orchestration/lambda/api-handler/index.py`
- `infra/orchestration/drs-orchestration/lambda/orchestration-stepfunctions/index.py`
- `infra/orchestration/drs-orchestration/cfn/database-stack.yaml` (DynamoDB schema)

---

### ❌ 2. Isolated Test Network Configuration
**Status**: ❌ **NOT STARTED**

**Required Infrastructure**:

1. **Test VPC and Subnets** (CloudFormation):
```yaml
DrillTestVPC:
  Type: AWS::EC2::VPC
  Properties:
    CidrBlock: 10.255.0.0/16
    EnableDnsHostnames: true
    EnableDnsSupport: true
    Tags:
      - Key: Name
        Value: !Sub '${AWS::StackName}-drill-test-vpc'
      - Key: Purpose
        Value: DRS-Drill-Testing

DrillTestSubnet:
  Type: AWS::EC2::Subnet
  Properties:
    VpcId: !Ref DrillTestVPC
    CidrBlock: 10.255.1.0/24
    AvailabilityZone: !Select [0, !GetAZs '']
    Tags:
      - Key: Name
        Value: !Sub '${AWS::StackName}-drill-test-subnet'
```

2. **Drill Security Group** (CloudFormation):
```yaml
DrillSecurityGroup:
  Type: AWS::EC2::SecurityGroup
  Properties:
    GroupDescription: Security group for DRS drill instances
    VpcId: !Ref DrillTestVPC
    SecurityGroupIngress:
      - IpProtocol: tcp
        FromPort: 22
        ToPort: 22
        CidrIp: 10.0.0.0/8  # Internal access only
      - IpProtocol: tcp
        FromPort: 443
        ToPort: 443
        CidrIp: 10.0.0.0/8
    Tags:
      - Key: Name
        Value: !Sub '${AWS::StackName}-drill-sg'
```

3. **Network Configuration Function**:
```python
def get_drill_network_config(
    production_subnet_id: str,
    region: str
) -> Dict:
    """Get drill network configuration for a production subnet."""
    # Map production subnets to drill subnets
    subnet_mapping = get_drill_subnet_mapping(region)
    
    drill_subnet = subnet_mapping.get(production_subnet_id)
    if not drill_subnet:
        raise ValueError(
            f"No drill subnet mapping found for {production_subnet_id}"
        )
    
    return {
        'subnetId': drill_subnet['subnetId'],
        'securityGroupIds': drill_subnet['securityGroupIds'],
        'vpcId': drill_subnet['vpcId']
    }
```

**Files to Create**:
- `infra/orchestration/drs-orchestration/cfn/drill-network-stack.yaml`
- `infra/orchestration/drs-orchestration/lambda/shared/drill_network.py`

---

### ❌ 3. Automatic Cleanup Logic
**Status**: ❌ **NOT STARTED**

**Required Components**:

1. **Drill Instance Tracking** (DynamoDB):
```python
# DynamoDB table: drs-orchestration-drill-instances
{
    "executionId": "exec-12345",
    "instanceId": "i-drill-001",
    "sourceServerId": "s-source-001",
    "launchTime": "2026-01-20T17:00:00Z",
    "cleanupTime": "2026-01-20T21:00:00Z",  # 4 hours later
    "status": "running",  # running, terminated, failed
    "autoCleanup": True
}
```

2. **Cleanup Lambda Function**:
```python
def lambda_handler(event, context):
    """
    Scheduled Lambda to cleanup expired drill instances.
    Triggered every hour by EventBridge rule.
    """
    now = datetime.utcnow()
    
    # Query drill instances past cleanup time
    expired_instances = query_expired_drill_instances(now)
    
    for instance in expired_instances:
        try:
            terminate_drill_instance(
                instance['instanceId'],
                instance['executionId']
            )
            
            logger.info(
                f"Terminated drill instance {instance['instanceId']} "
                f"from execution {instance['executionId']}"
            )
        except Exception as e:
            logger.error(
                f"Failed to terminate {instance['instanceId']}: {e}"
            )
    
    return {
        'cleanedUpInstances': len(expired_instances)
    }
```

3. **EventBridge Scheduled Rule**:
```yaml
DrillCleanupSchedule:
  Type: AWS::Events::Rule
  Properties:
    Description: Cleanup expired DRS drill instances
    ScheduleExpression: rate(1 hour)
    State: ENABLED
    Targets:
      - Arn: !GetAtt DrillCleanupLambda.Arn
        Id: DrillCleanupTarget
```

**Files to Create**:
- `infra/orchestration/drs-orchestration/lambda/drill-cleanup/index.py`
- `infra/orchestration/drs-orchestration/cfn/drill-cleanup-stack.yaml`

---

### ❌ 4. Drill Mode Testing
**Status**: ❌ **NOT STARTED**

**Test Scenarios**:

1. **Drill Mode Execution Test**:
   - Configure Protection Group with drill mode enabled
   - Execute drill recovery
   - Verify instances launched in test network
   - Verify production network unaffected

2. **Automatic Cleanup Test**:
   - Execute drill with 1-hour cleanup timeout
   - Wait 1 hour
   - Verify instances automatically terminated
   - Verify DynamoDB tracking updated

3. **Manual Cleanup Test**:
   - Execute drill
   - Manually trigger cleanup before timeout
   - Verify immediate termination

4. **Network Isolation Test**:
   - Launch drill instances
   - Verify no connectivity to production resources
   - Verify internal test network connectivity

**Test Files to Create**:
- `tests/integration/test_drill_mode.py`
- `tests/e2e/test_drill_cleanup.py`

---

### ❌ 5. Drill Mode Documentation
**Status**: ❌ **NOT STARTED**

**Required Documentation**:

1. **Drill Mode User Guide** (`docs/guides/drs-drill-mode.md`):
   - What is drill mode and when to use it
   - How to configure drill mode in Protection Groups
   - How to execute drill recovery
   - How to validate drill results
   - How to manually cleanup drill instances

2. **Drill Network Architecture** (`docs/architecture/drill-network-design.md`):
   - Test VPC and subnet design
   - Network isolation strategy
   - Security group configuration
   - DNS and connectivity considerations

3. **Drill Mode Runbook** (`docs/runbooks/quarterly-dr-drill.md`):
   - Pre-drill checklist
   - Drill execution procedure
   - Post-drill validation
   - Cleanup verification
   - Lessons learned documentation

---

## Current Implementation Status

### What's Working

1. **DRS API Integration**:
   - `start_recovery()` API calls functional
   - Source server management working
   - Recovery job monitoring implemented

2. **Protection Group Management**:
   - Protection Group CRUD operations
   - Launch configuration management
   - Server assignment to groups

### What's Missing

1. **Drill Mode Logic**:
   - `isDrill` parameter not used
   - No drill network configuration
   - No drill instance tracking

2. **Test Network Infrastructure**:
   - No drill VPC/subnets provisioned
   - No drill security groups configured
   - No subnet mapping logic

3. **Cleanup Automation**:
   - No drill instance tracking table
   - No cleanup Lambda function
   - No EventBridge scheduled rule

---

## Implementation Priority

### Phase 1: Core Drill Mode (2 weeks)
1. Add `isDrill` parameter to DRS API calls
2. Implement drill network configuration function
3. Add drill mode to Protection Group schema
4. Unit tests for drill mode logic

### Phase 2: Test Network Infrastructure (1 week)
1. Create drill VPC and subnets (CloudFormation)
2. Create drill security groups
3. Implement subnet mapping logic
4. Deploy test network to dev environment

### Phase 3: Automatic Cleanup (1 week)
1. Create drill instance tracking table
2. Implement cleanup Lambda function
3. Create EventBridge scheduled rule
4. Test automatic cleanup

### Phase 4: Documentation and Testing (1 week)
1. Write drill mode user guide
2. Write drill network architecture doc
3. Create quarterly DR drill runbook
4. End-to-end drill mode testing

---

## Related Stories

- AWSM-1111 - Core DRS integration
- AWSM-1116 - Pre-drill validation
