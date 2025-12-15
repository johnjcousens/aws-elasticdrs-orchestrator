# DRS Source Servers Page Implementation Plan

## Executive Summary

This document outlines the implementation plan for a dedicated Source Servers page that replicates the functionality of the AWS DRS Console's Source Servers view within our orchestration solution. This provides a unified experience where users can monitor all DRS source servers without leaving the application.

---

## Objective

Create a comprehensive Source Servers page that mirrors the AWS DRS Console experience, displaying:
- All DRS source servers across configured regions
- Real-time replication status and health
- Recovery readiness indicators
- Last recovery results
- Pending actions and recommendations

---

## AWS DRS Console Reference

The AWS DRS Console Source Servers page displays the following columns:

| Column | Description | Data Source |
|--------|-------------|-------------|
| Hostname | Server hostname | `sourceProperties.identificationHints.hostname` |
| Ready for Recovery | Boolean indicator | Derived from `dataReplicationInfo.dataReplicationState` |
| Data Replication Status | Current replication state with progress | `dataReplicationInfo.*` |
| Last Recovery Result | Success/Failed/Pending with timestamp | `lifeCycle.lastLaunch.*` + `lastLaunchResult` |
| Pending Actions | Actionable recommendations | Derived from multiple fields |

---

## DRS API Analysis

### Primary API: DescribeSourceServers

**Endpoint**: `POST /DescribeSourceServers`

**Request**:
```json
{
  "filters": {
    "sourceServerIDs": ["s-xxx"],
    "isArchived": false,
    "replicationTypes": ["AGENT_BASED"],
    "lifeCycleStates": ["READY_FOR_TEST", "READY_FOR_CUTOVER"]
  },
  "maxResults": 200,
  "nextToken": "string"
}
```

**Response Structure** (key fields):
```json
{
  "items": [{
    "sourceServerID": "s-1234567890abcdef0",
    "arn": "arn:aws:drs:us-east-1:123456789012:source-server/s-xxx",
    "tags": {},
    
    "sourceProperties": {
      "identificationHints": {
        "hostname": "web-server-01",
        "fqdn": "web-server-01.example.com",
        "vmPath": "/datacenter/vm/web-server-01",
        "vmWareUuid": "uuid-xxx"
      },
      "os": {
        "fullString": "Microsoft Windows Server 2019 Datacenter"
      },
      "cpus": [{"cores": 4, "modelName": "Intel Xeon"}],
      "ramBytes": 17179869184,
      "disks": [{
        "deviceName": "/dev/sda",
        "bytes": 107374182400
      }],
      "networkInterfaces": [{
        "macAddress": "00:00:00:00:00:00",
        "ips": ["10.0.1.100"],
        "isPrimary": true
      }],
      "lastUpdatedDateTime": "2025-12-15T10:00:00Z"
    },
    
    "dataReplicationInfo": {
      "dataReplicationState": "CONTINUOUS",
      "dataReplicationInitiation": {
        "startDateTime": "2025-12-01T00:00:00Z",
        "nextAttemptDateTime": null,
        "steps": [{
          "name": "WAIT",
          "status": "SUCCEEDED"
        }]
      },
      "etaDateTime": null,
      "lagDuration": "PT30S",
      "replicatedDisks": [{
        "deviceName": "/dev/sda",
        "totalStorageBytes": 107374182400,
        "replicatedStorageBytes": 107374182400,
        "rescannedStorageBytes": 0,
        "backloggedStorageBytes": 0
      }],
      "stagingAvailabilityZone": "us-east-1a"
    },
    
    "lifeCycle": {
      "addedToServiceDateTime": "2025-12-01T00:00:00Z",
      "firstByteDateTime": "2025-12-01T00:05:00Z",
      "elapsedReplicationDuration": "P14D",
      "lastSeenByServiceDateTime": "2025-12-15T10:00:00Z",
      "lastLaunch": {
        "initiated": {
          "apiCallDateTime": "2025-12-14T10:00:00Z",
          "jobID": "drsjob-xxx",
          "type": "DRILL"
        },
        "status": "LAUNCHED"
      }
    },
    
    "lastLaunchResult": "SUCCEEDED",
    "recoveryInstanceId": null,
    "replicationDirection": "FAILOVER",
    "reversedDirectionSourceServerArn": null,
    "stagingArea": {
      "stagingAccountID": "123456789012",
      "stagingSourceServerArn": null,
      "status": "READY"
    },
    "sourceCloudProperties": {
      "originAccountID": "123456789012",
      "originAvailabilityZone": "us-west-2a",
      "originRegion": "us-west-2"
    }
  }]
}
```

### DataReplicationState Values

| State | Description | UI Display |
|-------|-------------|------------|
| `STOPPED` | Replication stopped | ⚫ Stopped |
| `INITIATING` | Starting replication | 🔵 Initiating |
| `INITIAL_SYNC` | Initial sync in progress | 🔵 Initial sync (X%) |
| `BACKLOG` | Processing backlog | 🟡 Backlog |
| `CREATING_SNAPSHOT` | Creating snapshot | 🔵 Creating snapshot |
| `CONTINUOUS` | Healthy continuous replication | 🟢 Healthy |
| `PAUSED` | Replication paused | 🟡 Paused |
| `RESCAN` | Rescanning disks | 🔵 Rescanning (X%) |
| `STALLED` | Replication stalled | 🔴 Stalled |
| `DISCONNECTED` | Agent disconnected | 🔴 Disconnected |

### LastLaunchResult Values

| Value | Description | UI Display |
|-------|-------------|------------|
| `NOT_STARTED` | Never launched | — |
| `PENDING` | Launch in progress | 🔵 Pending |
| `SUCCEEDED` | Last launch successful | 🟢 Successful |
| `FAILED` | Last launch failed | 🔴 Failed |

---

## UI Design

### Page Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ Source Servers                                    [Region ▼] [⟳]   │
│ Monitor DRS source servers and replication status                   │
├─────────────────────────────────────────────────────────────────────┤
│ [Search servers...]                              Showing 24 servers │
├─────────────────────────────────────────────────────────────────────┤
│ □ Hostname          Ready  Replication Status  Last Recovery  Actions│
├─────────────────────────────────────────────────────────────────────┤
│ □ web-server-01     ✓      🟢 Healthy          🟢 Successful   [⋮]  │
│ □ app-server-01     ✓      🟢 Healthy (30s)    🟢 Successful   [⋮]  │
│ □ db-server-01      ✓      🔵 Initial sync 45% —               [⋮]  │
│ □ web-server-02     ✗      🔴 Stalled          🔴 Failed       [⋮]  │
│ □ app-server-02     ✓      🟡 Backlog          🟢 Successful   [⋮]  │
└─────────────────────────────────────────────────────────────────────┘
```

### CloudScape Components

```typescript
// Main page structure
<ContentLayout
  header={
    <Header
      variant="h1"
      description="Monitor DRS source servers and replication status"
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <RegionSelector value={region} onChange={setRegion} />
          <Button iconName="refresh" onClick={refresh} loading={loading}>
            Refresh
          </Button>
        </SpaceBetween>
      }
    >
      Source Servers
    </Header>
  }
>
  <Table
    items={servers}
    columnDefinitions={columnDefinitions}
    filter={<TextFilter filteringText={filterText} />}
    pagination={<Pagination />}
    loading={loading}
    empty={<EmptyState />}
  />
</ContentLayout>
```

### Column Definitions

```typescript
const columnDefinitions: TableProps.ColumnDefinition<SourceServer>[] = [
  {
    id: 'hostname',
    header: 'Hostname',
    cell: (item) => (
      <Link href={`/source-servers/${item.sourceServerID}`}>
        {item.sourceProperties?.identificationHints?.hostname || item.sourceServerID}
      </Link>
    ),
    sortingField: 'hostname',
    width: 200,
  },
  {
    id: 'readyForRecovery',
    header: 'Ready for Recovery',
    cell: (item) => (
      <StatusIndicator type={isReadyForRecovery(item) ? 'success' : 'error'}>
        {isReadyForRecovery(item) ? 'Yes' : 'No'}
      </StatusIndicator>
    ),
    width: 140,
  },
  {
    id: 'replicationStatus',
    header: 'Data Replication Status',
    cell: (item) => <ReplicationStatusCell server={item} />,
    width: 200,
  },
  {
    id: 'lastRecoveryResult',
    header: 'Last Recovery Result',
    cell: (item) => <LastRecoveryCell server={item} />,
    width: 180,
  },
  {
    id: 'actions',
    header: 'Actions',
    cell: (item) => <ActionsDropdown server={item} />,
    width: 100,
  },
];
```

---

## TypeScript Interfaces

```typescript
// types/drs.ts

export interface SourceServer {
  sourceServerID: string;
  arn: string;
  tags: Record<string, string>;
  sourceProperties: SourceProperties | null;
  dataReplicationInfo: DataReplicationInfo | null;
  lifeCycle: LifeCycle | null;
  lastLaunchResult: LastLaunchResult;
  recoveryInstanceId: string | null;
  replicationDirection: 'FAILOVER' | 'FAILBACK';
  stagingArea: StagingArea;
  sourceCloudProperties: SourceCloudProperties | null;
}

export interface SourceProperties {
  identificationHints: {
    hostname: string;
    fqdn: string;
    vmPath?: string;
    vmWareUuid?: string;
  };
  os: {
    fullString: string;
  };
  cpus: Array<{ cores: number; modelName: string }>;
  ramBytes: number;
  disks: Array<{
    deviceName: string;
    bytes: number;
  }>;
  networkInterfaces: Array<{
    macAddress: string;
    ips: string[];
    isPrimary: boolean;
  }>;
  lastUpdatedDateTime: string;
}

export interface DataReplicationInfo {
  dataReplicationState: DataReplicationState;
  dataReplicationInitiation: {
    startDateTime: string;
    nextAttemptDateTime: string | null;
    steps: Array<{
      name: string;
      status: 'NOT_STARTED' | 'IN_PROGRESS' | 'SUCCEEDED' | 'FAILED' | 'SKIPPED';
    }>;
  };
  etaDateTime: string | null;
  lagDuration: string | null;
  replicatedDisks: ReplicatedDisk[];
  stagingAvailabilityZone: string;
}

export type DataReplicationState =
  | 'STOPPED'
  | 'INITIATING'
  | 'INITIAL_SYNC'
  | 'BACKLOG'
  | 'CREATING_SNAPSHOT'
  | 'CONTINUOUS'
  | 'PAUSED'
  | 'RESCAN'
  | 'STALLED'
  | 'DISCONNECTED';

export interface ReplicatedDisk {
  deviceName: string;
  totalStorageBytes: number;
  replicatedStorageBytes: number;
  rescannedStorageBytes: number;
  backloggedStorageBytes: number;
}

export interface LifeCycle {
  addedToServiceDateTime: string;
  firstByteDateTime: string | null;
  elapsedReplicationDuration: string | null;
  lastSeenByServiceDateTime: string;
  lastLaunch: {
    initiated: {
      apiCallDateTime: string;
      jobID: string;
      type: 'RECOVERY' | 'DRILL';
    } | null;
    status: 'PENDING' | 'IN_PROGRESS' | 'LAUNCHED' | 'FAILED' | 'TERMINATED';
  } | null;
}

export type LastLaunchResult = 'NOT_STARTED' | 'PENDING' | 'SUCCEEDED' | 'FAILED';

export interface StagingArea {
  stagingAccountID: string;
  stagingSourceServerArn: string | null;
  status: 'READY' | 'NOT_READY' | 'EXTENDED';
}

export interface SourceCloudProperties {
  originAccountID: string;
  originAvailabilityZone: string;
  originRegion: string;
}
```

---

## Helper Functions

```typescript
// utils/drsHelpers.ts

export function isReadyForRecovery(server: SourceServer): boolean {
  const state = server.dataReplicationInfo?.dataReplicationState;
  return state === 'CONTINUOUS' || state === 'CREATING_SNAPSHOT';
}

export function getReplicationProgress(server: SourceServer): number | null {
  const disks = server.dataReplicationInfo?.replicatedDisks;
  if (!disks || disks.length === 0) return null;
  
  const totalBytes = disks.reduce((sum, d) => sum + d.totalStorageBytes, 0);
  const replicatedBytes = disks.reduce((sum, d) => sum + d.replicatedStorageBytes, 0);
  
  if (totalBytes === 0) return 100;
  return Math.round((replicatedBytes / totalBytes) * 100);
}

export function formatLagDuration(lagDuration: string | null): string {
  if (!lagDuration) return '—';
  
  // Parse ISO 8601 duration (e.g., "PT30S", "PT5M", "PT1H30M")
  const match = lagDuration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
  if (!match) return lagDuration;
  
  const hours = parseInt(match[1] || '0');
  const minutes = parseInt(match[2] || '0');
  const seconds = parseInt(match[3] || '0');
  
  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m ${seconds}s`;
  return `${seconds}s`;
}

export function getReplicationStatusDisplay(server: SourceServer): {
  type: 'success' | 'warning' | 'error' | 'info' | 'in-progress';
  text: string;
} {
  const state = server.dataReplicationInfo?.dataReplicationState;
  const lag = server.dataReplicationInfo?.lagDuration;
  
  switch (state) {
    case 'CONTINUOUS':
      return { type: 'success', text: `Healthy${lag ? ` (${formatLagDuration(lag)})` : ''}` };
    case 'INITIAL_SYNC':
      const progress = getReplicationProgress(server);
      return { type: 'in-progress', text: `Initial sync ${progress}%` };
    case 'RESCAN':
      return { type: 'in-progress', text: 'Rescanning' };
    case 'BACKLOG':
      return { type: 'warning', text: 'Backlog' };
    case 'PAUSED':
      return { type: 'warning', text: 'Paused' };
    case 'STALLED':
      return { type: 'error', text: 'Stalled' };
    case 'DISCONNECTED':
      return { type: 'error', text: 'Disconnected' };
    case 'STOPPED':
      return { type: 'error', text: 'Stopped' };
    case 'INITIATING':
      return { type: 'in-progress', text: 'Initiating' };
    case 'CREATING_SNAPSHOT':
      return { type: 'in-progress', text: 'Creating snapshot' };
    default:
      return { type: 'info', text: state || 'Unknown' };
  }
}

export function getLastRecoveryDisplay(server: SourceServer): {
  type: 'success' | 'error' | 'info' | 'in-progress';
  text: string;
  timestamp?: string;
} {
  const result = server.lastLaunchResult;
  const lastLaunch = server.lifeCycle?.lastLaunch;
  
  switch (result) {
    case 'SUCCEEDED':
      return {
        type: 'success',
        text: 'Successful',
        timestamp: lastLaunch?.initiated?.apiCallDateTime,
      };
    case 'FAILED':
      return {
        type: 'error',
        text: 'Failed',
        timestamp: lastLaunch?.initiated?.apiCallDateTime,
      };
    case 'PENDING':
      return { type: 'in-progress', text: 'Pending' };
    case 'NOT_STARTED':
    default:
      return { type: 'info', text: '—' };
  }
}
```

---

## API Endpoints

### New Backend Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/drs/source-servers?region={region}` | List all source servers (enhanced) |
| GET | `/drs/source-servers/{id}?region={region}` | Get single server details |
| GET | `/drs/source-servers/{id}/launch-config?region={region}` | Get launch configuration |
| GET | `/drs/source-servers/{id}/replication-config?region={region}` | Get replication configuration |

### Lambda Handler Updates

```python
# lambda/index.py - Add to existing handler

def get_source_servers_enhanced(event, region):
    """Get all source servers with full details for Source Servers page."""
    drs = boto3.client('drs', region_name=region)
    
    servers = []
    next_token = None
    
    while True:
        params = {
            'maxResults': 200,
            'filters': {'isArchived': False}
        }
        if next_token:
            params['nextToken'] = next_token
        
        response = drs.describe_source_servers(**params)
        servers.extend(response.get('items', []))
        
        next_token = response.get('nextToken')
        if not next_token:
            break
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'servers': servers,
            'count': len(servers)
        })
    }
```

---

## Server Details Page

### Route: `/source-servers/{sourceServerID}`

### Tabs Structure

| Tab | Content |
|-----|---------|
| Overview | Server info, OS, hardware specs, network interfaces |
| Replication | Replication state, disk progress, lag, staging area |
| Launch Settings | EC2 launch template, DRS launch settings |
| Recovery History | Past recovery jobs and results |
| Tags | Server tags management |

### Overview Tab

```typescript
<Container header={<Header variant="h2">Server Information</Header>}>
  <ColumnLayout columns={3} variant="text-grid">
    <div>
      <Box variant="awsui-key-label">Hostname</Box>
      <Box>{server.sourceProperties?.identificationHints?.hostname}</Box>
    </div>
    <div>
      <Box variant="awsui-key-label">Operating System</Box>
      <Box>{server.sourceProperties?.os?.fullString}</Box>
    </div>
    <div>
      <Box variant="awsui-key-label">Source Server ID</Box>
      <Box>{server.sourceServerID}</Box>
    </div>
    <div>
      <Box variant="awsui-key-label">CPUs</Box>
      <Box>{getTotalCores(server)} cores</Box>
    </div>
    <div>
      <Box variant="awsui-key-label">Memory</Box>
      <Box>{formatBytes(server.sourceProperties?.ramBytes)}</Box>
    </div>
    <div>
      <Box variant="awsui-key-label">Total Disk</Box>
      <Box>{formatBytes(getTotalDiskBytes(server))}</Box>
    </div>
  </ColumnLayout>
</Container>
```

### Replication Tab

```typescript
<SpaceBetween size="l">
  <Container header={<Header variant="h2">Replication Status</Header>}>
    <ColumnLayout columns={4} variant="text-grid">
      <div>
        <Box variant="awsui-key-label">State</Box>
        <StatusIndicator type={getStatusType(server)}>
          {server.dataReplicationInfo?.dataReplicationState}
        </StatusIndicator>
      </div>
      <div>
        <Box variant="awsui-key-label">Lag</Box>
        <Box>{formatLagDuration(server.dataReplicationInfo?.lagDuration)}</Box>
      </div>
      <div>
        <Box variant="awsui-key-label">Staging AZ</Box>
        <Box>{server.dataReplicationInfo?.stagingAvailabilityZone}</Box>
      </div>
      <div>
        <Box variant="awsui-key-label">Last Seen</Box>
        <Box>{formatDateTime(server.lifeCycle?.lastSeenByServiceDateTime)}</Box>
      </div>
    </ColumnLayout>
  </Container>
  
  <Container header={<Header variant="h2">Disk Replication</Header>}>
    <Table
      items={server.dataReplicationInfo?.replicatedDisks || []}
      columnDefinitions={diskColumnDefinitions}
    />
  </Container>
</SpaceBetween>
```

---

## Implementation Phases

### Phase 1: Source Servers List Page (1 week)

- [ ] Create `SourceServersPage.tsx` component
- [ ] Add route `/source-servers` to App.tsx
- [ ] Add navigation item to sidebar
- [ ] Implement `useSourceServers` hook with polling
- [ ] Create `ReplicationStatusCell` component
- [ ] Create `LastRecoveryCell` component
- [ ] Add region selector with persistence
- [ ] Implement table filtering and sorting
- [ ] Add auto-refresh (30 seconds)

### Phase 2: Server Details Page (1 week)

- [ ] Create `SourceServerDetailsPage.tsx` component
- [ ] Add route `/source-servers/:id` to App.tsx
- [ ] Implement Overview tab
- [ ] Implement Replication tab with disk progress
- [ ] Implement Launch Settings tab (read-only initially)
- [ ] Implement Recovery History tab
- [ ] Implement Tags tab (read-only initially)

### Phase 3: Backend API Enhancements (3-4 days)

- [ ] Enhance `/drs/source-servers` endpoint with full details
- [ ] Add `/drs/source-servers/{id}` endpoint
- [ ] Add `/drs/source-servers/{id}/launch-config` endpoint
- [ ] Add `/drs/source-servers/{id}/replication-config` endpoint
- [ ] Add pagination support for large server counts

### Phase 4: Actions & Integration (1 week)

- [ ] Add "Initiate Drill" action from server row
- [ ] Add "Initiate Recovery" action from server row
- [ ] Link to existing Protection Groups containing server
- [ ] Add "Add to Protection Group" quick action
- [ ] Implement server selection for bulk operations

---

## Navigation Integration

### Sidebar Update

```typescript
const navigationItems = [
  { type: 'link', text: 'Dashboard', href: '/' },
  { type: 'divider' },
  { type: 'link', text: 'Getting Started', href: '/getting-started' },
  { type: 'link', text: 'Source Servers', href: '/source-servers' },  // NEW
  { type: 'link', text: 'Protection Groups', href: '/protection-groups' },
  { type: 'link', text: 'Recovery Plans', href: '/recovery-plans' },
  { type: 'link', text: 'History', href: '/executions' },
];
```

---

## Testing Plan

### Unit Tests

- [ ] `isReadyForRecovery()` helper function
- [ ] `getReplicationProgress()` calculation
- [ ] `formatLagDuration()` parsing
- [ ] `getReplicationStatusDisplay()` mapping
- [ ] `getLastRecoveryDisplay()` mapping

### Integration Tests

- [ ] Source servers list loads correctly
- [ ] Region switching works
- [ ] Auto-refresh updates data
- [ ] Server details page loads
- [ ] All tabs render correctly

### E2E Tests (Playwright)

- [ ] Navigate to Source Servers page
- [ ] Filter servers by hostname
- [ ] Click server to view details
- [ ] Switch between tabs
- [ ] Verify replication status displays

---

## Dependencies

### Frontend

- Existing CloudScape components
- Existing `RegionSelector` component
- Existing `StatusBadge` component
- New `ReplicationStatusCell` component
- New `LastRecoveryCell` component

### Backend

- Existing DRS client in Lambda
- Existing API Gateway routes
- New endpoints for enhanced server data

---

## Estimated LOE

| Phase | Duration | Resources |
|-------|----------|-----------|
| Phase 1: List Page | 1 week | 1 frontend dev |
| Phase 2: Details Page | 1 week | 1 frontend dev |
| Phase 3: Backend APIs | 3-4 days | 1 backend dev |
| Phase 4: Actions | 1 week | 1 full-stack dev |
| **Total** | **3-4 weeks** | |

---

## References

- [AWS DRS DescribeSourceServers API](https://docs.aws.amazon.com/drs/latest/APIReference/API_DescribeSourceServers.html)
- [AWS DRS GetLaunchConfiguration API](https://docs.aws.amazon.com/drs/latest/APIReference/API_GetLaunchConfiguration.html)
- [AWS DRS GetReplicationConfiguration API](https://docs.aws.amazon.com/drs/latest/APIReference/API_GetReplicationConfiguration.html)
- [DRS Recovery Deep Dive](./DRS_RECOVERY_DEEP_DIVE.md)
- [CloudScape Table Component](https://cloudscape.design/components/table/)
