# DRS Launch Configuration Reference

**Version**: 2.1 (January 1, 2026)  
**Purpose**: Comprehensive guide to DRS launch template configuration and AWS sample tools  
**Scope**: Launch settings, EC2 templates, and configuration management

---

## Overview

AWS DRS uses EC2 Launch Templates to define how recovery instances are launched. This document consolidates analysis from AWS sample tools and provides definitive guidance on which settings can be safely modified.

## DRS Launch Configuration vs EC2 Launch Template

DRS provides two levels of launch configuration:

1. **DRS Launch Configuration** - High-level settings managed by DRS API
2. **EC2 Launch Template** - Low-level EC2 settings (can be edited by customers)

**Important**: AWS DRS creates launch templates that customers can modify directly in the EC2 console. DRS will not override customer changes to launch templates.

## DRS Launch Configuration Settings (Safe to Edit)

These settings are managed through DRS APIs and are safe to modify:

### Basic Settings
| Setting | API Field | Values | Description |
|---------|-----------|---------|-------------|
| **Launch Disposition** | `launchDisposition` | `STOPPED`, `STARTED` | Whether instance starts automatically after recovery |
| **Copy Private IP** | `copyPrivateIp` | `true`, `false` | Copy source server's private IP to recovery instance |
| **Copy Tags** | `copyTags` | `true`, `false` | Copy source server tags to recovery instance |
| **Configuration Name** | `name` | String (0-128 chars) | Human-readable name for the configuration |

### Instance Type Settings
| Setting | API Field | Values | Description |
|---------|-----------|---------|-------------|
| **Right Sizing Method** | `targetInstanceTypeRightSizingMethod` | `NONE`, `BASIC`, `IN_AWS` | How DRS selects instance type |

- `NONE`: Use exact instance type from source
- `BASIC`: DRS recommends based on CPU/RAM
- `IN_AWS`: AWS recommends optimal instance type

### Licensing Settings
| Setting | API Field | Values | Description |
|---------|-----------|---------|-------------|
| **BYOL (Bring Your Own License)** | `licensing.osByol` | `true`, `false` | Use existing OS license vs AWS-provided |

### Post-Launch Actions
| Setting | API Field | Values | Description |
|---------|-----------|---------|-------------|
| **Post-Launch Enabled** | `postLaunchEnabled` | `true`, `false` | Execute post-launch actions after recovery |

### Launch Into Existing Instance
| Setting | API Field | Values | Description |
|---------|-----------|---------|-------------|
| **Launch Into Instance ID** | `launchIntoInstanceProperties.launchIntoEC2InstanceID` | EC2 Instance ID | Launch into existing instance instead of creating new |

## AWS Configuration Synchronizer Analysis

### Official AWS Sample Tool

**Source**: [drs-configuration-synchronizer](https://github.com/aws-samples/drs-tools/tree/main/drs-configuration-synchronizer)

This tool demonstrates AWS's enterprise approach for managing DRS configurations at scale using Infrastructure as Code principles.

### Allowed EC2 Launch Template Settings (AWS Supported)

The Configuration Synchronizer explicitly lists **allowed** and **ignored** EC2 launch template settings:

#### ✅ Allowed Settings (AWS Officially Supports)
| Setting | Description | Use Case |
|---------|-------------|----------|
| **IamInstanceProfile** | Instance IAM role | Application permissions |
| **InstanceType** | EC2 instance type | Performance/cost optimization |
| **Monitoring** | CloudWatch detailed monitoring | Observability |
| **DisableApiTermination** | Termination protection | Production safety |
| **InstanceInitiatedShutdownBehavior** | Shutdown behavior | Instance lifecycle |
| **TagSpecifications** | Instance and volume tags | Organization/billing |
| **CreditSpecification** | T-series CPU credits | Burstable performance |
| **CpuOptions** | CPU configuration | Performance tuning |
| **CapacityReservationSpecification** | Reserved capacity | Cost optimization |
| **LicenseSpecifications** | License tracking | Compliance |
| **MetadataOptions** | Instance metadata settings | Security hardening |
| **PrivateDnsNameOptions** | DNS configuration | Networking |
| **MaintenanceOptions** | Maintenance settings | Availability |
| **DisableApiStop** | Stop protection | Production safety |
| **SecurityGroupIds** | Security groups | Network security |
| **NetworkInterfaces** | Network configuration | Advanced networking |

#### ❌ Ignored Settings (AWS Managed by DRS)
| Setting | Reason AWS Ignores |
|---------|-------------------|
| **BlockDeviceMappings** | DRS manages disk mappings from source |
| **EbsOptimized** | DRS determines based on instance type |
| **ElasticGpuSpecifications** | Not applicable to recovery |
| **ElasticInferenceAccelerators** | Not applicable to recovery |
| **EnclaveOptions** | Security feature not for recovery |
| **HibernationOptions** | Not applicable to recovery |
| **ImageId** | DRS creates recovery-specific AMIs |
| **InstanceRequirements** | DRS handles instance selection |
| **KernelId** | Part of AMI managed by DRS |
| **KeyName** | Handled separately by DRS |
| **RamDiskId** | Part of AMI managed by DRS |
| **SecurityGroups** | Use SecurityGroupIds instead |
| **UserData** | DRS may inject recovery scripts |

## AWS Template Manager Analysis

### Official AWS Sample Tool

**Source**: [drs-template-manager](https://github.com/aws-samples/drs-tools/tree/main/drs-template-manager)

This tool demonstrates AWS's recommended approach for batch editing DRS launch templates.

### Officially Supported Modifications

Based on the AWS sample tool, these launch template fields are **officially supported** for customer modification:

#### Safe to Edit (Per AWS Sample)
| Field | Example Value | Purpose |
|-------|---------------|---------|
| **InstanceType** | `"t3.small"` | Override DRS instance type recommendations |
| **KeyName** | `"my-keypair"` | Add SSH key for server access |
| **SecurityGroupIds** | `["sg-123", "sg-456"]` | Add application security groups |
| **IamInstanceProfile.Name** | `"MyCustomRole"` | Add application IAM permissions |
| **TagSpecifications** | Custom tags | Organization and cost allocation |
| **EbsOptimized** | `true/false` | EBS optimization setting |
| **Monitoring** | `{"Enabled": true}` | CloudWatch detailed monitoring |
| **BlockDeviceMappings.VolumeType** | `"gp3"`, `"io1"` | Change EBS volume types |
| **BlockDeviceMappings.VolumeSize** | `100` | Increase volume sizes |
| **BlockDeviceMappings.Iops** | `3000` | Set IOPS for io1/io2 volumes |
| **NetworkInterfaces.SubnetId** | `"subnet-123"` | Change recovery subnet |

#### Fields AWS Sets to null (DRS Manages)
| Field | Value in Sample | Reason |
|-------|-----------------|--------|
| **ImageId** | `null` | DRS creates recovery AMIs |
| **UserData** | `null` | DRS may inject recovery scripts |
| **NetworkInterfaces.Groups** | `null` | DRS manages primary security groups |
| **NetworkInterfaces.PrivateIpAddress** | `null` | DRS manages IP assignment |

### AWS Sample Template Structure

The sample template shows AWS's recommended approach:

```json
{
  "InstanceType": "t3.small",
  "KeyName": null,
  "ImageId": null,
  "IamInstanceProfile": {
    "Name": "AWSElasticDisasterRecoveryRecoveryInstanceRole"
  },
  "BlockDeviceMappings": [
    {
      "DeviceName": "/dev/sda1",
      "Ebs": {
        "VolumeType": "gp3",
        "VolumeSize": 100,
        "Iops": 3000,
        "DeleteOnTermination": true,
        "Encrypted": true
      }
    }
  ],
  "NetworkInterfaces": [
    {
      "DeviceIndex": 0,
      "SubnetId": "subnet-12345678",
      "Groups": ["sg-12345678"],
      "AssociatePublicIpAddress": false
    }
  ],
  "TagSpecifications": [
    {
      "ResourceType": "instance",
      "Tags": [
        {
          "Key": "Name",
          "Value": "Recovery-Instance"
        },
        {
          "Key": "Environment",
          "Value": "DR"
        }
      ]
    }
  ],
  "Monitoring": {
    "Enabled": true
  },
  "EbsOptimized": true,
  "DisableApiTermination": false
}
```

## Best Practices for Launch Template Modification

### 1. Safe Modifications
- **Instance Type**: Change for performance or cost optimization
- **Security Groups**: Add application-specific security groups
- **IAM Roles**: Add application permissions
- **Tags**: Add organizational and billing tags
- **Monitoring**: Enable detailed CloudWatch monitoring
- **EBS Settings**: Optimize volume types and sizes

### 2. Avoid These Modifications
- **ImageId**: DRS manages AMI creation
- **UserData**: May conflict with DRS recovery scripts
- **Primary Network Interface**: DRS manages networking
- **Block Device Mappings**: Only modify volume properties, not mappings

### 3. Testing Recommendations
- Test launch template changes in drill mode first
- Validate instance launches successfully
- Verify application functionality post-recovery
- Document all customizations for maintenance

## Configuration Management Patterns

### 1. Infrastructure as Code Approach

Use the Configuration Synchronizer pattern for enterprise environments:

```python
# Example configuration template
launch_template_config = {
    "InstanceType": "m5.large",
    "IamInstanceProfile": {
        "Name": "MyAppRecoveryRole"
    },
    "SecurityGroupIds": [
        "sg-app-tier",
        "sg-monitoring"
    ],
    "TagSpecifications": [
        {
            "ResourceType": "instance",
            "Tags": [
                {"Key": "Application", "Value": "MyApp"},
                {"Key": "Environment", "Value": "DR"},
                {"Key": "CostCenter", "Value": "IT-DR"}
            ]
        }
    ],
    "Monitoring": {"Enabled": True},
    "EbsOptimized": True
}
```

### 2. Batch Template Management

Use the Template Manager pattern for bulk updates:

```python
# Example batch update
def update_launch_templates(server_list, template_updates):
    for server in server_list:
        template_id = get_launch_template_id(server['sourceServerID'])
        update_launch_template(template_id, template_updates)
        
# Apply security group updates to all servers
security_updates = {
    "SecurityGroupIds": ["sg-new-security-group"]
}
update_launch_templates(protection_group_servers, security_updates)
```

### 3. Validation and Testing

```python
# Validate template changes
def validate_launch_template(template_id):
    template = describe_launch_template(template_id)
    
    # Check for DRS-managed fields
    if template.get('ImageId'):
        raise ValueError("ImageId should not be set - DRS manages AMIs")
    
    # Validate instance type availability
    if not is_instance_type_available(template['InstanceType']):
        raise ValueError(f"Instance type {template['InstanceType']} not available")
    
    return True
```

## Troubleshooting Launch Template Issues

### Common Issues

#### 1. Launch Template Version Conflicts
**Symptom**: DRS creates new template versions unexpectedly
**Cause**: Conflicting settings between DRS and customer modifications
**Solution**: Use only supported fields from AWS sample tools

#### 2. Instance Launch Failures
**Symptom**: Recovery instances fail to launch
**Cause**: Invalid launch template configuration
**Solution**: Validate template against AWS samples before deployment

#### 3. Network Configuration Issues
**Symptom**: Instances launch in wrong subnet or with wrong security groups
**Cause**: Incorrect NetworkInterfaces configuration
**Solution**: Use SecurityGroupIds at root level, not in NetworkInterfaces

### Validation Commands

```bash
# Describe launch template
AWS_PAGER="" aws ec2 describe-launch-template-versions \
  --launch-template-id lt-12345678 \
  --versions '$Latest'

# Test instance launch (dry run)
AWS_PAGER="" aws ec2 run-instances \
  --launch-template LaunchTemplateId=lt-12345678,Version='$Latest' \
  --min-count 1 --max-count 1 \
  --dry-run

# Validate security groups
AWS_PAGER="" aws ec2 describe-security-groups \
  --group-ids sg-12345678
```

This comprehensive reference consolidates all DRS launch configuration knowledge from official AWS sample tools and provides definitive guidance for safe template modifications.