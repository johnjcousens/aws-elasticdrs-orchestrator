# DRS AllowLaunchingIntoThisInstance Feature Research & Implementation

**Version**: 1.0  
**Date**: January 8, 2026  
**Author**: DRS Engineering Team  
**Status**: Research Complete - Implementation Ready  

---

## Executive Summary

The `AWSDRS=AllowLaunchingIntoThisInstance` feature enables AWS DRS to launch recovery instances into **pre-existing EC2 instances** instead of creating new ones. This is critical for scenarios where:

- **Pre-provisioned DR infrastructure** exists in the target region
- **IP address preservation** is required (instances keep their existing private IPs)
- **Cost optimization** through reusing stopped instances instead of creating new ones
- **Compliance requirements** mandate specific instance configurations

## Feature Overview

### What It Does

The `AWSDRS=AllowLaunchingIntoThisInstance` tag tells DRS to **launch into an existing EC2 instance** rather than creating a new one. When DRS performs recovery:

1. **Finds the tagged instance** in the target region
2. **Stops the instance** if it's running
3. **Replaces the EBS volumes** with recovery volumes from DRS
4. **Starts the instance** with the recovered data
5. **Preserves the instance metadata** (private IP, security groups, etc.)

### Key Benefits

- **IP Address Preservation**: Instance keeps its existing private IP address
- **Network Configuration**: Security groups, subnets, and network interfaces remain unchanged
- **Cost Efficiency**: Reuses existing instances instead of creating new ones
- **Faster Recovery**: No instance launch time, just volume replacement
- **Compliance**: Maintains pre-approved instance configurations

## Research Findings

### 1. Archive Implementation Analysis

From the enterprise DR orchestration archive (`archive/dr-orchestration-artifacts/src/modulefactory/modules/drs.py`), the pattern is:

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

### 2. DRS API Integration Points

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

### 3. Current Solution Integration Points

The current DRS solution has these relevant components:

**Frontend Components**:
- `LaunchConfigSection.tsx` - UI for launch settings
- Protection Group creation/editing forms

**Backend APIs**:
- `lambda/api-handler/index.py` - REST API endpoints
- Launch configuration management functions
- DRS integration functions

**Database Schema**:
- Protection Groups table with `LaunchConfig` field
- Support for hierarchical configuration inheritance

## Implementation Plan

### Phase 1: Core API Support (Week 1-2)

**1.1 Extend Launch Configuration Schema**

Add pre-provisioned instance support to Protection Group launch configuration:

```python
# In lambda/api-handler/index.py - extend LaunchConfig validation
def validate_launch_config(launch_config: Dict) -> Dict:
    """Validate launch configuration including pre-provisioned instance support."""
    
    # Existing validation...
    
    # NEW: Pre-provisioned instance validation
    if 'PreProvisionedInstance' in launch_config:
        pre_prov = launch_config['PreProvisionedInstance']
        
        if 'enabled' in pre_prov and pre_prov['enabled']:
            # Validate required fields for pre-provisioned mode
            if not pre_prov.get('targetInstanceId') and not pre_prov.get('nameTagMatching'):
                return {
                    'valid': False,
                    'error': 'Pre-provisioned mode requires either targetInstanceId or nameTagMatching'
                }
            
            # Validate instance exists and has correct tag
            if pre_prov.get('targetInstanceId'):
                validation_result = validate_target_instance(
                    pre_prov['targetInstanceId'],
                    launch_config.get('region', 'us-east-1')
                )
                if not validation_result['valid']:
                    return validation_result
    
    return {'valid': True}

def validate_target_instance(instance_id: str, region: str) -> Dict:
    """Validate target instance has AWSDRS=AllowLaunchingIntoThisInstance tag."""
    try:
        ec2_client = boto3.client('ec2', region_name=region)
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        
        if not response.get('Reservations'):
            return {
                'valid': False,
                'error': f'Instance {instance_id} not found in region {region}'
            }
        
        instance = response['Reservations'][0]['Instances'][0]
        tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
        
        if tags.get('AWSDRS') != 'AllowLaunchingIntoThisInstance':
            return {
                'valid': False,
                'error': f'Instance {instance_id} missing required tag AWSDRS=AllowLaunchingIntoThisInstance'
            }
        
        return {
            'valid': True,
            'instanceState': instance.get('State', {}).get('Name'),
            'instanceType': instance.get('InstanceType'),
            'privateIp': instance.get('PrivateIpAddress')
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': f'Error validating instance: {str(e)}'
        }
```

**1.2 Add Pre-Provisioned Instance Discovery API**

```python
# New API endpoint: GET /api/v1/drs/pre-provisioned-instances
def get_pre_provisioned_instances(region: str, name_pattern: str = None) -> Dict:
    """Find EC2 instances tagged for DRS pre-provisioned recovery."""
    try:
        ec2_client = boto3.client('ec2', region_name=region)
        
        filters = [
            {
                'Name': 'tag:AWSDRS',
                'Values': ['AllowLaunchingIntoThisInstance']
            },
            {
                'Name': 'instance-state-name',
                'Values': ['running', 'stopped']  # Exclude terminated
            }
        ]
        
        # Optional name pattern filter
        if name_pattern:
            filters.append({
                'Name': 'tag:Name',
                'Values': [f'*{name_pattern}*']
            })
        
        response = ec2_client.describe_instances(Filters=filters)
        
        instances = []
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                
                instances.append({
                    'instanceId': instance.get('InstanceId'),
                    'name': tags.get('Name', ''),
                    'instanceType': instance.get('InstanceType'),
                    'state': instance.get('State', {}).get('Name'),
                    'privateIp': instance.get('PrivateIpAddress'),
                    'availabilityZone': instance.get('Placement', {}).get('AvailabilityZone'),
                    'launchTime': instance.get('LaunchTime').isoformat() if instance.get('LaunchTime') else None,
                    'tags': tags
                })
        
        return {
            'instances': instances,
            'count': len(instances),
            'region': region
        }
        
    except Exception as e:
        raise Exception(f'Error discovering pre-provisioned instances: {str(e)}')
```

### Phase 2: Launch Configuration Application (Week 2-3)

**2.1 Extend apply_launch_config_to_servers Function**

```python
# In lambda/api-handler/index.py - extend existing function
def apply_launch_config_to_servers(
    server_ids: List[str],
    launch_config: Dict,
    region: str,
    protection_group_id: str = None,
    protection_group_name: str = None
) -> Dict:
    """Apply launch configuration to DRS source servers with pre-provisioned support."""
    
    results = []
    
    for server_id in server_ids:
        try:
            # Get current DRS launch configuration
            drs_client = boto3.client('drs', region_name=region)
            current_config = drs_client.get_launch_configuration(sourceServerID=server_id)
            
            # Build updated configuration
            updated_config = build_drs_launch_config(launch_config, current_config, server_id, region)
            
            # Apply configuration to DRS
            drs_client.update_launch_configuration(
                sourceServerID=server_id,
                **updated_config
            )
            
            results.append({
                'serverId': server_id,
                'status': 'success',
                'appliedConfig': updated_config
            })
            
        except Exception as e:
            results.append({
                'serverId': server_id,
                'status': 'failed',
                'error': str(e)
            })
    
    return {
        'total': len(server_ids),
        'successful': len([r for r in results if r['status'] == 'success']),
        'failed': len([r for r in results if r['status'] == 'failed']),
        'results': results
    }

def build_drs_launch_config(launch_config: Dict, current_config: Dict, server_id: str, region: str) -> Dict:
    """Build DRS launch configuration with pre-provisioned instance support."""
    
    updated_config = {}
    
    # Handle pre-provisioned instance configuration
    if launch_config.get('PreProvisionedInstance', {}).get('enabled'):
        pre_prov = launch_config['PreProvisionedInstance']
        
        if pre_prov.get('targetInstanceId'):
            # Explicit instance ID specified
            updated_config['launchIntoInstanceProperties'] = {
                'launchIntoEC2InstanceID': pre_prov['targetInstanceId']
            }
        elif pre_prov.get('nameTagMatching'):
            # Find instance by name tag matching
            target_instance = find_matching_pre_provisioned_instance(server_id, region)
            if target_instance:
                updated_config['launchIntoInstanceProperties'] = {
                    'launchIntoEC2InstanceID': target_instance['instanceId']
                }
            else:
                raise Exception(f'No matching pre-provisioned instance found for server {server_id}')
        
        # Pre-provisioned instances should use existing configuration
        updated_config['targetInstanceTypeRightSizingMethod'] = 'NONE'
        updated_config['copyPrivateIp'] = False  # Keep existing IP
        
    else:
        # Standard launch configuration (existing logic)
        if 'TargetInstanceTypeRightSizingMethod' in launch_config:
            updated_config['targetInstanceTypeRightSizingMethod'] = launch_config['TargetInstanceTypeRightSizingMethod']
        
        if 'CopyPrivateIp' in launch_config:
            updated_config['copyPrivateIp'] = launch_config['CopyPrivateIp']
    
    # Common settings
    if 'CopyTags' in launch_config:
        updated_config['copyTags'] = launch_config['CopyTags']
    
    if 'LaunchDisposition' in launch_config:
        updated_config['launchDisposition'] = launch_config['LaunchDisposition']
    
    if 'Licensing' in launch_config and 'osByol' in launch_config['Licensing']:
        updated_config['licensing'] = {
            'osByol': launch_config['Licensing']['osByol']
        }
    
    return updated_config

def find_matching_pre_provisioned_instance(server_id: str, region: str) -> Optional[Dict]:
    """Find pre-provisioned instance matching source server by name/hostname."""
    try:
        # Get source server details
        drs_client = boto3.client('drs', region_name=region)
        server_response = drs_client.describe_source_servers(
            filters={'sourceServerIDs': [server_id]}
        )
        
        if not server_response.get('items'):
            return None
        
        server = server_response['items'][0]
        hostname = server.get('sourceProperties', {}).get('identificationHints', {}).get('hostname', '')
        
        if not hostname:
            return None
        
        # Find matching pre-provisioned instance
        ec2_client = boto3.client('ec2', region_name=region)
        response = ec2_client.describe_instances(
            Filters=[
                {
                    'Name': 'tag:Name',
                    'Values': [hostname]
                },
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
        
        if response.get('Reservations') and response['Reservations'][0].get('Instances'):
            instance = response['Reservations'][0]['Instances'][0]
            return {
                'instanceId': instance.get('InstanceId'),
                'name': next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), ''),
                'state': instance.get('State', {}).get('Name'),
                'privateIp': instance.get('PrivateIpAddress')
            }
        
        return None
        
    except Exception as e:
        print(f'Error finding matching pre-provisioned instance for {server_id}: {e}')
        return None
```

### Phase 3: Frontend Integration (Week 3-4)

**3.1 Extend LaunchConfigSection Component**

```typescript
// In frontend/src/components/LaunchConfigSection.tsx
interface LaunchConfig {
  // Existing fields...
  PreProvisionedInstance?: {
    enabled: boolean;
    targetInstanceId?: string;
    nameTagMatching?: boolean;
    requireNameTagMatching?: boolean;
  };
}

// Add to LaunchConfigSection component
const [preProvisionedInstances, setPreProvisionedInstances] = useState<PreProvisionedInstance[]>([]);
const [loadingInstances, setLoadingInstances] = useState(false);

// Load pre-provisioned instances when region changes
const loadPreProvisionedInstances = useCallback(async () => {
  if (!region) return;
  
  setLoadingInstances(true);
  try {
    const instances = await apiClient.getPreProvisionedInstances(region);
    setPreProvisionedInstances(instances);
  } catch (err) {
    console.error('Error loading pre-provisioned instances:', err);
  } finally {
    setLoadingInstances(false);
  }
}, [region]);

// Add to JSX
<ExpandableSection
  variant="container"
  headerText="Pre-Provisioned Instance Recovery"
  headerDescription="Launch into existing EC2 instances instead of creating new ones"
>
  <SpaceBetween direction="vertical" size="m">
    <Checkbox
      checked={launchConfig.PreProvisionedInstance?.enabled || false}
      onChange={({ detail }) => 
        updateConfig('PreProvisionedInstance', {
          ...launchConfig.PreProvisionedInstance,
          enabled: detail.checked
        })
      }
      disabled={disabled}
    >
      Enable pre-provisioned instance recovery
    </Checkbox>

    {launchConfig.PreProvisionedInstance?.enabled && (
      <>
        <FormField
          label="Target Instance Selection"
          description="Choose how to select the target instance for recovery"
        >
          <RadioGroup
            value={launchConfig.PreProvisionedInstance?.nameTagMatching ? 'nameTag' : 'explicit'}
            onChange={({ detail }) => {
              const useNameTag = detail.value === 'nameTag';
              updateConfig('PreProvisionedInstance', {
                ...launchConfig.PreProvisionedInstance,
                nameTagMatching: useNameTag,
                targetInstanceId: useNameTag ? undefined : launchConfig.PreProvisionedInstance?.targetInstanceId
              });
            }}
            items={[
              {
                value: 'nameTag',
                label: 'Automatic by Name tag matching',
                description: 'Find instance with matching Name tag and AWSDRS=AllowLaunchingIntoThisInstance'
              },
              {
                value: 'explicit',
                label: 'Explicit instance selection',
                description: 'Manually select specific instance ID'
              }
            ]}
          />
        </FormField>

        {!launchConfig.PreProvisionedInstance?.nameTagMatching && (
          <FormField
            label="Target Instance"
            description="Select the pre-provisioned instance to launch into"
          >
            <Select
              selectedOption={
                preProvisionedInstances.find(i => 
                  i.instanceId === launchConfig.PreProvisionedInstance?.targetInstanceId
                ) ? {
                  value: launchConfig.PreProvisionedInstance.targetInstanceId,
                  label: `${preProvisionedInstances.find(i => 
                    i.instanceId === launchConfig.PreProvisionedInstance?.targetInstanceId
                  )?.name} (${launchConfig.PreProvisionedInstance.targetInstanceId})`
                } : null
              }
              onChange={({ detail }) =>
                updateConfig('PreProvisionedInstance', {
                  ...launchConfig.PreProvisionedInstance,
                  targetInstanceId: detail.selectedOption?.value
                })
              }
              options={preProvisionedInstances.map(instance => ({
                value: instance.instanceId,
                label: `${instance.name} (${instance.instanceId})`,
                description: `${instance.instanceType} - ${instance.state} - ${instance.privateIp}`
              }))}
              placeholder="Select pre-provisioned instance"
              filteringType="auto"
              disabled={disabled || loadingInstances}
              loading={loadingInstances}
            />
          </FormField>
        )}

        <Alert type="info">
          <strong>Pre-provisioned instance recovery:</strong>
          <ul>
            <li>Instance must have tag <code>AWSDRS=AllowLaunchingIntoThisInstance</code></li>
            <li>Instance will be stopped and volumes replaced during recovery</li>
            <li>Private IP address and network configuration will be preserved</li>
            <li>Instance type right-sizing will be disabled (uses existing instance type)</li>
          </ul>
        </Alert>
      </>
    )}
  </SpaceBetween>
</ExpandableSection>
```

**3.2 Add API Client Methods**

```typescript
// In frontend/src/services/api.ts
export interface PreProvisionedInstance {
  instanceId: string;
  name: string;
  instanceType: string;
  state: string;
  privateIp: string;
  availabilityZone: string;
  launchTime?: string;
  tags: Record<string, string>;
}

class ApiClient {
  // Existing methods...

  async getPreProvisionedInstances(region: string, namePattern?: string): Promise<PreProvisionedInstance[]> {
    const params = new URLSearchParams({ region });
    if (namePattern) {
      params.append('namePattern', namePattern);
    }
    
    const response = await this.request(`/drs/pre-provisioned-instances?${params}`);
    return response.instances;
  }

  async validatePreProvisionedInstance(instanceId: string, region: string): Promise<{
    valid: boolean;
    error?: string;
    instanceState?: string;
    instanceType?: string;
    privateIp?: string;
  }> {
    const response = await this.request('/drs/pre-provisioned-instances/validate', {
      method: 'POST',
      body: JSON.stringify({ instanceId, region })
    });
    return response;
  }
}
```

### Phase 4: Testing & Validation (Week 4-5)

**4.1 Unit Tests**

```python
# tests/python/unit/test_pre_provisioned_instances.py
import pytest
from unittest.mock import Mock, patch
from lambda.api_handler.index import (
    validate_target_instance,
    find_matching_pre_provisioned_instance,
    build_drs_launch_config
)

def test_validate_target_instance_success():
    """Test successful validation of pre-provisioned instance."""
    with patch('boto3.client') as mock_boto3:
        mock_ec2 = Mock()
        mock_boto3.return_value = mock_ec2
        
        mock_ec2.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [{
                    'InstanceId': 'i-1234567890abcdef0',
                    'State': {'Name': 'stopped'},
                    'InstanceType': 'm5.large',
                    'PrivateIpAddress': '10.0.1.100',
                    'Tags': [
                        {'Key': 'Name', 'Value': 'test-instance'},
                        {'Key': 'AWSDRS', 'Value': 'AllowLaunchingIntoThisInstance'}
                    ]
                }]
            }]
        }
        
        result = validate_target_instance('i-1234567890abcdef0', 'us-east-1')
        
        assert result['valid'] is True
        assert result['instanceState'] == 'stopped'
        assert result['instanceType'] == 'm5.large'
        assert result['privateIp'] == '10.0.1.100'

def test_validate_target_instance_missing_tag():
    """Test validation failure when AWSDRS tag is missing."""
    with patch('boto3.client') as mock_boto3:
        mock_ec2 = Mock()
        mock_boto3.return_value = mock_ec2
        
        mock_ec2.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [{
                    'InstanceId': 'i-1234567890abcdef0',
                    'Tags': [{'Key': 'Name', 'Value': 'test-instance'}]
                }]
            }]
        }
        
        result = validate_target_instance('i-1234567890abcdef0', 'us-east-1')
        
        assert result['valid'] is False
        assert 'missing required tag' in result['error']

def test_build_drs_launch_config_pre_provisioned():
    """Test building DRS launch config for pre-provisioned instance."""
    launch_config = {
        'PreProvisionedInstance': {
            'enabled': True,
            'targetInstanceId': 'i-1234567890abcdef0'
        },
        'CopyTags': True,
        'LaunchDisposition': 'STARTED'
    }
    
    current_config = {}
    
    result = build_drs_launch_config(launch_config, current_config, 's-test', 'us-east-1')
    
    assert result['launchIntoInstanceProperties']['launchIntoEC2InstanceID'] == 'i-1234567890abcdef0'
    assert result['targetInstanceTypeRightSizingMethod'] == 'NONE'
    assert result['copyPrivateIp'] is False
    assert result['copyTags'] is True
    assert result['launchDisposition'] == 'STARTED'
```

**4.2 Integration Tests**

```python
# tests/python/integration/test_pre_provisioned_integration.py
import pytest
import boto3
from moto import mock_ec2, mock_drs

@mock_ec2
@mock_drs
def test_end_to_end_pre_provisioned_recovery():
    """Test complete pre-provisioned instance recovery flow."""
    
    # Setup mock EC2 instance with AWSDRS tag
    ec2 = boto3.client('ec2', region_name='us-east-1')
    response = ec2.run_instances(
        ImageId='ami-12345678',
        MinCount=1,
        MaxCount=1,
        InstanceType='m5.large'
    )
    instance_id = response['Instances'][0]['InstanceId']
    
    # Tag instance for DRS pre-provisioned recovery
    ec2.create_tags(
        Resources=[instance_id],
        Tags=[
            {'Key': 'Name', 'Value': 'test-recovery-instance'},
            {'Key': 'AWSDRS', 'Value': 'AllowLaunchingIntoThisInstance'}
        ]
    )
    
    # Test discovery API
    from lambda.api_handler.index import get_pre_provisioned_instances
    instances = get_pre_provisioned_instances('us-east-1')
    
    assert len(instances['instances']) == 1
    assert instances['instances'][0]['instanceId'] == instance_id
    assert instances['instances'][0]['name'] == 'test-recovery-instance'
    
    # Test validation
    from lambda.api_handler.index import validate_target_instance
    validation = validate_target_instance(instance_id, 'us-east-1')
    
    assert validation['valid'] is True
```

### Phase 5: Documentation & Deployment (Week 5)

**5.1 Update API Documentation**

Add to `docs/guides/API_REFERENCE_GUIDE.md`:

```markdown
## Pre-Provisioned Instance Recovery

### GET /api/v1/drs/pre-provisioned-instances

Discover EC2 instances tagged for DRS pre-provisioned recovery.

**Parameters:**
- `region` (required): AWS region to search
- `namePattern` (optional): Filter by instance name pattern

**Response:**
```json
{
  "instances": [
    {
      "instanceId": "i-1234567890abcdef0",
      "name": "web-server-dr",
      "instanceType": "m5.large",
      "state": "stopped",
      "privateIp": "10.0.1.100",
      "availabilityZone": "us-east-1a",
      "launchTime": "2026-01-08T10:00:00Z",
      "tags": {
        "Name": "web-server-dr",
        "AWSDRS": "AllowLaunchingIntoThisInstance"
      }
    }
  ],
  "count": 1,
  "region": "us-east-1"
}
```

### POST /api/v1/drs/pre-provisioned-instances/validate

Validate that an instance is properly configured for pre-provisioned recovery.

**Request:**
```json
{
  "instanceId": "i-1234567890abcdef0",
  "region": "us-east-1"
}
```

**Response:**
```json
{
  "valid": true,
  "instanceState": "stopped",
  "instanceType": "m5.large",
  "privateIp": "10.0.1.100"
}
```
```

**5.2 Update User Guide**

Add to `docs/guides/DRS_EXECUTION_WALKTHROUGH.md`:

```markdown
## Pre-Provisioned Instance Recovery

### Overview

Pre-provisioned instance recovery allows DRS to launch into existing EC2 instances instead of creating new ones. This is useful for:

- Preserving IP addresses and network configurations
- Reusing pre-configured instances
- Meeting compliance requirements

### Setup Requirements

1. **Tag Target Instances**: Add `AWSDRS=AllowLaunchingIntoThisInstance` tag
2. **Name Matching**: Ensure instance Name tag matches source server hostname (for automatic matching)
3. **Instance State**: Instance can be running or stopped (DRS will stop if running)

### Configuration Steps

1. **Create/Edit Protection Group**
2. **Expand Launch Settings**
3. **Enable "Pre-Provisioned Instance Recovery"**
4. **Choose Selection Method**:
   - **Automatic**: Matches by Name tag
   - **Explicit**: Select specific instance ID
5. **Save Configuration**

### Recovery Behavior

When recovery executes:
1. DRS stops the target instance (if running)
2. Replaces EBS volumes with recovery data
3. Starts instance with recovered data
4. Preserves network configuration and private IP
```

## Implementation Summary

### Minimal Code Changes Required

**Backend (Python)**:
- Extend `validate_launch_config()` function
- Add `get_pre_provisioned_instances()` API endpoint
- Extend `apply_launch_config_to_servers()` function
- Add `build_drs_launch_config()` helper function

**Frontend (TypeScript)**:
- Extend `LaunchConfigSection.tsx` component
- Add pre-provisioned instance selection UI
- Add API client methods

**Database**:
- No schema changes required (uses existing `LaunchConfig` field)

### Key Integration Points

1. **Protection Group Creation/Update**: UI and API support for pre-provisioned configuration
2. **Launch Configuration Application**: Automatic DRS API calls during PG save
3. **Recovery Execution**: Uses existing recovery flow with enhanced launch configuration
4. **Validation**: Real-time validation of target instances and tags

### Testing Strategy

- Unit tests for all new functions
- Integration tests with mocked AWS services
- End-to-end tests with actual DRS recovery
- UI component tests for new form elements

### Deployment Plan

- Backward compatible (no breaking changes)
- Feature flag controlled rollout
- Comprehensive documentation updates
- User training materials

---

**Status**: Implementation Ready  
**Estimated Effort**: 5 weeks  
**Dependencies**: Current DRS Orchestration solution v1.4.6+  
**Risk Level**: Low (extends existing patterns)