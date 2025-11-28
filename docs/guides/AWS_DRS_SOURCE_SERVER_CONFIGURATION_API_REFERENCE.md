# AWS DRS Source Server Configuration - Complete API Reference

**Document Version**: 1.0  
**Last Updated**: November 27, 2025  
**Purpose**: Complete reference for reading and modifying all DRS source server settings

## Overview

This document covers every AWS DRS API for configuring source servers including launch settings, replication settings, tags, disk configuration, and post-launch actions.

---

## Configuration Categories

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Server Information (Read-Only)                              │
│ 2. Launch Configuration                                        │
│ 3. Replication Configuration                                   │
│ 4. Tags & Metadata                                             │
│ 5. Post-Launch Actions                                         │
│ 6. EC2 Launch Templates                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Server Information (Read-Only)

### API: DescribeSourceServers

**Purpose**: Read all source server properties

**Request**:
```python
import boto3
drs = boto3.client('drs', region_name='us-east-1')

response = drs.describe_source_servers(
    filters={'sourceServerIDs': ['s-1234567890abcdef0']}
)
```

**Response Structure**:
```json
{
  "items": [{
    "sourceServerID": "s-1234567890abcdef0",
    "arn": "arn:aws:drs:us-east-1:123456789012:source-server/s-1234567890abcdef0",
    "tags": {"Environment": "Production"},
    "sourceProperties": {
      "lastUpdatedDateTime": "2025-11-27T10:00:00Z",
      "recommendedInstanceType": "m5.large",
      "identificationHints": {
        "fqdn": "web-server-01.example.com",
        "hostname": "web-server-01",
        "vmWareUuid": "502f1234-5678-90ab-cdef-123456789012"
      },
      "networkInterfaces": [{
        "macAddress": "02:12:34:56:78:90",
        "ips": ["10.0.1.100"],
        "isPrimary": true
      }],
      "disks": [{
        "deviceName": "/dev/sda1",
        "bytes": 107374182400
      }],
      "cpus": [{
        "cores": 2,
        "modelName": "Intel(R) Xeon(R) CPU E5-2686 v4"
      }],
      "ramBytes": 8589934592,
      "os": {
        "fullString": "Ubuntu 20.04.3 LTS"
      }
    },
    "dataReplicationInfo": {
      "dataReplicationState": "CONTINUOUS",
      "lagDuration": "PT30S"
    },
    "lifeCycle": {
      "state": "READY_FOR_RECOVERY"
    }
  }]
}
```

---

## 2. Launch Configuration

### API: GetLaunchConfiguration

**Purpose**: Read current launch settings

**Request**:
```python
response = drs.get_launch_configuration(
    sourceServerID='s-1234567890abcdef0'
)
```

**Response**:
```json
{
  "sourceServerID": "s-1234567890abcdef0",
  "name": "web-server-01-launch-config",
  "ec2LaunchTemplateID": "lt-1234567890abcdef0",
  "launchDisposition": "STARTED",
  "targetInstanceTypeRightSizingMethod": "BASIC",
  "copyPrivateIp": false,
  "copyTags": true,
  "licensing": {
    "osByol": false
  },
  "bootMode": "LEGACY_BIOS"
}
```

### API: UpdateLaunchConfiguration

**Purpose**: Modify launch settings

**Request**:
```python
response = drs.update_launch_configuration(
    sourceServerID='s-1234567890abcdef0',
    name='web-server-01-updated',
    launchDisposition='STARTED',  # STOPPED or STARTED
    targetInstanceTypeRightSizingMethod='BASIC',  # BASIC or NONE
    copyPrivateIp=True,
    copyTags=True,
    licensing={'osByol': False},
    bootMode='UEFI'  # LEGACY_BIOS, UEFI, or USE_DEFAULT
)
```

**Parameters**:
- `launchDisposition`: Instance state after launch
  - `STOPPED`: Launch but keep stopped
  - `STARTED`: Launch and start automatically
- `targetInstanceTypeRightSizingMethod`:
  - `BASIC`: Use recommended instance type
  - `NONE`: Use exact source specifications
- `copyPrivateIp`: Preserve source private IP
- `copyTags`: Copy source server tags to recovery instance
- `bootMode`: Boot mode for recovery instance

---

## 3. Replication Configuration

### API: GetReplicationConfiguration

**Purpose**: Read replication settings

**Request**:
```python
response = drs.get_replication_configuration(
    sourceServerID='s-1234567890abcdef0'
)
```

**Response**:
```json
{
  "sourceServerID": "s-1234567890abcdef0",
  "name": "web-server-01-replication",
  "stagingAreaSubnetId": "subnet-1234567890abcdef0",
  "associateDefaultSecurityGroup": true,
  "securityGroupIDs": ["sg-1234567890abcdef0"],
  "stagingAreaTags": {
    "Environment": "Production",
    "Purpose": "DRS-Staging"
  },
  "replicationServerInstanceType": "t3.small",
  "useDedicatedReplicationServer": false,
  "defaultLargeStagingDiskType": "GP3",
  "replicatedDisks": [{
    "deviceName": "/dev/sda1",
    "iops": 3000,
    "isBootDisk": true,
    "stagingDiskType": "GP3",
    "throughput": 125
  }],
  "createPublicIP": false,
  "dataPlaneRouting": "PRIVATE_IP",
  "ebsEncryption": "DEFAULT",
  "ebsEncryptionKeyArn": "arn:aws:kms:us-east-1:123456789012:key/12345678",
  "bandwidthThrottling": 0,
  "pitPolicy": [{
    "interval": 10,
    "retentionDuration": 60,
    "units": "MINUTE",
    "enabled": true,
    "ruleID": 1
  }]
}
```

### API: UpdateReplicationConfiguration

**Purpose**: Modify replication settings

**Request**:
```python
response = drs.update_replication_configuration(
    sourceServerID='s-1234567890abcdef0',
    stagingAreaSubnetId='subnet-1234567890abcdef0',
    replicationServerInstanceType='t3.medium',
    defaultLargeStagingDiskType='GP3',
    replicatedDisks=[{
        'deviceName': '/dev/sda1',
        'iops': 3000,
        'isBootDisk': True,
        'stagingDiskType': 'GP3',
        'throughput': 125
    }],
    dataPlaneRouting='PRIVATE_IP',
    ebsEncryption='CUSTOM',
    ebsEncryptionKeyArn='arn:aws:kms:us-east-1:123456789012:key/12345678',
    bandwidthThrottling=100,  # Mbps (0 = unlimited)
    pitPolicy=[{
        'interval': 10,
        'retentionDuration': 60,
        'units': 'MINUTE',
        'enabled': True,
        'ruleID': 1
    }]
)
```

**Key Parameters**:
- `stagingAreaSubnetId`: Subnet for replication servers
- `replicationServerInstanceType`: Instance type for replication server
- `useDedicatedReplicationServer`: Dedicated vs shared replication server
- `defaultLargeStagingDiskType`: `GP2`, `GP3`, `ST1`, `SC1`
- `dataPlaneRouting`: `PRIVATE_IP` or `PUBLIC_IP`
- `ebsEncryption`: `DEFAULT`, `CUSTOM`, or `NONE`
- `bandwidthThrottling`: Limit replication bandwidth (Mbps)
- `pitPolicy`: Point-in-time snapshot retention rules

---

## 4. Tags & Metadata

### API: TagResource

**Purpose**: Add/update tags on source server

**Request**:
```python
response = drs.tag_resource(
    resourceArn='arn:aws:drs:us-east-1:123456789012:source-server/s-1234567890abcdef0',
    tags={
        'Environment': 'Production',
        'Application': 'WebApp',
        'Owner': 'IT-Team',
        'CostCenter': 'CC-1234',
        'ProtectionGroup': 'WebServers'
    }
)
```

### API: UntagResource

**Purpose**: Remove tags from source server

**Request**:
```python
response = drs.untag_resource(
    resourceArn='arn:aws:drs:us-east-1:123456789012:source-server/s-1234567890abcdef0',
    tagKeys=['Owner', 'CostCenter']
)
```

### API: ListTagsForResource

**Purpose**: Read current tags

**Request**:
```python
response = drs.list_tags_for_resource(
    resourceArn='arn:aws:drs:us-east-1:123456789012:source-server/s-1234567890abcdef0'
)
```

**Response**:
```json
{
  "tags": {
    "Environment": "Production",
    "Application": "WebApp",
    "ProtectionGroup": "WebServers"
  }
}
```

---

## 5. Post-Launch Actions

### API: UpdateLaunchConfiguration (post-launch)

**Purpose**: Configure post-launch actions

**Request**:
```python
response = drs.update_launch_configuration(
    sourceServerID='s-1234567890abcdef0',
    postLaunchActions={
        'deployment': 'TEST_AND_CUTOVER',  # or 'CUTOVER_ONLY'
        's3LogBucket': 'drs-logs-bucket',
        's3OutputKeyPrefix': 'post-launch-logs/',
        'cloudWatchLogGroupName': '/aws/drs/post-launch',
        'ssmDocuments': [
            {
                'actionName': 'health-check',
                'ssmDocumentName': 'AWS-RunShellScript',
                'timeoutSeconds': 300,
                'mustSucceedForCutover': True,
                'parameters': {
                    'commands': [
                        'systemctl status nginx',
                        'curl -f http://localhost/health'
                    ]
                }
            },
            {
                'actionName': 'application-startup',
                'ssmDocumentName': 'Custom-AppStartup',
                'timeoutSeconds': 600,
                'mustSucceedForCutover': True,
                'parameters': {
                    'ServiceName': 'myapp'
                }
            }
        ]
    }
)
```

**Parameters**:
- `deployment`:
  - `TEST_AND_CUTOVER`: Run actions before marking ready
  - `CUTOVER_ONLY`: Skip testing phase
- `mustSucceedForCutover`: Block cutover if action fails
- `timeoutSeconds`: Maximum execution time per action

**Common SSM Documents**:
- `AWS-RunShellScript`: Execute shell commands
- `AWS-RunPowerShellScript`: Execute PowerShell (Windows)
- `AWS-ConfigureAWSPackage`: Install AWS packages
- Custom documents: Your own SSM documents

---

## 6. EC2 Launch Templates

### API: CreateLaunchConfigurationTemplate

**Purpose**: Create reusable launch template

**Request**:
```python
response = drs.create_launch_configuration_template(
    launchDisposition='STARTED',
    targetInstanceTypeRightSizingMethod='BASIC',
    copyPrivateIp=False,
    copyTags=True,
    postLaunchActions={
        'deployment': 'TEST_AND_CUTOVER',
        's3LogBucket': 'drs-logs-bucket',
        'cloudWatchLogGroupName': '/aws/drs/post-launch',
        'ssmDocuments': [{
            'actionName': 'standard-health-check',
            'ssmDocumentName': 'AWS-RunShellScript',
            'timeoutSeconds': 300,
            'mustSucceedForCutover': True,
            'parameters': {
                'commands': ['echo "Health check passed"']
            }
        }]
    },
    tags={
        'Name': 'Standard-Web-Server-Template',
        'Type': 'Production'
    }
)
```

**Response**:
```json
{
  "launchConfigurationTemplate": {
    "launchConfigurationTemplateID": "lct-1234567890abcdef0",
    "arn": "arn:aws:drs:us-east-1:123456789012:launch-configuration-template/lct-1234567890abcdef0",
    "launchDisposition": "STARTED",
    "tags": {
      "Name": "Standard-Web-Server-Template"
    }
  }
}
```

### API: UpdateLaunchConfigurationTemplate

**Purpose**: Modify existing template

**Request**:
```python
response = drs.update_launch_configuration_template(
    launchConfigurationTemplateID='lct-1234567890abcdef0',
    launchDisposition='STARTED',
    copyPrivateIp=True
)
```

### API: DeleteLaunchConfigurationTemplate

**Purpose**: Remove template

**Request**:
```python
response = drs.delete_launch_configuration_template(
    launchConfigurationTemplateID='lct-1234567890abcdef0'
)
```

---

## Complete Configuration Workflow

### Scenario: Configure New Source Server

```python
import boto3

drs = boto3.client('drs', region_name='us-east-1')
server_id = 's-1234567890abcdef0'

# Step 1: Read current configuration
server_info = drs.describe_source_servers(
    filters={'sourceServerIDs': [server_id]}
)['items'][0]

# Step 2: Configure replication
drs.update_replication_configuration(
    sourceServerID=server_id,
    stagingAreaSubnetId='subnet-1234567890abcdef0',
    replicationServerInstanceType='t3.small',
    defaultLargeStagingDiskType='GP3',
    ebsEncryption='DEFAULT',
    dataPlaneRouting='PRIVATE_IP',
    bandwidthThrottling=0
)

# Step 3: Configure launch settings
drs.update_launch_configuration(
    sourceServerID=server_id,
    launchDisposition='STARTED',
    targetInstanceTypeRightSizingMethod='BASIC',
    copyPrivateIp=False,
    copyTags=True,
    bootMode='UEFI',
    postLaunchActions={
        'deployment': 'TEST_AND_CUTOVER',
        's3LogBucket': 'drs-logs-bucket',
        'cloudWatchLogGroupName': '/aws/drs/post-launch',
        'ssmDocuments': [{
            'actionName': 'health-check',
            'ssmDocumentName': 'AWS-RunShellScript',
            'timeoutSeconds': 300,
            'mustSucceedForCutover': True,
            'parameters': {
                'commands': ['systemctl status nginx']
            }
        }]
    }
)

# Step 4: Add tags
drs.tag_resource(
    resourceArn=f'arn:aws:drs:us-east-1:123456789012:source-server/{server_id}',
    tags={
        'Environment': 'Production',
        'Application': 'WebApp',
        'ProtectionGroup': 'WebServers'
    }
)

print("✅ Configuration complete")
```

---

## Configuration Best Practices

### 1. Replication Settings
```python
# Production: High performance, encrypted
{
    'defaultLargeStagingDiskType': 'GP3',
    'ebsEncryption': 'CUSTOM',
    'dataPlaneRouting': 'PRIVATE_IP',
    'bandwidthThrottling': 0
}

# Cost-optimized: Lower performance
{
    'defaultLargeStagingDiskType': 'ST1',
    'ebsEncryption': 'DEFAULT',
    'bandwidthThrottling': 50  # Limit to 50 Mbps
}
```

### 2. Launch Configuration
```python
# Production recovery
{
    'launchDisposition': 'STARTED',
    'targetInstanceTypeRightSizingMethod': 'BASIC',
    'copyPrivateIp': True,  # Preserve IP
    'copyTags': True
}

# Testing/drill
{
    'launchDisposition': 'STOPPED',  # Launch but don't start
    'targetInstanceTypeRightSizingMethod': 'NONE',
    'copyPrivateIp': False
}
```

### 3. Post-Launch Actions
```python
# Critical application
{
    'deployment': 'TEST_AND_CUTOVER',
    'ssmDocuments': [{
        'actionName': 'health-check',
        'mustSucceedForCutover': True,  # Block if fails
        'timeoutSeconds': 300
    }]
}

# Non-critical
{
    'deployment': 'CUTOVER_ONLY',  # Skip testing
    'ssmDocuments': []
}
```

---

## Summary

**Configuration APIs**:
1. DescribeSourceServers - Read server info
2. GetLaunchConfiguration - Read launch settings
3. UpdateLaunchConfiguration - Modify launch settings
4. GetReplicationConfiguration - Read replication settings
5. UpdateReplicationConfiguration - Modify replication settings
6. TagResource - Add tags
7. UntagResource - Remove tags
8. ListTagsForResource - Read tags
9. CreateLaunchConfigurationTemplate - Create template
10. UpdateLaunchConfigurationTemplate - Modify template
11. DeleteLaunchConfigurationTemplate - Delete template

**Key Configuration Areas**:
- Launch disposition (STARTED/STOPPED)
- Instance type right-sizing
- Network settings (IP, security groups)
- Replication performance (disk types, bandwidth)
- Encryption (default or custom KMS)
- Point-in-time snapshots
- Post-launch automation (SSM)
- Tags and metadata
