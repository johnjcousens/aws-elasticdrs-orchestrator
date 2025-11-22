# Session 47: Frontend Execution Visibility - Implementation Plan

**Created**: 2025-11-22
**Status**: Ready for Implementation
**Estimated Time**: 2-3 hours

## Overview

Implement real-time execution visibility in the frontend to show users what's happening when they execute a recovery plan. Users can see launched instance IDs, per-server status, and click through to AWS console.

## Current State Analysis

### ✅ Backend Ready
- **GET /executions/{executionId}** endpoint exists (`get_execution_details()`)
- Returns complete execution structure:
  ```python
  {
    "ExecutionId": "uuid",
    "PlanId": "uuid", 
    "Status": "IN_PROGRESS|COMPLETED|PARTIAL|FAILED",
    "StartTime": timestamp,
    "EndTime": timestamp,
    "Waves": [
      {
        "WaveName": "Wave 1",
        "ProtectionGroupId": "uuid",
        "Region": "us-east-1",
        "Status": "IN_PROGRESS|COMPLETED|PARTIAL",
        "Servers": [
          {
            "SourceServerId": "s-xxx",
            "RecoveryJobId": "job-xxx",
            "InstanceId": "i-xxx" (or null if still launching),
            "Status": "LAUNCHING|LAUNCHED|FAILED",
            "LaunchTime": timestamp,
            "Error": "message" (if failed)
          }
        ]
      }
    ]
  }
  ```

### ✅ Frontend Ready
- **API client** has `getExecution(executionId)` method
- **Types defined**: Execution, WaveExecution, ServerExecution
- **RecoveryPlansPage** calls `executeRecoveryPlan()` and gets executionId back
- **Routing** exists for `/executions` (list view)

### ❌ Missing
1. **ExecutionDetailsPage** component - doesn't exist yet
2. **Route** for `/executions/:executionId` - needs to be added
3. **Navigation** after execution - RecoveryPlansPage doesn't navigate to details
4. **Polling mechanism** - no auto-refresh to see status updates
5. **AWS console links** - no clickable links to instances
6. **Status indicators** - no visual per-server status

## Implementation Tasks

### Task 1: Create ExecutionDetailsPage Component
**File**: `frontend/src/pages/ExecutionDetailsPage.tsx`
**Complexity**: High
**Time**: 45-60 minutes

**Features**:
- Fetch execution details on mount using `apiClient.getExecution(executionId)`
- Display execution metadata (plan name, start time, status)
- Show wave-by-wave breakdown
- Display per-server status with indicators
- Instance ID links to AWS console
- Polling every 10-30 seconds while status is IN_PROGRESS
- Error handling with retry button

**Status Indicators**:
- 🟡 **LAUNCHING** - Recovery job started, instance not yet available
- 🟢 **LAUNCHED** - Instance ID available (show link)
- 🔴 **FAILED** - Show error message

**AWS Console Link Format**:
```typescript
const consoleUrl = `https://console.aws.amazon.com/ec2/v2/home?region=${region}#Instances:instanceId=${instanceId}`;
```

**Component Structure**:
```tsx
<PageTransition>
  <ExecutionHeader execution={execution} />
  <ExecutionTimeline waves={execution.Waves} />
  <WaveAccordions>
    {waves.map(wave => (
      <WaveAccordion key={wave.WaveName}>
        <ServerTable servers={wave.Servers} region={wave.Region} />
      </WaveAccordion>
    ))}
  </WaveAccordions>
</PageTransition>
```

**Polling Logic**:
```typescript
useEffect(() => {
  const interval = setInterval(() => {
    if (execution?.Status === 'IN_PROGRESS') {
      fetchExecution(); // Refresh data
    } else {
      clearInterval(interval); // Stop polling when complete
    }
  }, 15000); // 15 seconds
  
  return () => clearInterval(interval);
}, [execution?.Status]);
```

### Task 2: Add Route to App.tsx
**File**: `frontend/src/App.tsx`
**Complexity**: Low
**Time**: 5 minutes

**Changes**:
```tsx
// Add import
import { ExecutionDetailsPage } from './pages/ExecutionDetailsPage';

// Add route before /executions list route
<Route
  path="/executions/:executionId"
  element={
    <ProtectedRoute>
      <Layout>
        <ExecutionDetailsPage />
      </Layout>
    </ProtectedRoute>
  }
/>
```

### Task 3: Update RecoveryPlansPage Navigation
**File**: `frontend/src/pages/RecoveryPlansPage.tsx`
**Complexity**: Low
**Time**: 10 minutes

**Changes to `handleExecute()`**:
```typescript
import { useNavigate } from 'react-router-dom';

const navigate = useNavigate();

const handleExecute = async (plan: RecoveryPlan) => {
  try {
    const execution = await apiClient.executeRecoveryPlan({
      recoveryPlanId: plan.id,
      dryRun: false,
      executedBy: 'demo-user'
    });
    
    toast.success('Recovery execution started');
    
    // Navigate to execution details
    navigate(`/executions/${execution.executionId}`);
  } catch (err: any) {
    toast.error(err.message || 'Failed to execute recovery plan');
  }
};
```

### Task 4: Update Type Definitions (if needed)
**File**: `frontend/src/types/index.ts`
**Complexity**: Low
**Time**: 10 minutes

**Backend Response Structure** (from Lambda):
```typescript
interface BackendExecution {
  ExecutionId: string;
  PlanId: string;
  ExecutionType: 'DRILL' | 'RECOVERY' | 'FAILBACK';
  Status: 'IN_PROGRESS' | 'COMPLETED' | 'PARTIAL' | 'FAILED';
  StartTime: number;
  EndTime?: number;
  InitiatedBy: string;
  Waves: Array<{
    WaveName: string;
    ProtectionGroupId: string;
    Region: string;
    Status: string;
    Servers: Array<{
      SourceServerId: string;
      RecoveryJobId?: string;
      InstanceId?: string;
      Status: 'LAUNCHING' | 'LAUNCHED' | 'FAILED';
      LaunchTime: number;
      Error?: string;
    }>;
    StartTime: number;
    EndTime?: number;
  }>;
  RecoveryPlanName?: string;  // Added by get_execution_details
}
```

**May need to update frontend types to match backend PascalCase format.**

### Task 5: Create Reusable Components
**Complexity**: Medium
**Time**: 30 minutes

**Components to create**:

1. **ServerStatusChip** (`frontend/src/components/ServerStatusChip.tsx`)
   - Props: status ('LAUNCHING' | 'LAUNCHED' | 'FAILED')
   - Renders colored chip with emoji

2. **InstanceLink** (`frontend/src/components/InstanceLink.tsx`)
   - Props: instanceId, region
   - Renders clickable link to AWS console
   - Opens in new tab

3. **ExecutionTimeline** (`frontend/src/components/ExecutionTimeline.tsx`)
   - Props: waves, currentWave
   - Visual progress indicator showing wave completion

### Task 6: Testing
**Complexity**: Medium
**Time**: 30 minutes

**Manual Test Scenarios**:
1. Execute a recovery plan
2. Verify navigation to /executions/{id}
3. Verify polling updates status every 15 seconds
4. Verify instance links work (open in new tab)
5. Verify status indicators display correctly
6. Test with failed server scenario
7. Test with partial success scenario

**Test Checklist**:
- [ ] Page loads after execution
- [ ] Execution metadata displays correctly
- [ ] Waves display in order
- [ ] Servers show correct status
- [ ] Instance links work
- [ ] Polling updates data
- [ ] Polling stops when complete
- [ ] Error states handled gracefully
- [ ] Back button works

## Backend Response Example

```json
{
  "ExecutionId": "abc-123",
  "PlanId": "plan-456",
  "ExecutionType": "DRILL",
  "Status": "IN_PROGRESS",
  "StartTime": 1700000000,
  "InitiatedBy": "demo-user",
  "RecoveryPlanName": "Production DR Plan",
  "Waves": [
    {
      "WaveName": "Database Tier",
      "ProtectionGroupId": "pg-123",
      "Region": "us-east-1",
      "Status": "COMPLETED",
      "Servers": [
        {
          "SourceServerId": "s-abc123",
          "RecoveryJobId": "job-xyz789",
          "InstanceId": "i-0a1b2c3d4e5f",
          "Status": "LAUNCHED",
          "LaunchTime": 1700000100,
          "Error": null
        }
      ],
      "StartTime": 1700000100,
      "EndTime": 1700000300
    },
    {
      "WaveName": "Application Tier",
      "ProtectionGroupId": "pg-456",
      "Region": "us-east-1",
      "Status": "IN_PROGRESS",
      "Servers": [
        {
          "SourceServerId": "s-def456",
          "RecoveryJobId": "job-abc123",
          "InstanceId": null,
          "Status": "LAUNCHING",
          "LaunchTime": 1700000400,
          "Error": null
        },
        {
          "SourceServerId": "s-ghi789",
          "RecoveryJobId": "job-def456",
          "InstanceId": "i-1a2b3c4d5e6f",
          "Status": "LAUNCHED",
          "LaunchTime": 1700000410,
          "Error": null
        }
      ],
      "StartTime": 1700000400,
      "EndTime": null
    }
  ]
}
```

## UI Mockup

```
┌─────────────────────────────────────────────────────────┐
│ Execution Details                                        │
│ ← Back to Recovery Plans                                │
├─────────────────────────────────────────────────────────┤
│ Production DR Plan - Drill Execution                     │
│ Status: IN PROGRESS 🟡                                   │
│ Started: 2 minutes ago by demo-user                      │
│ Duration: 5 minutes                                      │
├─────────────────────────────────────────────────────────┤
│ Wave Progress: 1 of 2 complete                          │
│ ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░ 50%                              │
├─────────────────────────────────────────────────────────┤
│ ▼ Wave 1: Database Tier - COMPLETED ✓                  │
│   Region: us-east-1                                      │
│   ┌───────────────────────────────────────────────────┐ │
│   │ Server ID       Status     Instance ID            │ │
│   ├───────────────────────────────────────────────────┤ │
│   │ s-abc123       🟢 LAUNCHED  i-0a1b2c3d4e5f 🔗    │ │
│   └───────────────────────────────────────────────────┘ │
│                                                          │
│ ▼ Wave 2: Application Tier - IN PROGRESS 🟡            │
│   Region: us-east-1                                      │
│   ┌───────────────────────────────────────────────────┐ │
│   │ Server ID       Status      Instance ID           │ │
│   ├───────────────────────────────────────────────────┤ │
│   │ s-def456       🟡 LAUNCHING  -                    │ │
│   │ s-ghi789       🟢 LAUNCHED   i-1a2b3c4d5e6f 🔗   │ │
│   └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

Auto-refreshing every 15 seconds...
```

## Implementation Order

1. ✅ **Prerequisites** - Analysis complete
2. **Create ExecutionDetailsPage** - Core component
3. **Add Route** - Enable navigation
4. **Update RecoveryPlansPage** - Add navigation after execution
5. **Create Sub-components** - ServerStatusChip, InstanceLink, etc.
6. **Testing** - Manual verification
7. **Documentation** - Update README and PROJECT_STATUS

## Success Criteria

- ✅ User clicks Execute, sees execution details page immediately
- ✅ Page polls every 15 seconds while execution in progress
- ✅ User sees per-server status with visual indicators
- ✅ User can click instance IDs to open AWS console
- ✅ Polling stops automatically when execution completes
- ✅ Error states display clearly with helpful messages
- ✅ Page is responsive and loads quickly

## Risk Mitigation

**Risk**: Backend response format differs from frontend types
**Mitigation**: Transform backend PascalCase to frontend camelCase in API client

**Risk**: Polling causes performance issues
**Mitigation**: Use 15-30 second intervals, stop when complete

**Risk**: Instance ID not immediately available
**Mitigation**: Show "Launching..." status, refresh until available

**Risk**: Multiple waves with many servers cause UI overload
**Mitigation**: Use accordions/collapse to show waves one at a time

## Next Steps After Session 47

- **Session 48**: Enhanced execution visualization (charts, graphs)
- **Session 49**: Execution history page improvements
- **Session 50**: Export execution reports
