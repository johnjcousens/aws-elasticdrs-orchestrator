# DRS Tag Synchronization - UI Integration Implementation Plan

## Executive Summary

Integrate the archived DRS tag synchronization tool into the orchestration UI, enabling users to synchronize EC2 instance tags and instance types to DRS source servers through a visual interface with on-demand and scheduled sync capabilities.

## Problem Statement

The archived `drs-synch-ec2-tags-and-instance-type` solution provides automated tag and instance type synchronization via EventBridge scheduled rules, but lacks:
- Visual interface for on-demand synchronization
- Per-server sync control and status visibility
- Integration with Protection Group workflows
- Real-time sync progress monitoring
- Sync history and audit trail

## Proposed Solution

### Architecture Overview

```
Frontend (React)
    ↓
API Gateway → Lambda (api-handler)
    ↓
Lambda (drs-tag-sync) → DRS API
    ↓                    ↓
DynamoDB (sync-history) EC2 API
```

### Core Features

1. **On-Demand Sync**: Trigger tag/instance type sync from UI
2. **Bulk Operations**: Sync all servers in a Protection Group or region
3. **Selective Sync**: Choose to sync tags only, instance types only, or both
4. **Sync History**: Track all sync operations with timestamps and results
5. **Real-Time Status**: Monitor sync progress with server-level details
6. **Scheduled Sync**: Configure automatic sync schedules per region

## Implementation Plan

### Phase 1: Backend Infrastructure (Week 1)

#### 1.1 DynamoDB Table for Sync History

**Table**: `drs-tag-sync-history-{env}`

| Attribute | Type | Description |
|-----------|------|-------------|
| SyncId (PK) | String | Unique sync operation ID |
| Timestamp (SK) | Number | Unix timestamp |
| Region | String | AWS region |
| SyncType | String | `tags`, `instance-type`, `both` |
| Status | String | `PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED` |
| TotalServers | Number | Total servers to sync |
| SuccessCount | Number | Successfully synced servers |
| FailureCount | Number | Failed servers |
| ServerResults | Map | Per-server sync results |
| InitiatedBy | String | User email |
| CompletedAt | Number | Completion timestamp |

**GSI**: `RegionIndex` (Region as PK, Timestamp as SK)

#### 1.2 Lambda Function: `drs-tag-sync`

**Purpose**: Execute tag and instance type synchronization

**Handler**: `lambda/drs_tag_sync.py`

**Key Functions**:
```python
def sync_tags_and_instance_types(event, context):
    """
    Main handler for tag/instance type sync
    
    Event payload:
    {
        "region": "us-east-1",
        "syncType": "both",  # tags | instance-type | both
        "serverIds": ["s-1234", "s-5678"],  # optional, all if not specified
        "protectionGroupId": "pg-123"  # optional, sync all servers in PG
    }
    """
    
def sync_server_tags(drs_client, ec2_client, source_server_id, instance_id):
    """Sync tags from EC2 instance to DRS source server"""
    
def sync_server_instance_type(drs_client, ec2_client, source_server_id, instance_id, instance_type):
    """Update DRS launch template with EC2 instance type"""
```

**Environment Variables**:
- `TAG_SYNC_HISTORY_TABLE`: DynamoDB table name
- `PROTECTION_GROUPS_TABLE`: Existing PG table

**IAM Permissions**:
```yaml
- drs:DescribeSourceServers
- drs:TagResource
- drs:UpdateLaunchConfiguration
- drs:GetLaunchConfiguration
- ec2:DescribeInstances
- ec2:DescribeLaunchTemplateVersions
- ec2:CreateLaunchTemplateVersion
- ec2:ModifyLaunchTemplate
- dynamodb:PutItem
- dynamodb:UpdateItem
- dynamodb:Query
```

#### 1.3 API Endpoints

**POST /drs/sync-tags**
```json
{
  "region": "us-east-1",
  "syncType": "both",
  "serverIds": ["s-1234"],
  "protectionGroupId": "pg-123"
}
```

**Response**:
```json
{
  "syncId": "sync-abc123",
  "status": "IN_PROGRESS",
  "message": "Tag sync initiated for 5 servers"
}
```

**GET /drs/sync-history?region={region}&limit={limit}**

**Response**:
```json
{
  "items": [
    {
      "syncId": "sync-abc123",
      "timestamp": 1234567890,
      "region": "us-east-1",
      "syncType": "both",
      "status": "COMPLETED",
      "totalServers": 5,
      "successCount": 5,
      "failureCount": 0,
      "initiatedBy": "admin@example.com"
    }
  ]
}
```

**GET /drs/sync-status/{syncId}**

**Response**:
```json
{
  "syncId": "sync-abc123",
  "status": "COMPLETED",
  "totalServers": 5,
  "successCount": 5,
  "failureCount": 0,
  "serverResults": {
    "s-1234": {
      "status": "SUCCESS",
      "tagsSynced": 12,
      "instanceTypeUpdated": true,
      "message": "Synced successfully"
    }
  }
}
```

### Phase 2: Frontend UI Components (Week 2)

#### 2.1 DRS Settings Page

**Location**: `frontend/src/pages/DRSSettingsPage.tsx`

**Features**:
- Configure sync schedules per region
- View sync history
- Trigger bulk sync operations

**UI Layout**:
```
┌─────────────────────────────────────────┐
│ DRS Tag Synchronization Settings       │
├─────────────────────────────────────────┤
│ [Region Selector: us-east-1 ▼]         │
│                                         │
│ Sync Configuration                      │
│ ┌─────────────────────────────────────┐ │
│ │ ☑ Sync Tags                         │ │
│ │ ☑ Sync Instance Types               │ │
│ │                                     │ │
│ │ Schedule: [Daily ▼] at [02:00 ▼]   │ │
│ │                                     │ │
│ │ [Save Schedule] [Sync Now]         │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Sync History                            │
│ ┌─────────────────────────────────────┐ │
│ │ Date       | Type | Status | Servers│ │
│ │ 2025-01-15 | Both | ✓      | 5/5    │ │
│ │ 2025-01-14 | Tags | ✓      | 3/3    │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

#### 2.2 Protection Group Sync Action

**Location**: `frontend/src/pages/ProtectionGroupDetailsPage.tsx`

**Add Button**: "Sync Tags & Instance Types"

**Modal Dialog**:
```
┌─────────────────────────────────────────┐
│ Sync Tags & Instance Types              │
├─────────────────────────────────────────┤
│ Protection Group: DB-Primary            │
│ Region: us-east-1                       │
│ Servers: 3                              │
│                                         │
│ Sync Options:                           │
│ ☑ Sync EC2 tags to DRS source servers  │
│ ☑ Update DRS instance types             │
│                                         │
│ This will:                              │
│ • Copy all EC2 tags to DRS servers     │
│ • Add source:* metadata tags           │
│ • Update launch template instance types│
│ • Disable right-sizing                 │
│                                         │
│ [Cancel] [Sync Now]                    │
└─────────────────────────────────────────┘
```

#### 2.3 Server List Sync Status

**Location**: `frontend/src/pages/ProtectionGroupDetailsPage.tsx`

**Add Column**: "Tag Sync Status"

**Status Indicators**:
- 🟢 Synced (< 24 hours ago)
- 🟡 Stale (> 24 hours ago)
- 🔴 Never synced
- ⏳ Syncing...

**Tooltip**: Shows last sync timestamp and details

#### 2.4 Sync Progress Modal

**Real-Time Progress Display**:
```
┌─────────────────────────────────────────┐
│ Syncing Tags & Instance Types           │
├─────────────────────────────────────────┤
│ Progress: 3/5 servers completed         │
│ [████████████░░░░░░░░] 60%             │
│                                         │
│ ✓ i-1234 (db-primary-1)                │
│ ✓ i-5678 (db-primary-2)                │
│ ⏳ i-9012 (db-primary-3) - In progress │
│ ⏸ i-3456 (db-primary-4) - Pending     │
│ ⏸ i-7890 (db-primary-5) - Pending     │
│                                         │
│ [Close]                                 │
└─────────────────────────────────────────┘
```

### Phase 3: Integration & Testing (Week 3)

#### 3.1 CloudFormation Updates

**Add to `cfn/database-stack.yaml`**:
```yaml
TagSyncHistoryTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: !Sub '${ProjectName}-tag-sync-history-${Environment}'
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: SyncId
        AttributeType: S
      - AttributeName: Timestamp
        AttributeType: N
      - AttributeName: Region
        AttributeType: S
    KeySchema:
      - AttributeName: SyncId
        KeyType: HASH
      - AttributeName: Timestamp
        KeyType: RANGE
    GlobalSecondaryIndexes:
      - IndexName: RegionIndex
        KeySchema:
          - AttributeName: Region
            KeyType: HASH
          - AttributeName: Timestamp
            KeyType: RANGE
        Projection:
          ProjectionType: ALL
```

**Add to `cfn/lambda-stack.yaml`**:
```yaml
DRSTagSyncFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: !Sub '${ProjectName}-drs-tag-sync-${Environment}'
    Runtime: python3.12
    Handler: drs_tag_sync.handler
    Code:
      S3Bucket: !Ref SourceBucket
      S3Key: lambda/drs-tag-sync.zip
    Environment:
      Variables:
        TAG_SYNC_HISTORY_TABLE: !Ref TagSyncHistoryTable
        PROTECTION_GROUPS_TABLE: !Ref ProtectionGroupsTable
    Role: !GetAtt DRSTagSyncRole.Arn
```

#### 3.2 API Gateway Routes

**Add to `cfn/api-stack.yaml`**:
```yaml
/drs/sync-tags:
  post:
    x-amazon-apigateway-integration:
      uri: !Sub 'arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ApiHandlerFunction.Arn}/invocations'

/drs/sync-history:
  get:
    x-amazon-apigateway-integration:
      uri: !Sub 'arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ApiHandlerFunction.Arn}/invocations'

/drs/sync-status/{syncId}:
  get:
    x-amazon-apigateway-integration:
      uri: !Sub 'arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ApiHandlerFunction.Arn}/invocations'
```

#### 3.3 Testing Strategy

**Unit Tests** (`tests/python/unit/test_drs_tag_sync.py`):
- Test tag extraction from EC2 instances
- Test DRS source server tag updates
- Test instance type synchronization
- Test launch template version creation
- Test error handling for missing servers

**Integration Tests** (`tests/python/integration/test_drs_tag_sync_integration.py`):
- Test end-to-end sync with mock DRS/EC2 APIs
- Test sync history recording
- Test bulk sync operations
- Test Protection Group integration

**E2E Tests** (`tests/playwright/drs-tag-sync.spec.ts`):
- Test sync from Protection Group details page
- Test sync progress monitoring
- Test sync history display
- Test DRS Settings page configuration

### Phase 4: Documentation & Deployment (Week 4)

#### 4.1 User Documentation

**Add to `docs/guides/DRS_TAG_SYNC_GUIDE.md`**:
- Feature overview and benefits
- Step-by-step sync instructions
- Scheduled sync configuration
- Troubleshooting common issues
- IAM permission requirements

#### 4.2 Deployment Guide

**Update `docs/guides/DEPLOYMENT_AND_OPERATIONS_GUIDE.md`**:
- New DynamoDB table deployment
- New Lambda function deployment
- API Gateway route updates
- IAM permission updates

#### 4.3 README Updates

**Add to Future Enhancements**:
- Mark as "Completed" with link to guide

## Technical Specifications

### Lambda Function Structure

**File**: `lambda/drs_tag_sync.py`

```python
"""
DRS Tag Synchronization Lambda
Syncs EC2 instance tags and instance types to DRS source servers
"""

import boto3
import json
import time
from typing import Dict, List, Any
from os import environ

dynamodb = boto3.resource('dynamodb')
tag_sync_history_table = dynamodb.Table(environ['TAG_SYNC_HISTORY_TABLE'])

def handler(event: Dict, context: Any) -> Dict:
    """Main handler for tag sync operations"""
    
def sync_protection_group(pg_id: str, region: str, sync_type: str) -> Dict:
    """Sync all servers in a Protection Group"""
    
def sync_servers(server_ids: List[str], region: str, sync_type: str) -> Dict:
    """Sync specific servers"""
    
def sync_single_server(drs_client, ec2_client, source_server_id: str, sync_type: str) -> Dict:
    """Sync tags and/or instance type for a single server"""
    
def get_ec2_instance_details(ec2_client, instance_id: str) -> Dict:
    """Get EC2 instance tags and instance type"""
    
def update_drs_tags(drs_client, source_server_id: str, tags: Dict) -> bool:
    """Update DRS source server tags"""
    
def update_drs_instance_type(drs_client, ec2_client, source_server_id: str, instance_type: str) -> bool:
    """Update DRS launch template instance type"""
    
def record_sync_history(sync_id: str, results: Dict) -> None:
    """Record sync operation in DynamoDB"""
```

### Frontend Service

**File**: `frontend/src/services/drsTagSyncService.ts`

```typescript
export interface SyncRequest {
  region: string;
  syncType: 'tags' | 'instance-type' | 'both';
  serverIds?: string[];
  protectionGroupId?: string;
}

export interface SyncHistoryItem {
  syncId: string;
  timestamp: number;
  region: string;
  syncType: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
  totalServers: number;
  successCount: number;
  failureCount: number;
  initiatedBy: string;
}

export const syncTagsAndInstanceTypes = async (request: SyncRequest): Promise<string> => {
  // POST /drs/sync-tags
};

export const getSyncHistory = async (region?: string, limit?: number): Promise<SyncHistoryItem[]> => {
  // GET /drs/sync-history
};

export const getSyncStatus = async (syncId: string): Promise<SyncHistoryItem> => {
  // GET /drs/sync-status/{syncId}
};
```

### React Components

**File**: `frontend/src/components/DRSTagSyncModal.tsx`

```typescript
interface DRSTagSyncModalProps {
  visible: boolean;
  onDismiss: () => void;
  protectionGroupId?: string;
  region: string;
  serverIds?: string[];
}

export const DRSTagSyncModal: React.FC<DRSTagSyncModalProps> = ({
  visible,
  onDismiss,
  protectionGroupId,
  region,
  serverIds
}) => {
  const [syncType, setSyncType] = useState<'tags' | 'instance-type' | 'both'>('both');
  const [syncing, setSyncing] = useState(false);
  const [progress, setProgress] = useState<SyncProgress | null>(null);
  
  // Component implementation
};
```

## Benefits

### For Users
- **Visual Control**: Trigger sync operations from UI without CLI commands
- **Real-Time Feedback**: Monitor sync progress with server-level details
- **Audit Trail**: Complete history of all sync operations
- **Bulk Operations**: Sync entire Protection Groups with one click
- **Flexible Scheduling**: Configure automatic sync per region

### For Operations
- **Reduced Manual Work**: Automated tag propagation from EC2 to DRS
- **Consistency**: Ensures DRS tags match source EC2 instances
- **Cost Tracking**: Preserves cost allocation tags in DR environment
- **Right-Sizing Control**: Maintains exact instance types in DR

### For Compliance
- **Audit Trail**: Complete history of tag synchronization operations
- **Metadata Tracking**: Automatic source:* tags for traceability
- **Scheduled Compliance**: Regular sync ensures tag consistency

## Cost Estimate

| Component | Monthly Cost |
|-----------|--------------|
| DynamoDB (sync history) | $1-2 |
| Lambda (sync operations) | $1-3 |
| API Gateway (sync endpoints) | <$1 |
| **Total Additional** | **$2-6/month** |

## Migration from Archived Solution

### Key Differences

| Archived Solution | New UI-Integrated Solution |
|-------------------|----------------------------|
| EventBridge scheduled only | On-demand + scheduled |
| No visibility into sync status | Real-time progress monitoring |
| No per-server control | Selective server sync |
| No audit trail | Complete sync history |
| CLI deployment only | UI-driven operations |

### Preserved Functionality

✅ Tag synchronization from EC2 to DRS  
✅ Instance type synchronization  
✅ source:* metadata tags  
✅ Launch template updates  
✅ Right-sizing disable  
✅ Cross-account support (future)  

## Future Enhancements

1. **Cross-Account Sync**: Sync tags across multiple AWS accounts
2. **Tag Filtering**: Selective tag sync with include/exclude patterns
3. **Conflict Resolution**: Handle tag conflicts with merge strategies
4. **Sync Validation**: Pre-sync validation and dry-run mode
5. **Webhook Notifications**: SNS notifications for sync completion
6. **Scheduled Sync UI**: Visual cron expression builder

## Success Metrics

- Sync operation completion time < 30 seconds for 10 servers
- UI response time < 2 seconds for sync initiation
- 100% tag accuracy between EC2 and DRS
- Zero manual CLI operations required
- 95%+ user satisfaction with sync workflow

## Rollback Plan

1. Remove new API routes from API Gateway
2. Delete DRSTagSyncFunction Lambda
3. Delete TagSyncHistoryTable DynamoDB table
4. Revert frontend components
5. Restore archived solution if needed

**Rollback Time**: < 30 minutes

## Implementation Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1: Backend | 1 week | Lambda function, DynamoDB table, API endpoints |
| Phase 2: Frontend | 1 week | React components, sync modal, settings page |
| Phase 3: Testing | 1 week | Unit tests, integration tests, E2E tests |
| Phase 4: Documentation | 1 week | User guide, deployment guide, README updates |
| **Total** | **4 weeks** | **Production-ready feature** |

## Conclusion

This implementation plan transforms the archived EventBridge-scheduled tag sync tool into a fully integrated UI feature with on-demand sync, real-time monitoring, and complete audit trails. The solution maintains all core functionality while adding visual control, bulk operations, and sync history tracking.

**Recommended Next Steps**:
1. Review and approve implementation plan
2. Create feature branch: `feature/drs-tag-sync-ui-integration`
3. Begin Phase 1: Backend infrastructure
4. Deploy to dev environment for testing
5. Gather user feedback and iterate
