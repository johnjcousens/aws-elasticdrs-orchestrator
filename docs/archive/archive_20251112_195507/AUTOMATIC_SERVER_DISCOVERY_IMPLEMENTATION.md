# Automatic Server Discovery Implementation Guide

**Date**: November 10, 2025  
**Session**: 31  
**Status**: Ready for Implementation  
**Estimated Time**: 12-14 hours

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Requirements](#requirements)
3. [Architecture Overview](#architecture-overview)
4. [Backend Implementation](#backend-implementation)
5. [Frontend Implementation](#frontend-implementation)
6. [Database Schema Changes](#database-schema-changes)
7. [API Specifications](#api-specifications)
8. [Testing Strategy](#testing-strategy)
9. [Implementation Checklist](#implementation-checklist)
10. [Deployment Instructions](#deployment-instructions)
11. [Rollback Plan](#rollback-plan)
12. [Tomorrow's Pickup Instructions](#tomorrows-pickup-instructions)

---

## Executive Summary

### What We're Building

Automatic DRS source server discovery system that provides a VMware SRM-like experience for creating Protection Groups.

### Key Features

1. **Region-based Discovery** - Select AWS region, automatically discover all DRS source servers
2. **Automatic Inventory** - No manual tagging required
3. **Single PG per Server** - Each server can only belong to one Protection Group
4. **Visual Assignment Status** - See which servers are available vs. assigned
5. **Real-time Search** - Filter by hostname, server ID, or Protection Group name
6. **Auto-refresh** - Server list refreshes every 30 seconds
7. **DRS Initialization Check** - Detect and handle uninitialized regions

### Benefits Over Current System

| Feature | Current (Tag-based) | New (Discovery-based) |
|---------|-------------------|----------------------|
| Server Discovery | Manual tagging | Automatic via DRS API |
| Visibility | No visibility | See all available servers |
| Assignment Status | Unknown | Clear visual indication |
| Setup Effort | High (tag each server) | Low (select from list) |
| Error Prevention | Can overlap | Enforced uniqueness |
| User Experience | CLI/manual | GUI dropdown selection |

### Migration Strategy

**Clean Start** - No migration of existing Protection Groups. Starting fresh with new system.

---

## Requirements

### Functional Requirements

1. **FR-1**: User selects AWS region from dropdown
2. **FR-2**: System queries DRS for all source servers in region
3. **FR-3**: System checks if DRS is initialized in region
4. **FR-4**: System displays server list with current state and assignment status
5. **FR-5**: User searches/filters servers by hostname, ID, or assigned PG
6. **FR-6**: User selects multiple servers via checkboxes
7. **FR-7**: System validates no server is assigned to multiple PGs
8. **FR-8**: System creates Protection Group with region + server IDs
9. **FR-9**: System auto-refreshes server list every 30 seconds
10. **FR-10**: System disables servers already assigned to other PGs

### Non-Functional Requirements

1. **NFR-1**: API response time < 2 seconds for server discovery
2. **NFR-2**: UI remains responsive during auto-refresh
3. **NFR-3**: Search filter responds in < 100ms (client-side)
4. **NFR-4**: Graceful degradation if DRS API unavailable
5. **NFR-5**: Clear error messages for all failure scenarios

### Constraints

1. **C-1**: Single region per Protection Group
2. **C-2**: Single Protection Group per server
3. **C-3**: Must work with existing DynamoDB schema
4. **C-4**: Must integrate with existing Cognito authentication
5. **C-5**: Must work with existing API Gateway configuration

---

## Architecture Overview

### Current System (Tag-based)

```
User Action                         System Action
─────────────────────────────────   ─────────────────────────────
1. Manually tag EC2 instances       
   Key=ProtectionGroup               
   Value=MyGroup                     
                                    
2. Create PG via API                → Store tag value in DynamoDB
   POST /protection-groups          
   {                                
     "name": "MyGroup",             
     "tags": {                      
       "ProtectionGroup": "MyGroup" 
     }                              
   }                                
                                    
3. At runtime                       → Query EC2 for instances
                                     with matching tag
```

**Problems:**
- ❌ No visibility into available servers
- ❌ Can't see what's already assigned
- ❌ Manual tagging error-prone
- ❌ Can accidentally overlap assignments

### New System (Discovery-based)

```
User Action                         System Action
─────────────────────────────────   ─────────────────────────────
1. Select region: us-west-2         → Query DRS API
                                     GET /drs/source-servers
                                    
2. View discovered servers          → Fetch all PGs
   ☑ web-01 (s-abc) READY           → Build assignment map
   ☑ web-02 (s-def) READY           → Mark assigned/available
   ☒ db-01 (s-ghi) READY [DB Tier]  
                                    
3. Select servers + Create          → Validate no conflicts
                                     → Store region + server IDs
                                     → Return success
```

**Benefits:**
- ✅ Full visibility into inventory
- ✅ Clear assignment status
- ✅ No manual tagging
- ✅ Enforced uniqueness

### High-Level Data Flow

```mermaid
graph TB
    subgraph "Frontend"
        UI[Protection Group Form]
        Region[Region Selector]
        Panel[Server Discovery Panel]
    end
    
    subgraph "Backend API"
        Endpoint[/drs/source-servers]
        Validator[Assignment Validator]
        Handler[PG Create/Edit Handler]
    end
    
    subgraph "AWS Services"
        DRS[AWS DRS Service]
        DDB[DynamoDB]
    end
    
    UI --> Region
    Region --> Endpoint
    Endpoint --> DRS
    Endpoint --> DDB
    DRS --> Panel
    DDB --> Panel
    Panel --> Validator
    Validator --> Handler
    Handler --> DDB
```

---

## Backend Implementation

### New API Endpoint: `/drs/source-servers`

**Purpose:** Discover DRS source servers in a region with assignment tracking

**Method:** GET  
**Path:** `/drs/source-servers`  
**Query Parameters:**
- `region` (required): AWS region code (e.g., `us-west-2`)

#### Implementation in `lambda/index.py`

**Location:** Add after line 650 (after executions handlers)

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
        
        # 3. Query all Protection Groups to build assignment map
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
```

### Updated Protection Group Handlers

**Modify `create_protection_group()` function:**

**Location:** Around line 100-150 in `lambda/index.py`

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
        
        server_ids = body['sourceServerIds']
        
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
            'name': body['name'],
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

**Modify `update_protection_group()` function:**

**Location:** Around line 200-250 in `lambda/index.py`

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
        
        if 'name' in body:
            update_expr += ", #n = :name"
            expr_values[':name'] = body['name']
        
        if 'description' in body:
            update_expr += ", description = :desc"
            expr_values[':desc'] = body['description']
        
        if 'sourceServerIds' in body:
            update_expr += ", sourceServerIds = :servers"
            expr_values[':servers'] = body['sourceServerIds']
        
        # Region cannot be changed after creation
        # This is intentional - would require moving servers
        
        table.update_item(
            Key={'protectionGroupId': protection_group_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames={'#n': 'name'} if 'name' in body else None,
            ExpressionAttributeValues=expr_values
        )
        
        # Return updated item
        response = table.get_item(Key={'protectionGroupId': protection_group_id})
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(response['Item'])
        }
        
    except Exception as e:
        logger.error(f"Error updating protection group: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }
```

### Router Updates

**Add to main router function:**

**Location:** Bottom of `lambda/index.py`, around line 900

```python
def lambda_handler(event, context):
    """Main Lambda handler with routing"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        path = event.get('path', '')
        method = event.get('httpMethod', '')
        
        # ... existing routes ...
        
        # DRS source servers discovery
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

### IAM Permissions

**Add to Lambda execution role in `cfn/lambda-stack.yaml`:**

```yaml
- Effect: Allow
  Action:
    - drs:DescribeSourceServers
    - drs:DescribeReplicationConfigurationTemplates
  Resource: "*"
```

---

## Frontend Implementation

### Component Hierarchy

```
ProtectionGroupsPage
├─ Create/Edit Dialog
│  ├─ Name Input
│  ├─ Description Input
│  ├─ RegionSelector (NEW)
│  └─ ServerDiscoveryPanel (NEW)
│     ├─ Search Input
│     ├─ Filter Dropdown
│     ├─ Server Count Display
│     └─ ServerListItem[] (NEW)
│        ├─ Checkbox
│        ├─ Hostname
│        ├─ Server ID
│        ├─ State Badge
│        └─ Assignment Status
```

### Component 1: RegionSelector

**File:** `frontend/src/components/RegionSelector.tsx`

```typescript
import React from 'react';
import { FormControl, InputLabel, Select, MenuItem } from '@mui/material';

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
      {helperText && <span style={{ fontSize: '0.75rem', color: error ? 'error' : 'text.secondary' }}>{helperText}</span>}
    </FormControl>
  );
};
```

### Component 2: ServerDiscoveryPanel

**File:** `frontend/src/components/ServerDiscoveryPanel.tsx`

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
  List
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

### Component 3: ServerListItem

**File:** `frontend/src/components/ServerListItem.tsx`

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

### Component Integration

**Update `ProtectionGroupsPage.tsx`:**

**Location:** `frontend/src/pages/ProtectionGroupsPage.tsx`

```typescript
// Add imports
import { RegionSelector } from '../components/RegionSelector';
import { ServerDiscoveryPanel } from '../components/ServerDiscoveryPanel';

// Update form state
interface ProtectionGroupFormState {
  name: string;
  description: string;
  region: string;  // NEW
  sourceServerIds: string[];  // NEW (replace tags)
}

// In dialog component
<DialogContent>
  <TextField
    label="Name"
    fullWidth
    required
    value={formData.name}
    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
    margin="normal"
  />
  <TextField
    label="Description"
    fullWidth
    multiline
    rows={2}
    value={formData.description}
    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
    margin="normal"
  />
  
  {/* NEW: Region Selector */}
  <Box mt={2}>
    <RegionSelector
      value={formData.region}
      onChange={(region) => setFormData({ ...formData, region, sourceServerIds: [] })}
      error={!formData.region}
      helperText={!formData.region ? "Please select a region" : ""}
    />
  </Box>
  
  {/* NEW: Server Discovery Panel */}
  {formData.region && (
    <Box mt={3}>
      <Typography variant="subtitle1" gutterBottom>
        Select Source Servers
      </Typography>
      <ServerDiscoveryPanel
        region={formData.region}
        selectedServerIds={formData.sourceServerIds}
        onSelectionChange={(serverIds) => 
          setFormData({ ...formData, sourceServerIds: serverIds })
        }
      />
    </Box>
  )}
</DialogContent>
```

---

## Database Schema Changes

### Old Schema (Tag-based)

```json
{
  "protectionGroupId": "pg-abc-123",
  "name": "Web Tier",
  "description": "Web application servers",
  "region": "us-west-2",
  "tags": {
    "ProtectionGroup": "Web Tier"
  },
  "createdAt": "2025-11-10T20:00:00Z",
  "updatedAt": "2025-11-10T20:00:00Z"
}
```

### New Schema (Server ID-based)

```json
{
  "protectionGroupId": "pg-abc-123",
  "name": "Web Tier",
  "description": "Web application servers",
  "region": "us-west-2",
  "sourceServerIds": [
    "s-abc123def456",
    "s-def456ghi789",
    "s-ghi789jkl012"
  ],
  "createdAt": "2025-11-10T20:00:00Z",
  "updatedAt": "2025-11-10T20:00:00Z"
}
```

### Changes Summary

| Field | Old | New | Notes |
|-------|-----|-----|-------|
| `tags` | Object | REMOVED | No longer needed |
| `sourceServerIds` | N/A | Array of strings | NEW - List of DRS source server IDs |
| `region` | String | String (enforced) | Now validated as required |

### Migration Notes

**N/A** - Starting fresh, no migration needed.

---

## API Specifications

### 1. List DRS Source Servers

**Endpoint:** `GET /drs/source-servers`

**Request:**
```
GET /drs/source-servers?region=us-west-2
Authorization: Bearer <cognito-token>
```

**Success Response (200):**
```json
{
  "region": "us-west-2",
  "initialized": true,
  "servers": [
    {
      "sourceServerID": "s-abc123def456",
      "hostname": "web-server-01",
      "state": "READY_FOR_RECOVERY",
      "replicationState": "CONTINUOUS",
      "lagDuration": "PT5S",
      "lastSeen": "2025-11-10T20:00:00Z",
      "assignedToProtectionGroup": null,
      "selectable": true
    },
    {
      "sourceServerID": "s-def456ghi789",
      "hostname": "db-server-01",
      "state": "READY_FOR_RECOVERY",
      "replicationState": "CONTINUOUS",
      "lagDuration": "PT3S",
      "lastSeen": "2025-11-10T20:00:00Z",
      "assignedToProtectionGroup": {
        "protectionGroupId": "pg-xyz-789",
        "protectionGroupName": "Database Tier"
      },
      "selectable": false
    }
  ],
  "totalCount": 2,
  "availableCount": 1,
  "assignedCount": 1
}
```

**Error Response - DRS Not Initialized (400):**
```json
{
  "error": "DRS_NOT_INITIALIZED",
  "message": "DRS is not initialized in us-west-2. Please initialize DRS before creating Protection Groups.",
  "region": "us-west-2",
  "initialized": false
}
```

**Error Response - Missing Region (400):**
```json
{
  "error": "MISSING_PARAMETER",
  "message": "region parameter is required"
}
```

### 2. Create Protection Group

**Endpoint:** `POST /protection-groups`

**Request:**
```json
{
  "name": "Web Tier",
  "description": "Web application servers",
  "region": "us-west-2",
  "sourceServerIds": [
    "s-abc123def456",
    "s-ghi789jkl012"
  ]
}
```

**Success Response (201):**
```json
{
  "protectionGroupId": "pg-new-123",
  "name": "Web Tier",
  "description": "Web application servers",
  "region": "us-west-2",
  "sourceServerIds": [
    "s-abc123def456",
    "s-ghi789jkl012"
  ],
  "createdAt": "2025-11-10T21:00:00Z",
  "updatedAt": "2025-11-10T21:00:00Z"
}
```

**Error Response - Server Conflict (409):**
```json
{
  "error": "SERVER_ASSIGNMENT_CONFLICT",
  "message": "Some servers are already assigned to other Protection Groups",
  "conflicts": [
    {
      "serverId": "s-abc123def456",
      "protectionGroupId": "pg-existing-456",
      "protectionGroupName": "Database Tier"
    }
  ]
}
```

**Error Response - Validation (400):**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "At least one source server must be selected"
}
```

### 3. Update Protection Group

**Endpoint:** `PUT /protection-groups/{protectionGroupId}`

**Request:**
```json
{
  "name": "Web Tier Updated",
  "sourceServerIds": [
    "s-abc123def456",
    "s-ghi789jkl012",
    "s-mno345pqr678"
  ]
}
```

**Success Response (200):**
```json
{
  "protectionGroupId": "pg-abc-123",
  "name": "Web Tier Updated",
  "description": "Web application servers",
  "region": "us-west-2",
  "sourceServerIds": [
    "s-abc123def456",
    "s-ghi789jkl012",
    "s-mno345pqr678"
  ],
  "createdAt": "2025-11-10T20:00:00Z",
  "updatedAt": "2025-11-10T21:30:00Z"
}
```

**Error Response - Server Conflict (409):**
```json
{
  "error": "SERVER_ASSIGNMENT_CONFLICT",
  "message": "Some servers are already assigned to other Protection Groups",
  "conflicts": [
    {
      "serverId": "s-mno345pqr678",
      "protectionGroupId": "pg-other-789",
      "protectionGroupName": "App Tier"
    }
  ]
}
```

---

## Testing Strategy

### Unit Tests

#### Backend Tests (`lambda/tests/test_server_discovery.py`)

```python
def test_list_source_servers_success():
    """Test successful server discovery"""
    # Mock DRS response
    # Assert server list returned
    # Assert assignment map correct

def test_list_source_servers_not_initialized():
    """Test DRS not initialized error"""
    # Mock UninitializedAccountException
    # Assert 400 status
    # Assert error message

def test_validate_server_assignments_no_conflicts():
    """Test validation with no conflicts"""
    # Mock DynamoDB with existing PGs
    # Assert no conflicts returned

def test_validate_server_assignments_with_conflicts():
    """Test validation with conflicts"""
    # Mock DynamoDB with conflicting PGs
    # Assert conflicts detected

def test_create_protection_group_with_validation():
    """Test PG creation with server validation"""
    # Mock validation success
    # Assert PG created

def test_create_protection_group_conflict():
    """Test PG creation with conflict"""
    # Mock validation failure
    # Assert 409 status
```

#### Frontend Tests (`frontend/src/components/__tests__/`)

```typescript
describe('RegionSelector', () => {
  it('renders all regions', () => {});
  it('calls onChange when region selected', () => {});
  it('displays error state', () => {});
});

describe('ServerDiscoveryPanel', () => {
  it('fetches servers on mount', () => {});
  it('displays loading state', () => {});
  it('displays DRS not initialized error', () => {});
  it('displays no servers message', () => {});
  it('filters servers by search term', () => {});
  it('filters servers by availability', () => {});
  it('auto-refreshes every 30 seconds', () => {});
  it('handles server selection', () => {});
});

describe('ServerListItem', () => {
  it('renders available server', () => {});
  it('renders assigned server as disabled', () => {});
  it('shows assignment status', () => {});
  it('calls onToggle when clicked', () => {});
});
```

### Integration Tests

#### API Integration (`tests/integration/test_discovery_flow.py`)

```python
def test_full_discovery_flow():
    """Test complete discovery flow"""
    # 1. Query /drs/source-servers
    # 2. Verify servers returned
    # 3. Create PG with selected servers
    # 4. Query servers again
    # 5. Verify assignment status updated

def test_conflict_detection():
    """Test server conflict detection"""
    # 1. Create PG with servers
    # 2. Try to create another PG with same servers
    # 3. Assert 409 error
    # 4. Assert conflict details correct
```

### E2E Tests (Playwright)

```typescript
test('create protection group with server discovery', async ({ page }) => {
  // 1. Login
  // 2. Navigate to Protection Groups
  // 3. Click Create
  // 4. Enter name and description
  // 5. Select region
  // 6. Wait for servers to load
  // 7. Search for specific server
  // 8. Select servers
  // 9. Click Create
  // 10. Verify success message
  // 11. Verify PG appears in list
});

test('server assignment conflict handling', async ({ page }) => {
  // 1. Create first PG with server A
  // 2. Try to create second PG with server A
  // 3. Verify error message shown
  // 4. Verify conflict details displayed
});
```

---

## Implementation Checklist

### Phase 1: Backend API (4 hours)

- [ ] **1.1** Add `list_source_servers()` function to lambda/index.py
- [ ] **1.2** Add `validate_server_assignments()` function to lambda/index.py
- [ ] **1.3** Update `create_protection_group()` with validation
- [ ] **1.4** Update `update_protection_group()` with validation
- [ ] **1.5** Add route for `/drs/source-servers` in lambda_handler
- [ ] **1.6** Add IAM permissions for DRS API in cfn/lambda-stack.yaml
- [ ] **1.7** Test API endpoints with curl/Postman

### Phase 2: Frontend Components (5 hours)

- [ ] **2.1** Create RegionSelector component
- [ ] **2.2** Create ServerListItem component
- [ ] **2.3** Create ServerDiscoveryPanel component with search & filter
- [ ] **2.4** Add auto-refresh logic (30s interval)
- [ ] **2.5** Update ProtectionGroupsPage with new components
- [ ] **2.6** Remove old tag-based UI elements
- [ ] **2.7** Test components in browser

### Phase 3: API Gateway (1 hour)

- [ ] **3.1** Add `/drs/source-servers` resource in cfn/api-stack.yaml
- [ ] **3.2** Add GET method with Cognito authorizer
- [ ] **3.3** Add CORS configuration
- [ ] **3.4** Deploy CloudFormation stack
- [ ] **3.5** Test endpoint with frontend

### Phase 4: Testing (2 hours)

- [ ] **4.1** Test with initialized DRS region
- [ ] **4.2** Test with uninitialized DRS region
- [ ] **4.3** Test with no servers in region
- [ ] **4.4** Test server selection and filtering
- [ ] **4.5** Test auto-refresh functionality
- [ ] **4.6** Test assignment conflict detection
- [ ] **4.7** Test creating PG with selected servers
- [ ] **4.8** Test editing PG and moving servers
- [ ] **4.9** Test error scenarios
- [ ] **4.10** End-to-end validation

---

## Deployment Instructions

### Step 1: Deploy Backend

```bash
# Navigate to project
cd AWS-DRS-Orchestration

# Update Lambda function
cd lambda
zip -r ../lambda-function.zip .
aws lambda update-function-code \
  --function-name drs-orchestration-api \
  --zip-file fileb://../lambda-function.zip

# Deploy CloudFormation stack
cd ../cfn
aws cloudformation update-stack \
  --stack-name drs-orchestration-api \
  --template-body file://api-stack.yaml \
  --capabilities CAPABILITY_IAM
```

### Step 2: Deploy Frontend

```bash
# Build frontend
cd ../frontend
npm run build

# Sync to S3
aws s3 sync dist/ s3://drs-orchestration-frontend-bucket/

# Invalidate CloudFront
aws cloudfront create-invalidation \
  --distribution-id E3EHO8EL65JUV4 \
  --paths "/*"
```

### Step 3: Verify Deployment

```bash
# Test API endpoint
curl -X GET \
  "https://etv40zymeg.execute-api.us-east-1.amazonaws.com/test/drs/source-servers?region=us-west-2" \
  -H "Authorization: Bearer <token>"

# Open frontend
open https://d20h85rw0j51j.cloudfront.net
```

---

## Rollback Plan

### If Backend Issues

```bash
# Revert Lambda function
aws lambda update-function-code \
  --function-name drs-orchestration-api \
  --s3-bucket previous-version-bucket \
  --s3-key lambda-function-v1.zip

# Revert CloudFormation stack
aws cloudformation update-stack \
  --stack-name drs-orchestration-api \
  --template-body file://api-stack-previous.yaml \
  --capabilities CAPABILITY_IAM
```

### If Frontend Issues

```bash
# Sync previous version
aws s3 sync s3://backup-bucket/ s3://drs-orchestration-frontend-bucket/

# Invalidate CloudFront
aws cloudfront create-invalidation \
  --distribution-id E3EHO8EL65JUV4 \
  --paths "/*"
```

### If Database Issues

**No database migration** - Just delete any test Protection Groups if needed:

```bash
aws dynamodb delete-item \
  --table-name protection-groups-test \
  --key '{"protectionGroupId":{"S":"pg-test-123"}}'
```

---

## Tomorrow's Pickup Instructions

### Exact Command to Give Cline

```
Read docs/AUTOMATIC_SERVER_DISCOVERY_IMPLEMENTATION.md and implement 
all checklist items in order. Start with Phase 1: Backend API, 
specifically task 1.1 - Add list_source_servers() function to lambda/index.py.
```

### What to Check First

1. **Read the implementation guide:**
   ```
   open AWS-DRS-Orchestration/docs/AUTOMATIC_SERVER_DISCOVERY_IMPLEMENTATION.md
   ```

2. **Review current lambda code:**
   ```
   open AWS-DRS-Orchestration/lambda/index.py
   ```

3. **Check git status:**
   ```bash
   cd AWS-DRS-Orchestration
   git status
   git log --oneline -5
   ```

### Implementation Order

1. **Backend First** (Checklist 1.1-1.7) - ~4 hours
   - Add new API endpoint
   - Add validation logic
   - Update existing handlers
   - Add IAM permissions
   - Test with curl

2. **Frontend Second** (Checklist 2.1-2.7) - ~5 hours
   - Create components
   - Wire up to API
   - Test in browser

3. **Infrastructure Third** (Checklist 3.1-3.5) - ~1 hour
   - Update API Gateway
   - Deploy changes

4. **Testing Last** (Checklist 4.1-4.10) - ~2 hours
   - Comprehensive testing
   - Bug fixes

### Key Files to Modify

**Backend:**
- `lambda/index.py` - Add functions and routes
- `cfn/lambda-stack.yaml` - Add IAM permissions
- `cfn/api-stack.yaml` - Add API endpoint

**Frontend:**
- `frontend/src/components/RegionSelector.tsx` - NEW
- `frontend/src/components/ServerDiscoveryPanel.tsx` - NEW
- `frontend/src/components/ServerListItem.tsx` - NEW
- `frontend/src/pages/ProtectionGroupsPage.tsx` - MODIFY

### Success Criteria

✅ Backend API returns server list with assignment status  
✅ Frontend displays region selector  
✅ Frontend shows discovered servers  
✅ Search and filter work  
✅ Auto-refresh every 30 seconds  
✅ Server selection creates PG  
✅ Assignment conflicts detected and prevented  
✅ All tests pass  

---

## Document End

**Version**: 1.0  
**Date**: November 10, 2025  
**Status**: Ready for Implementation  
**Total Implementation Time**: 12-14 hours

For questions or clarifications, refer to Session 31 conversation in `.cline_memory/conversations/`
