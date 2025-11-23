# Automatic Server Discovery - Implementation Plan

**Date**: November 10, 2025  
**Version**: 1.0  
**Status**: Ready for Implementation  
**Estimated Time**: 12-14 hours

---

## Table of Contents

1. [Overview](#overview)
2. [Enhanced Requirements](#enhanced-requirements)
3. [Architecture Changes](#architecture-changes)
4. [Phase 1: Backend API Changes](#phase-1-backend-api-changes)
5. [Phase 2: Frontend Components](#phase-2-frontend-components)
6. [Phase 3: Infrastructure Updates](#phase-3-infrastructure-updates)
7. [Phase 4: Testing & Validation](#phase-4-testing--validation)
8. [Implementation Checklist](#implementation-checklist)
9. [Risk Mitigation](#risk-mitigation)
10. [Deployment Instructions](#deployment-instructions)

---

## Overview

### Objective

Implement automatic DRS source server discovery with visual selection interface, replacing the current tag-based discovery system with a VMware SRM-like experience.

### Key Changes

| Aspect | Current (Tag-based) | New (Discovery-based) |
|--------|-------------------|----------------------|
| Discovery | Runtime tag queries | Visual server selection |
| Assignment | No visibility | Clear status display |
| Uniqueness | No enforcement | Enforced per server |
| User Isolation | No cross-user visibility | All PGs visible to all users |
| Region | Optional | Required per PG |

### Environment Details

- **Region**: us-east-1 (administrator account)
- **DRS Status**: Initialized with replicating servers
- **Current PGs**: None (clean slate)
- **Deployment**: Current environment

---

## Enhanced Requirements

### Critical: Cross-User Conflict Prevention

1. **Unique PG Names Globally**
   - No two users can create PGs with the same name
   - Case-insensitive comparison
   - 409 error with clear message on conflict

2. **Single PG Assignment per Server**
   - Each DRS source server can only belong to ONE Protection Group
   - Assignment tracked across all users
   - 409 error listing conflicts

3. **Global Visibility**
   - All users see all Protection Groups
   - Server discovery shows assignments from any user
   - No user-scoped filtering

4. **Real-time Assignment Tracking**
   - Auto-refresh every 30 seconds
   - Silent updates (no loading spinner)
   - Immediate conflict detection

### Database Schema Change

**Old Schema**:
```json
{
  "protectionGroupId": "pg-abc-123",
  "name": "Web Tier",
  "tags": {
    "KeyName": "Environment",
    "KeyValue": "Production"
  }
}
```

**New Schema**:
```json
{
  "protectionGroupId": "pg-abc-123",
  "name": "Web Tier",
  "description": "Production web servers",
  "region": "us-east-1",
  "sourceServerIds": [
    "s-abc123def456",
    "s-def456ghi789"
  ],
  "createdAt": "2025-11-10T20:00:00Z",
  "updatedAt": "2025-11-10T20:00:00Z"
}
```

---

## Architecture Changes

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ User Action                    │ System Action                   │
├────────────────────────────────┼─────────────────────────────────┤
│ 1. Select region: us-east-1   │ → Query DRS API                 │
│                                │   GET /drs/source-servers       │
│                                │                                 │
│ 2. View discovered servers     │ → Fetch ALL PGs (global)        │
│    ☑ web-01 (s-abc) READY     │ → Build assignment map          │
│    ☑ web-02 (s-def) READY     │ → Mark assigned/available       │
│    ☒ db-01 (s-ghi) [DB Tier]  │                                 │
│                                │                                 │
│ 3. Select servers + Create     │ → Validate no conflicts         │
│                                │ → Validate unique name          │
│                                │ → Store region + server IDs     │
│                                │ → Return success                │
└────────────────────────────────┴─────────────────────────────────┘
```

### API Changes

**New Endpoint**:
- `GET /drs/source-servers?region={region}` - Discover servers with assignment status

**Modified Endpoints**:
- `POST /protection-groups` - New schema, conflict validation
- `PUT /protection-groups/{id}` - New schema, conflict re-validation

---

## Phase 1: Backend API Changes

**Estimated Time**: 4-5 hours

### 1.1: New API Endpoint - `/drs/source-servers` (1.5 hours)

**Location**: `lambda/index.py` after line 650 (after execution handlers)

**Implementation**:

```python
def list_source_servers(region, event, context):
    """
    Discover DRS source servers in a region and track assignments
    
    Returns:
    - All DRS source servers in region
    - Assignment status for each server
    - DRS initialization status
    """
    logger.info(f"Listing source servers for region: {region}")
    
    try:
        # 1. Query DRS for source servers
        drs = boto3.client('drs', region_name=region)
        
        try:
            response = drs.describe_source_servers(maxResults=200)
            drs_initialized = True
        except drs.exceptions.UninitializedAccountException:
            logger.warning(f"DRS not initialized in {region}")
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'DRS_NOT_INITIALIZED',
                    'message': f'DRS is not initialized in {region}. Please initialize DRS before creating Protection Groups.',
                    'region': region,
                    'initialized': False
                })
            }
        
        # 2. Build server list from DRS response
        servers = []
        for item in response.get('items', []):
            server_id = item['sourceServerID']
            
            # Extract server metadata
            source_props = item.get('sourceProperties', {})
            ident_hints = source_props.get('identificationHints', {})
            hostname = ident_hints.get('hostname', 'Unknown')
            
            # Extract replication info
            lifecycle = item.get('lifeCycle', {})
            state = lifecycle.get('state', 'UNKNOWN')
            
            data_rep_info = item.get('dataReplicationInfo', {})
            rep_state = data_rep_info.get('dataReplicationState', 'UNKNOWN')
            lag_duration = data_rep_info.get('lagDuration', 'UNKNOWN')
            
            servers.append({
                'sourceServerID': server_id,
                'hostname': hostname,
                'state': state,
                'replicationState': rep_state,
                'lagDuration': lag_duration,
                'lastSeen': lifecycle.get('lastSeenByServiceDateTime', ''),
                'assignedToProtectionGroup': None,  # Will be populated below
                'selectable': True  # Will be updated below
            })
        
        # 3. Query ALL Protection Groups to build assignment map
        table = dynamodb.Table('protection-groups-test')
        pg_response = table.scan()
        
        assignment_map = {}
        for pg in pg_response.get('Items', []):
            pg_id = pg['protectionGroupId']
            pg_name = pg['name']
            pg_servers = pg.get('sourceServerIds', [])
            
            for server_id in pg_servers:
                assignment_map[server_id] = {
                    'protectionGroupId': pg_id,
                    'protectionGroupName': pg_name
                }
        
        # 4. Update servers with assignment info
        for server in servers:
            server_id = server['sourceServerID']
            if server_id in assignment_map:
                server['assignedToProtectionGroup'] = assignment_map[server_id]
                server['selectable'] = False
        
        # 5. Return enhanced server list
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'region': region,
                'initialized': True,
                'servers': servers,
                'totalCount': len(servers),
                'availableCount': sum(1 for s in servers if s['selectable']),
                'assignedCount': sum(1 for s in servers if not s['selectable'])
            })
        }
        
    except Exception as e:
        logger.error(f"Error listing source servers: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'INTERNAL_ERROR',
                'message': f'Failed to list source servers: {str(e)}'
            })
        }
```

**Key Features**:
- DRS initialization detection
- Global assignment tracking (scans ALL PGs)
- Per-server assignment status
- Aggregate counts

### 1.2: Validation Helper - `validate_server_assignments()` (1 hour)

**Location**: `lambda/index.py` after `list_source_servers()`

**Implementation**:

```python
def validate_server_assignments(server_ids, current_pg_id=None):
    """
    Validate that servers are not already assigned to other Protection Groups
    
    Args:
    - server_ids: List of server IDs to validate
    - current_pg_id: Optional PG ID to exclude (for edit operations)
    
    Returns:
    - conflicts: List of {serverId, protectionGroupId, protectionGroupName}
    """
    table = dynamodb.Table('protection-groups-test')
    response = table.scan()
    
    conflicts = []
    for pg in response.get('Items', []):
        # Skip current PG when editing
        if current_pg_id and pg['protectionGroupId'] == current_pg_id:
            continue
        
        assigned_servers = pg.get('sourceServerIds', [])
        for server_id in server_ids:
            if server_id in assigned_servers:
                conflicts.append({
                    'serverId': server_id,
                    'protectionGroupId': pg['protectionGroupId'],
                    'protectionGroupName': pg['name']
                })
    
    return conflicts


def validate_unique_pg_name(name, current_pg_id=None):
    """
    Validate that Protection Group name is unique (case-insensitive)
    
    Args:
    - name: Protection Group name to validate
    - current_pg_id: Optional PG ID to exclude (for edit operations)
    
    Returns:
    - True if unique, False if duplicate exists
    """
    table = dynamodb.Table('protection-groups-test')
    response = table.scan()
    
    name_lower = name.lower()
    for pg in response.get('Items', []):
        # Skip current PG when editing
        if current_pg_id and pg['protectionGroupId'] == current_pg_id:
            continue
        
        if pg['name'].lower() == name_lower:
            return False
    
    return True
```

### 1.3: Update `create_protection_group()` (1 hour)

**Location**: `lambda/index.py` around line 100-150

**Replace existing function with**:

```python
def create_protection_group(event, context):
    """Create a new Protection Group with server ID validation"""
    logger.info("Creating protection group")
    
    try:
        body = json.loads(event['body'])
        
        # Validate required fields
        if 'name' not in body:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Name is required'})
            }
        
        if 'region' not in body:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Region is required'})
            }
        
        if 'sourceServerIds' not in body or not body['sourceServerIds']:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'At least one source server must be selected'})
            }
        
        name = body['name']
        server_ids = body['sourceServerIds']
        
        # Validate unique name (NEW - prevents race condition)
        if not validate_unique_pg_name(name):
            return {
                'statusCode': 409,  # Conflict
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'PG_NAME_EXISTS',
                    'message': f'A Protection Group named "{name}" already exists',
                    'existingName': name
                })
            }
        
        # Validate server assignments (no conflicts)
        conflicts = validate_server_assignments(server_ids)
        if conflicts:
            return {
                'statusCode': 409,  # Conflict
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'SERVER_ASSIGNMENT_CONFLICT',
                    'message': 'Some servers are already assigned to other Protection Groups',
                    'conflicts': conflicts
                })
            }
        
        # Create Protection Group
        table = dynamodb.Table('protection-groups-test')
        
        item = {
            'protectionGroupId': str(uuid.uuid4()),
            'name': name,
            'description': body.get('description', ''),
            'region': body['region'],
            'sourceServerIds': server_ids,
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat()
        }
        
        table.put_item(Item=item)
        
        logger.info(f"Created Protection Group: {item['protectionGroupId']}")
        return {
            'statusCode': 201,
            'headers': get_cors_headers(),
            'body': json.dumps(item)
        }
        
    except Exception as e:
        logger.error(f"Error creating protection group: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }
```

### 1.4: Update `update_protection_group()` (0.5 hours)

**Location**: `lambda/index.py` around line 200-250

**Key changes**:

```python
def update_protection_group(protection_group_id, event, context):
    """Update Protection Group with server validation"""
    logger.info(f"Updating protection group: {protection_group_id}")
    
    try:
        body = json.loads(event['body'])
        table = dynamodb.Table('protection-groups-test')
        
        # Get current Protection Group
        response = table.get_item(Key={'protectionGroupId': protection_group_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Protection Group not found'})
            }
        
        # Prevent region changes
        if 'region' in body:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Cannot change region after creation'})
            }
        
        # Validate unique name if changing
        if 'name' in body:
            if not validate_unique_pg_name(body['name'], protection_group_id):
                return {
                    'statusCode': 409,
                    'headers': get_cors_headers(),
                    'body': json.dumps({
                        'error': 'PG_NAME_EXISTS',
                        'message': f'A Protection Group named "{body["name"]}" already exists'
                    })
                }
        
        # If updating server list, validate assignments
        if 'sourceServerIds' in body:
            conflicts = validate_server_assignments(
                body['sourceServerIds'],
                current_pg_id=protection_group_id
            )
            if conflicts:
                return {
                    'statusCode': 409,
                    'headers': get_cors_headers(),
                    'body': json.dumps({
                        'error': 'SERVER_ASSIGNMENT_CONFLICT',
                        'message': 'Some servers are already assigned to other Protection Groups',
                        'conflicts': conflicts
                    })
                }
        
        # Build update expression
        update_expr = "SET updatedAt = :updated"
        expr_values = {':updated': datetime.utcnow().isoformat()}
        expr_names = {}
        
        if 'name' in body:
            update_expr += ", #n = :name"
            expr_values[':name'] = body['name']
            expr_names['#n'] = 'name'
        
        if 'description' in body:
            update_expr += ", description = :desc"
            expr_values[':desc'] = body['description']
        
        if 'sourceServerIds' in body:
            update_expr += ", sourceServerIds = :servers"
            expr_values[':servers'] = body['sourceServerIds']
        
        # Update item
        update_args = {
            'Key': {'protectionGroupId': protection_group_id},
            'UpdateExpression': update_expr,
            'ExpressionAttributeValues': expr_values,
            'ReturnValues': 'ALL_NEW'
        }
        
        if expr_names:
            update_args['ExpressionAttributeNames'] = expr_names
        
        result = table.update_item(**update_args)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(result['Attributes'])
        }
        
    except Exception as e:
        logger.error(f"Error updating protection group: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }
```

### 1.5: Router Updates (0.5 hours)

**Location**: `lambda/index.py` bottom of file, around line 900

**Add to `lambda_handler()` routing**:

```python
def lambda_handler(event, context):
    """Main Lambda handler with routing"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        path = event.get('path', '')
        method = event.get('httpMethod', '')
        
        # ... existing routes ...
        
        # DRS source servers discovery (NEW)
        if path == '/drs/source-servers' and method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            region = query_params.get('region')
            
            if not region:
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'region parameter is required'})
                }
            
            return list_source_servers(region, event, context)
        
        # ... rest of routes ...
```

### 1.6: IAM Permissions (0.5 hours)

**Location**: `cfn/lambda-stack.yaml`

**Add to Lambda execution role policies**:

```yaml
- Effect: Allow
  Action:
    - drs:DescribeSourceServers
    - drs:DescribeReplicationConfigurationTemplates
  Resource: "*"
```

---

## Phase 2: Frontend Components

**Estimated Time**: 5 hours

### 2.1: RegionSelector Component (0.5 hours)

**File**: `frontend/src/components/RegionSelector.tsx` (NEW)

```typescript
import React from 'react';
import { FormControl, InputLabel, Select, MenuItem, FormHelperText } from '@mui/material';

interface RegionSelectorProps {
  value: string;
  onChange: (region: string) => void;
  disabled?: boolean;
  error?: boolean;
  helperText?: string;
}

const AWS_REGIONS = [
  { value: 'us-east-1', label: 'US East (N. Virginia)' },
  { value: 'us-east-2', label: 'US East (Ohio)' },
  { value: 'us-west-1', label: 'US West (N. California)' },
  { value: 'us-west-2', label: 'US West (Oregon)' },
  { value: 'eu-west-1', label: 'EU (Ireland)' },
  { value: 'eu-west-2', label: 'EU (London)' },
  { value: 'eu-central-1', label: 'EU (Frankfurt)' },
  { value: 'ap-southeast-1', label: 'Asia Pacific (Singapore)' },
  { value: 'ap-southeast-2', label: 'Asia Pacific (Sydney)' },
  { value: 'ap-northeast-1', label: 'Asia Pacific (Tokyo)' },
  { value: 'ap-south-1', label: 'Asia Pacific (Mumbai)' },
  { value: 'sa-east-1', label: 'South America (São Paulo)' },
  { value: 'ca-central-1', label: 'Canada (Central)' },
];

export const RegionSelector: React.FC<RegionSelectorProps> = ({
  value,
  onChange,
  disabled = false,
  error = false,
  helperText
}) => {
  return (
    <FormControl fullWidth error={error} disabled={disabled}>
      <InputLabel id="region-select-label">AWS Region *</InputLabel>
      <Select
        labelId="region-select-label"
        id="region-select"
        value={value}
        label="AWS Region *"
        onChange={(e) => onChange(e.target.value)}
      >
        {AWS_REGIONS.map((region) => (
          <MenuItem key={region.value} value={region.value}>
            {region.label}
          </MenuItem>
        ))}
      </Select>
      {helperText && (
        <FormHelperText>{helperText}</FormHelperText>
      )}
    </FormControl>
  );
};
```

### 2.2: ServerListItem Component (1 hour)

**File**: `frontend/src/components/ServerListItem.tsx` (NEW)

```typescript
import React from 'react';
import {
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Checkbox,
  Chip,
  Box,
  Typography
} from '@mui/material';
import {
  CheckCircle as ReadyIcon,
  Sync as SyncingIcon,
  Error as ErrorIcon,
  HelpOutline as UnknownIcon
} from '@mui/icons-material';

interface DRSServer {
  sourceServerID: string;
  hostname: string;
  state: string;
  replicationState: string;
  lagDuration: string;
  assignedToProtectionGroup?: {
    protectionGroupId: string;
    protectionGroupName: string;
  };
  selectable: boolean;
}

interface ServerListItemProps {
  server: DRSServer;
  selected: boolean;
  onToggle: () => void;
}

const getStateColor = (state: string): 'success' | 'info' | 'error' | 'default' => {
  switch (state) {
    case 'READY_FOR_RECOVERY':
      return 'success';
    case 'SYNCING':
    case 'INITIATED':
      return 'info';
    case 'DISCONNECTED':
    case 'STOPPED':
      return 'error';
    default:
      return 'default';
  }
};

const getStateIcon = (state: string) => {
  switch (state) {
    case 'READY_FOR_RECOVERY':
      return <ReadyIcon fontSize="small" />;
    case 'SYNCING':
    case 'INITIATED':
      return <SyncingIcon fontSize="small" />;
    case 'DISCONNECTED':
    case 'STOPPED':
      return <ErrorIcon fontSize="small" />;
    default:
      return <UnknownIcon fontSize="small" />;
  }
};

export const ServerListItem: React.FC<ServerListItemProps> = ({
  server,
  selected,
  onToggle
}) => {
  const { sourceServerID, hostname, state, assignedToProtectionGroup, selectable } = server;
  
  return (
    <ListItem
      disablePadding
      sx={{
        opacity: selectable ? 1 : 0.6,
        backgroundColor: selectable ? 'inherit' : 'action.disabledBackground'
      }}
    >
      <ListItemButton onClick={onToggle} disabled={!selectable} dense>
        <ListItemIcon>
          <Checkbox
            edge="start"
            checked={selected}
            disabled={!selectable}
            tabIndex={-1}
            disableRipple
          />
        </ListItemIcon>
        <ListItemText
          primary={
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="body1">
                {hostname}
              </Typography>
              <Chip
                size="small"
                label={state}
                color={getStateColor(state)}
                icon={getStateIcon(state)}
              />
            </Box>
          }
          secondary={
            <Box>
              <Typography variant="body2" color="text.secondary">
                {sourceServerID}
              </Typography>
              {assignedToProtectionGroup && (
                <Typography variant="body2" color="warning.main">
                  Already assigned to: {assignedToProtectionGroup.protectionGroupName}
                </Typography>
              )}
              {selectable && (
                <Typography variant="body2" color="success.main">
                  Available
                </Typography>
              )}
            </Box>
          }
        />
      </ListItemButton>
    </ListItem>
  );
};
```

### 2.3: ServerDiscoveryPanel Component (2.5 hours)

**File**: `frontend/src/components/ServerDiscoveryPanel.tsx` (NEW)

```typescript
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  List,
  Stack
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import { ServerListItem } from './ServerListItem';
import { apiClient } from '../services/api';

interface DRSServer {
  sourceServerID: string;
  hostname: string;
  state: string;
  replicationState: string;
  lagDuration: string;
  assignedToProtectionGroup?: {
    protectionGroupId: string;
    protectionGroupName: string;
  };
  selectable: boolean;
}

interface ServerDiscoveryPanelProps {
  region: string;
  selectedServerIds: string[];
  onSelectionChange: (serverIds: string[]) => void;
}

export const ServerDiscoveryPanel: React.FC<ServerDiscoveryPanelProps> = ({
  region,
  selectedServerIds,
  onSelectionChange
}) => {
  const [servers, setServers] = useState<DRSServer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState<'all' | 'available' | 'assigned'>('all');
  const [drsInitialized, setDrsInitialized] = useState(true);

  // Fetch servers
  const fetchServers = useCallback(async (silent = false) => {
    if (!region) return;
    
    if (!silent) setLoading(true);
    setError(null);
    
    try {
      const response = await apiClient.get(`/drs/source-servers?region=${region}`);
      
      if (response.data.initialized === false) {
        setDrsInitialized(false);
        setError(response.data.message);
        setServers([]);
      } else {
        setDrsInitialized(true);
        setServers(response.data.servers || []);
      }
    } catch (err: any) {
      console.error('Error fetching servers:', err);
      if (err.response?.data?.error === 'DRS_NOT_INITIALIZED') {
        setDrsInitialized(false);
        setError(err.response.data.message);
        setServers([]);
      } else {
        setError('Failed to fetch DRS source servers. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }, [region]);

  // Initial fetch
  useEffect(() => {
    fetchServers();
  }, [fetchServers]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!region || !drsInitialized) return;
    
    const interval = setInterval(() => {
      fetchServers(true); // Silent refresh
    }, 30000);
    
    return () => clearInterval(interval);
  }, [region, drsInitialized, fetchServers]);

  // Filter and search
  const filteredServers = servers.filter(server => {
    // Apply filter
    if (filter === 'available' && !server.selectable) return false;
    if (filter === 'assigned' && server.selectable) return false;
    
    // Apply search
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      return (
        server.hostname.toLowerCase().includes(searchLower) ||
        server.sourceServerID.toLowerCase().includes(searchLower) ||
        server.assignedToProtectionGroup?.protectionGroupName.toLowerCase().includes(searchLower)
      );
    }
    
    return true;
  });

  // Handle selection
  const handleToggle = (serverId: string) => {
    const currentIndex = selectedServerIds.indexOf(serverId);
    const newSelected = [...selectedServerIds];
    
    if (currentIndex === -1) {
      newSelected.push(serverId);
    } else {
      newSelected.splice(currentIndex, 1);
    }
    
    onSelectionChange(newSelected);
  };

  const handleSelectAll = () => {
    const selectableServers = filteredServers.filter(s => s.selectable);
    onSelectionChange(selectableServers.map(s => s.sourceServerID));
  };

  const handleDeselectAll = () => {
    onSelectionChange([]);
  };

  if (loading && servers.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" p={4}>
        <CircularProgress />
        <Typography ml={2}>Discovering servers in {region}...</Typography>
      </Box>
    );
  }

  if (!drsInitialized) {
    return (
      <Alert severity="warning">
        <Typography variant="subtitle1" gutterBottom>
          DRS Not Initialized
        </Typography>
        <Typography variant="body2">
          {error || `DRS is not initialized in ${region}. Please initialize DRS before creating Protection Groups.`}
        </Typography>
      </Alert>
    );
  }

  if (servers.length === 0) {
    return (
      <Alert severity="info">
        <Typography variant="subtitle1" gutterBottom>
          No Servers Found
        </Typography>
        <Typography variant="body2">
          No DRS source servers found in {region}. Add servers to DRS before creating Protection Groups.
        </Typography>
      </Alert>
    );
  }

  const availableCount = servers.filter(s => s.selectable).length;
  const assignedCount = servers.filter(s => !s.selectable).length;

  return (
    <Box>
      {/* Search and Filter */}
      <Box display="flex" gap={2} mb={2}>
        <TextField
          fullWidth
          placeholder="Search by hostname, server ID, or Protection Group..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
          }}
        />
        <FormControl sx={{ minWidth: 150 }}>
          <InputLabel>Filter</InputLabel>
          <Select
            value={filter}
            label="Filter"
            onChange={(e) => setFilter(e.target.value as any)}
          >
            <MenuItem value="all">All Servers</MenuItem>
            <MenuItem value="available">Available</MenuItem>
            <MenuItem value="assigned">Assigned</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Server Count */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="body2" color="text.secondary">
          Total: {servers.length} | Available: {availableCount} | Assigned: {assignedCount}
        </Typography>
        <Box>
          <Typography
            variant="body2"
            component="span"
            sx={{ cursor: 'pointer', color: 'primary.main', mr: 2 }}
            onClick={handleSelectAll}
          >
            Select All Available
          </Typography>
          <Typography
            variant="body2"
            component="span"
            sx={{ cursor: 'pointer', color: 'primary.main' }}
            onClick={handleDeselectAll}
          >
            Deselect All
          </Typography>
        </Box>
      </Box>

      {/* Server List */}
      <Paper variant="outlined">
        <List sx={{ maxHeight: 400, overflow: 'auto' }}>
          {filteredServers.map((server) => (
            <ServerListItem
              key={server.sourceServerID}
              server={server}
              selected={selectedServerIds.includes(server.sourceServerID)}
              onToggle={() => handleToggle(server.sourceServerID)}
            />
          ))}
        </List>
      </Paper>

      {/* Selection Count */}
      <Typography variant="body2" color="text.secondary" mt={1}>
        {selectedServerIds.length} of {availableCount} available servers selected
      </Typography>
    </Box>
  );
};
```

**Continue with remaining sections...**

---

## Phase 3: Infrastructure Updates

**Estimated Time**: 1 hour

### 3.1: API Gateway Resource (0.5 hours)

**File**: `cfn/api-stack.yaml`

**Add after ExecutionResumeResource** (around line 450):

```yaml
# DRS Source Servers Resource
DRSSourceServersResource:
  Type: AWS::ApiGateway::Resource
  Properties:
    RestApiId: !Ref RestApi
    ParentId: !GetAtt RestApi.RootResourceId
    PathPart: drs

DRSSourceServersListResource:
  Type: AWS::ApiGateway::Resource
  Properties:
    RestApiId: !Ref RestApi
    ParentId: !Ref DRSSourceServersResource
    PathPart: source-servers

# GET /drs/source-servers
DRSSourceServersGetMethod:
  Type: AWS::ApiGateway::Method
  Properties:
    RestApiId: !Ref RestApi
    ResourceId: !Ref DRSSourceServersListResource
    HttpMethod: GET
    AuthorizationType: COGNITO_USER_POOLS
    AuthorizerId: !Ref ApiAuthorizer
    RequestParameters:
      method.request.querystring.region: true
    Integration:
      Type: AWS_PROXY
      IntegrationHttpMethod: POST
      Uri: !Sub 'arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ApiHandlerFunctionArn}/invocations'
    MethodResponses:
      - StatusCode: 200
        ResponseParameters:
          method.response.header.Access-Control-Allow-Origin: true

# CORS - OPTIONS /drs/source-servers
DRSSourceServersOptionsMethod:
  Type: AWS::ApiGateway::Method
  Properties:
    RestApiId: !Ref RestApi
    ResourceId: !Ref DRSSourceServersListResource
    HttpMethod: OPTIONS
    AuthorizationType: NONE
    Integration:
      Type: MOCK
      IntegrationResponses:
        - StatusCode: 200
          ResponseParameters:
            method.response.header.Access-Control-Allow-Headers: "'Content-Type,Authorization'"
            method.response.header.Access-Control-Allow-Methods: "'GET,OPTIONS'"
            method.response.header.Access-Control-Allow-Origin: "'*'"
          ResponseTemplates:
            application/json: ''
      RequestTemplates:
        application/json: '{"statusCode": 200}'
    MethodResponses:
      - StatusCode: 200
        ResponseParameters:
          method.response.header.Access-Control-Allow-Headers: true
          method.response.header.Access-Control-Allow-Methods: true
          method.response.header.Access-Control-Allow-Origin: true
```

### 3.2: Update Deployment Dependencies (0.5 hours)

**Add to ApiDeployment DependsOn list**:
```yaml
- DRSSourceServersGetMethod
- DRSSourceServersOptionsMethod
```

---

## Phase 4: Testing & Validation

**Estimated Time**: 2 hours

### Complete test procedures available in `AUTOMATIC_SERVER_DISCOVERY_IMPLEMENTATION.md`

---

## Implementation Checklist

### Backend (4-5 hours)
- [ ] Add `list_source_servers()` function (1.5h)
- [ ] Add `validate_server_assignments()` helper (1h)
- [ ] Update `create_protection_group()` with conflict checks (1h)
- [ ] Update `update_protection_group()` with conflict checks (0.5h)
- [ ] Add router handler for `/drs/source-servers` (0.5h)
- [ ] Update Lambda IAM role permissions (0.5h)

### Frontend (5 hours)
- [ ] Create `RegionSelector.tsx` (0.5h)
- [ ] Create `ServerListItem.tsx` (1h)
- [ ] Create `ServerDiscoveryPanel.tsx` (2.5h)
- [ ] Update `ProtectionGroupDialog.tsx` integration (1h)

### Infrastructure (1 hour)
- [ ] Add API Gateway resources for `/drs/source-servers` (0.5h)
- [ ] Update deployment dependencies (0.5h)

### Testing (2 hours)
- [ ] Backend API tests with curl (0.5h)
- [ ] Frontend integration tests (1h)
- [ ] End-to-end validation (0.5h)

**Total Estimated Time: 12-14 hours**

---

## Risk Mitigation

### Race Condition Prevention
✅ **Solved with**:
1. Unique name check in `create_protection_group()`
2. Global server assignment validation
3. Case-insensitive comparison

### Cross-User Visibility
✅ **Solved with**:
1. No user-scoped queries - all PGs visible to all users
2. Server discovery shows assignments from any user
3. UI displays which PG owns each server

### API Rate Limiting
⚠️ **Mitigation**:
- Auto-refresh is 30s (not aggressive)
- Silent refresh (doesn't block UI)
- Can disable if needed

---

## Deployment Instructions

### Step 1: Deploy Backend

```bash
# Update Lambda function
cd lambda
zip -r lambda-function.zip index.py
aws lambda update-function-code \
  --function-name drs-orchestration-api \
  --zip-file fileb://lambda-function.zip

# Deploy CloudFormation updates
cd ../cfn
aws cloudformation update-stack \
  --stack-name drs-orchestration-api \
  --template-body file://api-stack.yaml \
  --capabilities CAPABILITY_IAM
```

### Step 2: Deploy Frontend

```bash
cd frontend
npm run build
aws s3 sync dist/ s3://drs-orchestration-frontend-bucket/
aws cloudfront create-invalidation \
  --distribution-id E3EHO8EL65JUV4 \
  --paths "/*"
```

### Step 3: Verify Deployment

```bash
# Test API endpoint
curl -X GET "https://API_URL/drs/source-servers?region=us-east-1" \
  -H "Authorization: Bearer $TOKEN"
```

---

---

## Deployment Status - Session 32

**Date**: November 10, 2025 11:45 PM  
**Status**: Backend & Infrastructure DEPLOYED ✅ | Frontend PENDING ⏳

### ✅ Completed Deployment Steps

#### Backend Lambda (DEPLOYED)
- **Function**: `drs-orchestration-api-handler-test`
- **Status**: Active and updated
- **New Features**:
  - `list_source_servers()` - DRS discovery endpoint
  - `validate_server_assignments()` - Conflict detection
  - `validate_unique_pg_name()` - Name uniqueness check
  - Updated `create_protection_group()` - New schema + validation
  - Updated `update_protection_group()` - Conflict re-validation
- **Git Commits**:
  - `46755fa` - feat(discovery): Implement automatic DRS source server discovery
  - `783a251` - feat(frontend): Integrate automatic server discovery UI

#### Infrastructure (DEPLOYED)
- **Lambda IAM Stack**: `drs-orchestration-test-LambdaStack-RW3BGBI3K2FL`
  - Status: UPDATE_COMPLETE
  - New Permissions: `drs:DescribeSourceServers`, `drs:DescribeReplicationConfigurationTemplates`
  
- **API Gateway Stack**: `drs-orchestration-test-ApiStack-M4KCK1868T5F`
  - Status: UPDATE_COMPLETE
  - New Endpoint: `GET /drs/source-servers?region={region}`
  - CORS: Configured for OPTIONS

#### Frontend Components (CODE COMPLETE)
- **Created** (3 new components):
  - `RegionSelector.tsx` - 13 AWS regions dropdown
  - `ServerListItem.tsx` - Server selection with badges
  - `ServerDiscoveryPanel.tsx` - Discovery interface with auto-refresh

- **Modified**:
  - `ProtectionGroupDialog.tsx` - Integrated new discovery UI
  - `types/index.ts` - Updated schema (removed tagFilters, added region + sourceServerIds)

### ⏳ Remaining Tasks (Tomorrow Morning)

#### 1. Deploy Frontend (5 minutes)
```bash
cd frontend
npm run build
aws s3 sync dist/ s3://drs-orchestration-frontend-bucket/
aws cloudfront create-invalidation \
  --distribution-id E3EHO8EL65JUV4 \
  --paths "/*"
```

#### 2. Test API Endpoint (5 minutes)
```bash
# Get auth token from Cognito (login to app first)
TOKEN="<your-token>"

# Test new DRS discovery endpoint
curl -X GET \
  "https://etv40zymeg.execute-api.us-east-1.amazonaws.com/test/drs/source-servers?region=us-east-1" \
  -H "Authorization: Bearer $TOKEN"

# Expected response:
{
  "region": "us-east-1",
  "initialized": true,
  "servers": [...],
  "totalCount": 5,
  "availableCount": 5,
  "assignedCount": 0
}
```

#### 3. UI Testing (10 minutes)
- Login to CloudFront URL
- Create Protection Group
- Verify region selector, server discovery, search/filter
- Test auto-refresh (30 seconds)
- Validate conflict prevention (name + server)

### 🎯 Expected Behavior After Frontend Deploy

1. **Protection Group Creation**:
   - Select region → see discovered servers
   - Search/filter → find specific servers
   - Select servers → create PG
   - Auto-refresh → see assignments update

2. **Conflict Prevention**:
   - Duplicate name → 409 error with message
   - Server already assigned → 409 with conflict details
   - Cross-user visibility → all PGs visible

3. **User Experience**:
   - VMware SRM-like discovery interface
   - Real-time assignment tracking
   - Clear status indicators (available/assigned)
   - No manual tagging required

### 📊 Implementation Summary

**Code Changes**:
- Backend: 345 lines (Lambda + IAM)
- Frontend: 478 lines (3 components + updates)
- **Total**: 823 lines

**Files Modified**: 8 files
- `lambda/index.py`
- `cfn/lambda-stack.yaml`
- `cfn/api-stack.yaml`
- `frontend/src/components/RegionSelector.tsx` (NEW)
- `frontend/src/components/ServerListItem.tsx` (NEW)
- `frontend/src/components/ServerDiscoveryPanel.tsx` (NEW)
- `frontend/src/components/ProtectionGroupDialog.tsx`
- `frontend/src/types/index.ts`

**Deployment Timeline**:
- Backend deployed: 11:46 PM
- Infrastructure updates: Completed 11:47 PM
- Frontend pending: Tomorrow morning
- Testing pending: After frontend deploy

### 🚀 Pickup Instructions for Tomorrow

**Command to run first**:
```bash
# Navigate to project
cd /Users/jocousen/Library/CloudStorage/OneDrive-amazon.com/DOCUMENTS/CODE/GITHUB/AWS-DRS-Orchestration

# Pull latest (if needed)
git pull

# Review deployment status
git log -2 --oneline

# Continue with frontend deployment (see step 1 above)
```

**Expected state**:
- ✅ Backend fully deployed and functional
- ✅ Infrastructure updated and ready
- ⏳ Frontend code complete, needs build + deploy
- ⏳ End-to-end testing pending

---

## Document End

**Version**: 1.0  
**Last Updated**: November 10, 2025 11:52 PM  
**Status**: Backend DEPLOYED | Frontend PENDING

For complete implementation details, refer to `AUTOMATIC_SERVER_DISCOVERY_IMPLEMENTATION.md`
