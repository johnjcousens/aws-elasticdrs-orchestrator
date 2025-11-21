# AWS DRS to VMware SRM API Mapping Guide

A comprehensive mapping between AWS Elastic Disaster Recovery (DRS) and VMware Site Recovery Manager (SRM) REST API functionality.

## Overview

This document provides a detailed mapping between AWS DRS and VMware SRM APIs, enabling organizations to understand equivalent functionality when migrating from VMware SRM to AWS DRS or building hybrid solutions.

## Core Concept Mapping

| VMware SRM Concept | AWS DRS Equivalent | Notes |
|-------------------|-------------------|-------|
| Protection Group | Protection Group (Custom) | DRS doesn't have native PGs - implemented via tags/grouping |
| Recovery Plan | Recovery Plan (Custom) | DRS doesn't have native plans - implemented via orchestration |
| Virtual Machine | Source Server | DRS protects physical/virtual servers |
| Datastore | EBS Volume/Snapshot | DRS replicates individual disks |
| Site Pairing | Cross-Region/Account | DRS supports multi-region recovery |
| Placeholder VM | Recovery Instance + AWSDRS Tag | DRS creates EC2 instances during recovery or uses existing tagged instances |
| Recovery Priority Group | Wave (Custom) | Implemented via Step Functions orchestration |

## Protection Group Management

### List Protection Groups

**VMware SRM**:
```http
GET /api/protection-groups
```

**AWS DRS Equivalent**:
```python
# Custom implementation - no native DRS API
# Query DynamoDB table or use tagging
def list_protection_groups():
    return dynamodb.scan(TableName='ProtectionGroups')
```

**Mapping Notes**:
- SRM has native protection groups
- DRS requires custom implementation using tags or external storage
- Our solution uses DynamoDB to store protection group metadata

### Create Protection Group

**VMware SRM**:
```http
POST /api/protection-groups
{
  "name": "WebServers-PG",
  "type": "san",
  "input_spec": {
    "datastore_groups": [{"datastores": ["ds-001"]}]
  }
}
```

**AWS DRS Equivalent**:
```python
# Custom implementation
def create_protection_group(name, server_ids):
    # Store in DynamoDB
    dynamodb.put_item(
        TableName='ProtectionGroups',
        Item={
            'GroupId': str(uuid.uuid4()),
            'GroupName': name,
            'SourceServerIds': server_ids
        }
    )
    
    # Tag servers for grouping
    for server_id in server_ids:
        drs_client.tag_resource(
            resourceArn=f'arn:aws:drs:region:account:source-server/{server_id}',
            tags={'ProtectionGroup': name}
        )
```

### Get Protection Group VMs/Servers

**VMware SRM**:
```http
GET /api/protection-groups/{pg-id}
# Returns VMs in protection group
```

**AWS DRS Equivalent**:
```python
# List servers by protection group tag
def get_protection_group_servers(pg_name):
    response = drs_client.describe_source_servers()
    return [
        server for server in response['items']
        if server.get('tags', {}).get('ProtectionGroup') == pg_name
    ]
```

## Recovery Plan Management

### List Recovery Plans

**VMware SRM**:
```http
GET /api/recovery-plans
```

**AWS DRS Equivalent**:
```python
# Custom implementation
def list_recovery_plans():
    return dynamodb.scan(TableName='RecoveryPlans')
```

### Create Recovery Plan

**VMware SRM**:
```http
POST /api/recovery-plans
{
  "name": "WebApp-Recovery",
  "protection_groups": [
    {
      "protection_group_id": "pg-001",
      "recovery_priority_group": {"priority": 1}
    }
  ]
}
```

**AWS DRS Equivalent**:
```python
# Custom implementation with Step Functions
def create_recovery_plan(name, waves):
    plan_id = str(uuid.uuid4())
    
    # Store plan metadata
    dynamodb.put_item(
        TableName='RecoveryPlans',
        Item={
            'PlanId': plan_id,
            'PlanName': name,
            'Waves': waves
        }
    )
    
    # Create Step Function state machine
    stepfunctions.create_state_machine(
        name=f'recovery-plan-{plan_id}',
        definition=generate_state_machine_definition(waves)
    )
```

## Recovery Execution

### Start Recovery (Test/Planned/Emergency)

**VMware SRM**:
```http
POST /api/recovery-plans/{rp-id}/recovery
{
  "recovery_type": "test",
  "sync_data": true,
  "recovery_options": {
    "power_on_vms": true
  }
}
```

**AWS DRS Equivalent**:
```python
# Start recovery using DRS API
def start_recovery(server_ids, is_drill=False):
    source_servers = [
        {
            'sourceServerID': server_id,
            'recoveryInstanceProperties': {
                'targetInstanceTypeRightSizingMethod': 'BASIC'
            }
        }
        for server_id in server_ids
    ]
    
    return drs_client.start_recovery(
        sourceServers=source_servers,
        isDrill=is_drill
    )
```

### Monitor Recovery Progress

**VMware SRM**:
```http
GET /api/recovery-plans/{rp-id}/recovery-history/{rh-id}
```

**AWS DRS Equivalent**:
```python
# Monitor DRS job progress
def monitor_recovery_job(job_id):
    return drs_client.describe_jobs(
        filters={'jobIDs': [job_id]}
    )
```

### Cleanup Test Recovery

**VMware SRM**:
```http
POST /api/recovery-plans/{rp-id}/cleanup
{
  "recovery_history_id": "rh-12345"
}
```

**AWS DRS Equivalent**:
```python
# Terminate recovery instances
def cleanup_test_recovery(recovery_instance_ids):
    return drs_client.terminate_recovery_instances(
        recoveryInstanceIDs=recovery_instance_ids
    )
```

## Virtual Machine / Source Server Management

### List Protected VMs/Servers

**VMware SRM**:
```http
GET /api/vms
```

**AWS DRS Equivalent**:
```python
# List all DRS source servers
def list_source_servers():
    return drs_client.describe_source_servers()
```

### Configure VM Recovery Settings

**VMware SRM**:
```http
PUT /api/vms/{vm-id}/recovery-settings
{
  "priority": "high",
  "startup_delay": 60,
  "ip_customization": {
    "enabled": true,
    "ip_address": "10.0.2.100"
  }
}
```

**AWS DRS Equivalent**:
```python
# Configure launch settings
def configure_launch_settings(server_id, settings):
    return drs_client.update_launch_configuration(
        sourceServerID=server_id,
        launchDisposition='STARTED',
        targetInstanceTypeRightSizingMethod='BASIC',
        copyPrivateIp=settings.get('copyPrivateIp', False),
        postLaunchActions={
            'deployment': 'TEST_AND_CUTOVER',
            'ssmDocuments': settings.get('ssmDocuments', [])
        }
    )
```

## Replication Management

### Get Replication Status

**VMware SRM**:
```http
GET /api/protection-groups/{pg-id}
# Returns protection state and replication info
```

**AWS DRS Equivalent**:
```python
# Get server replication status
def get_replication_status(server_id):
    response = drs_client.describe_source_servers(
        filters={'sourceServerIDs': [server_id]}
    )
    
    server = response['items'][0]
    return {
        'state': server['dataReplicationInfo']['dataReplicationState'],
        'lagDuration': server['dataReplicationInfo']['lagDuration'],
        'error': server['dataReplicationInfo']['dataReplicationError']
    }
```

### Configure Replication Settings

**VMware SRM**:
```http
# Configured through vSphere Replication
```

**AWS DRS Equivalent**:
```python
# Configure replication settings
def configure_replication(server_id, settings):
    return drs_client.update_replication_configuration(
        sourceServerID=server_id,
        stagingAreaSubnetId=settings['subnetId'],
        replicationServerInstanceType=settings.get('instanceType', 't3.small'),
        ebsEncryption='DEFAULT',
        pitPolicy=settings.get('pitPolicy', [])
    )
```

## Site Management

### List Sites

**VMware SRM**:
```http
GET /api/sites
```

**AWS DRS Equivalent**:
```python
# List AWS regions where DRS is available
def list_available_regions():
    return [
        'us-east-1', 'us-west-2', 'eu-west-1', 
        'ap-southeast-1', 'ap-northeast-1'
    ]
```

### Get Site Pairing Status

**VMware SRM**:
```http
GET /api/sites/{site-id}/pairing
```

**AWS DRS Equivalent**:
```python
# Check cross-region/account connectivity
def check_cross_region_connectivity(source_region, target_region):
    # Custom implementation - check IAM roles, network connectivity
    return {
        'source_region': source_region,
        'target_region': target_region,
        'connectivity': 'connected',
        'iam_roles_configured': True
    }
```

## Inventory and Resource Management

### List Datastores

**VMware SRM**:
```http
GET /api/datastores
```

**AWS DRS Equivalent**:
```python
# List EBS volumes for source servers
def list_server_volumes(server_id):
    response = drs_client.describe_source_servers(
        filters={'sourceServerIDs': [server_id]}
    )
    
    server = response['items'][0]
    return server['sourceProperties']['disks']
```

### List Resource Pools

**VMware SRM**:
```http
GET /api/resource-pools
```

**AWS DRS Equivalent**:
```python
# List EC2 instance types and availability
def list_instance_types():
    ec2 = boto3.client('ec2')
    return ec2.describe_instance_types()
```

## Placeholder VM / Recovery Instance Management

### VMware SRM Placeholder VMs

**VMware SRM**:
```http
GET /api/vms/{vm-id}
# Returns placeholder VM information
{
  "vm_id": "vm-001",
  "name": "web-server-01",
  "placeholder_vm_id": "vm-placeholder-001",
  "recovery_settings": {
    "target_host": "esx-host-02",
    "target_datastore": "recovery-ds-001"
  }
}
```

### AWS DRS Recovery Instance Targeting

**AWS DRS Equivalent**:
```python
# Method 1: Tag existing EC2 instance as recovery target
def configure_recovery_target_instance(target_instance_id, source_server_id):
    ec2 = boto3.client('ec2')
    
    # Tag the target instance to allow DRS recovery
    ec2.create_tags(
        Resources=[target_instance_id],
        Tags=[
            {
                'Key': 'AWSDRS',
                'Value': 'AllowLaunchingIntoThisInstance'
            },
            {
                'Key': 'DRS-SourceServer',
                'Value': source_server_id
            }
        ]
    )
    
    return {
        'target_instance_id': target_instance_id,
        'source_server_id': source_server_id,
        'recovery_mode': 'existing_instance'
    }

# Method 2: Configure launch template for new instance creation
def configure_launch_template(source_server_id, launch_settings):
    return drs_client.update_launch_configuration(
        sourceServerID=source_server_id,
        ec2LaunchTemplateID=launch_settings.get('templateId'),
        targetInstanceTypeRightSizingMethod='BASIC',
        launchDisposition='STARTED'
    )
```

### List Recovery Targets

**VMware SRM**:
```http
GET /api/vms
# Filter for placeholder VMs
```

**AWS DRS Equivalent**:
```python
# List instances tagged for DRS recovery
def list_recovery_target_instances():
    ec2 = boto3.client('ec2')
    
    response = ec2.describe_instances(
        Filters=[
            {
                'Name': 'tag:AWSDRS',
                'Values': ['AllowLaunchingIntoThisInstance']
            },
            {
                'Name': 'instance-state-name',
                'Values': ['running', 'stopped']
            }
        ]
    )
    
    recovery_targets = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            # Find associated source server from tags
            source_server_id = None
            for tag in instance.get('Tags', []):
                if tag['Key'] == 'DRS-SourceServer':
                    source_server_id = tag['Value']
                    break
            
            recovery_targets.append({
                'instance_id': instance['InstanceId'],
                'instance_type': instance['InstanceType'],
                'state': instance['State']['Name'],
                'source_server_id': source_server_id,
                'availability_zone': instance['Placement']['AvailabilityZone']
            })
    
    return recovery_targets
```

### Recovery into Existing Instance

**VMware SRM**:
```http
POST /api/recovery-plans/{rp-id}/recovery
{
  "recovery_type": "test",
  "recovery_options": {
    "use_placeholder_vms": true
  }
}
```

**AWS DRS Equivalent**:
```python
# Start recovery into tagged existing instance
def start_recovery_into_existing_instance(source_server_id, target_instance_id):
    # Ensure target instance is properly tagged
    configure_recovery_target_instance(target_instance_id, source_server_id)
    
    # Start recovery - DRS will automatically use tagged instance
    return drs_client.start_recovery(
        sourceServers=[
            {
                'sourceServerID': source_server_id,
                'recoveryInstanceProperties': {
                    'targetInstanceTypeRightSizingMethod': 'BASIC'
                }
            }
        ],
        isDrill=True  # Use drill mode for testing
    )
```

### Remove Recovery Target

**VMware SRM**:
```http
DELETE /api/vms/{placeholder-vm-id}
```

**AWS DRS Equivalent**:
```python
# Remove DRS tags from instance
def remove_recovery_target(instance_id):
    ec2 = boto3.client('ec2')
    
    # Remove DRS-specific tags
    ec2.delete_tags(
        Resources=[instance_id],
        Tags=[
            {'Key': 'AWSDRS'},
            {'Key': 'DRS-SourceServer'}
        ]
    )
    
    return {'instance_id': instance_id, 'status': 'recovery_target_removed'}
```

## Key Differences: Placeholder VMs vs Recovery Instances

| Feature | VMware SRM Placeholder VM | AWS DRS Recovery Instance |
|---------|---------------------------|---------------------------|
| **Pre-provisioning** | Creates placeholder VMs in advance | Tags existing instances or uses launch templates |
| **Resource Allocation** | Reserves compute/storage resources | Uses on-demand EC2 capacity |
| **Network Configuration** | Pre-configured network settings | Configured via launch templates or instance settings |
| **Storage Mapping** | Maps to target datastores | Creates new EBS volumes from snapshots |
| **Customization** | vSphere customization specs | EC2 user data and SSM documents |
| **Cost Model** | Consumes vSphere resources | Pay-per-use EC2 pricing |

### Implementation Notes

1. **AWSDRS Tag Behavior**:
   - Must be applied to stopped or running EC2 instances
   - DRS automatically discovers tagged instances during recovery
   - Instance must be in same AZ as DRS staging area
   - Original instance data is preserved during drill recovery

2. **Recovery Process**:
   - **Drill Mode**: DRS creates temporary recovery instance, preserves original
   - **Recovery Mode**: DRS replaces target instance with recovered data
   - **Failback**: Original source can be restored from AWS snapshots

3. **Best Practices**:
   - Use consistent tagging strategy for recovery targets
   - Document instance-to-server mappings
   - Test recovery procedures regularly
   - Monitor instance capacity and availability

## Compliance and Reporting

### Get Recovery Test History

**VMware SRM**:
```http
GET /api/recovery-plans/{rp-id}/test-history
```

**AWS DRS Equivalent**:
```python
# Query execution history from DynamoDB
def get_execution_history(plan_id):
    return dynamodb.query(
        TableName='ExecutionHistory',
        KeyConditionExpression='PlanId = :plan_id',
        ExpressionAttributeValues={':plan_id': plan_id}
    )
```

### Generate Compliance Report

**VMware SRM**:
```http
POST /api/reports/compliance
{
  "report_type": "rpo_rto_compliance",
  "date_range": {"start_date": "2024-01-01"}
}
```

**AWS DRS Equivalent**:
```python
# Generate custom compliance report
def generate_compliance_report(date_range):
    executions = get_execution_history_by_date(date_range)
    
    return {
        'total_tests': len(executions),
        'successful_tests': len([e for e in executions if e['status'] == 'SUCCESS']),
        'average_rto': calculate_average_rto(executions),
        'rpo_compliance': check_rpo_compliance(executions)
    }
```

## Advanced Orchestration Mapping

### Wave-Based Recovery (Priority Groups)

**VMware SRM**:
```http
# Recovery priority groups in recovery plan
{
  "recovery_priority_groups": [
    {"priority": 1, "name": "Database"},
    {"priority": 2, "name": "Application"},
    {"priority": 3, "name": "Web"}
  ]
}
```

**AWS DRS Equivalent**:
```python
# Step Functions state machine for wave orchestration
def create_wave_orchestration(waves):
    state_machine = {
        "Comment": "DRS Wave-based Recovery",
        "StartAt": "Wave1",
        "States": {}
    }
    
    for i, wave in enumerate(waves, 1):
        state_machine["States"][f"Wave{i}"] = {
            "Type": "Task",
            "Resource": "arn:aws:lambda:region:account:function:drs-orchestration",
            "Parameters": {
                "wave": wave,
                "servers": wave['serverIds']
            },
            "Next": f"Wave{i+1}" if i < len(waves) else "Success"
        }
    
    return state_machine
```

### Custom Recovery Actions

**VMware SRM**:
```http
# Callout commands in recovery plan
{
  "callout_commands": [
    {
      "command": "health-check.sh",
      "timeout": 300,
      "run_on": "recovery_site"
    }
  ]
}
```

**AWS DRS Equivalent**:
```python
# SSM Documents for post-launch actions
def configure_post_launch_actions(server_id, actions):
    ssm_documents = []
    
    for action in actions:
        ssm_documents.append({
            "actionName": action['name'],
            "ssmDocumentName": action['document'],
            "timeoutSeconds": action.get('timeout', 300),
            "mustSucceedForCutover": action.get('required', True),
            "parameters": action.get('parameters', {})
        })
    
    return drs_client.update_launch_configuration(
        sourceServerID=server_id,
        postLaunchActions={
            "deployment": "TEST_AND_CUTOVER",
            "ssmDocuments": ssm_documents
        }
    )
```

## Key Differences and Limitations

### VMware SRM Advantages
- **Native Protection Groups**: Built-in grouping and dependency management
- **Integrated UI**: Complete disaster recovery management interface
- **Site Pairing**: Automatic site-to-site replication management
- **VM Customization**: Advanced network and compute customization options
- **Compliance Reporting**: Built-in compliance and testing reports

### AWS DRS Advantages
- **Serverless Architecture**: No infrastructure to manage
- **Cloud-Native Integration**: Deep integration with AWS services
- **Scalability**: Automatic scaling and pay-per-use pricing
- **Cross-Platform**: Supports physical, virtual, and cloud workloads
- **Advanced Automation**: Integration with AWS Systems Manager and Lambda

### Implementation Gaps
1. **Protection Groups**: Must be implemented using tags or external storage
2. **Recovery Plans**: Require custom orchestration using Step Functions
3. **Wave Dependencies**: Need custom logic for dependency management
4. **UI Integration**: Requires custom web interface development
5. **Compliance Reporting**: Must build custom reporting solutions

## Migration Strategy

### Phase 1: Assessment
1. **Inventory SRM Configuration**: Document existing protection groups and recovery plans
2. **Map Dependencies**: Identify VM dependencies and recovery priorities
3. **Network Planning**: Design AWS network architecture for recovery
4. **Compliance Requirements**: Document RPO/RTO and testing requirements

### Phase 2: Implementation
1. **DRS Setup**: Initialize DRS and configure replication
2. **Custom Orchestration**: Build protection groups and recovery plans using our solution
3. **Automation**: Implement post-launch actions using SSM documents
4. **Testing**: Validate recovery procedures with drill executions

### Phase 3: Migration
1. **Parallel Operation**: Run both SRM and DRS during transition
2. **Gradual Migration**: Move workloads in phases
3. **Validation**: Ensure all functionality is replicated
4. **Cutover**: Complete migration to AWS DRS solution

This mapping guide provides the foundation for understanding how VMware SRM functionality translates to AWS DRS, enabling successful migration and hybrid implementations.