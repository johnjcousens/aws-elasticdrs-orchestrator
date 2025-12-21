# ExecutionDetailsPage.tsx - Pending Changes

File: `frontend/src/pages/ExecutionDetailsPage.tsx`
Current state: Clean working version from commit 779ab48

## Changes Needed

### 1. Add 'cancelling' status to polling list (~line 96-97)

In the `isActive` check inside the polling useEffect, add:
```typescript
execution.status === 'cancelling' ||
(execution.status as string) === 'CANCELLING' ||
```

### 2. Prevent cancel if already cancelling (~line 406)

Update the `canCancel` logic to exclude cancelling status:
```typescript
) && !(
  execution.status === 'cancelling' ||
  (execution.status as string) === 'CANCELLING'
);
```

### 3. Pass execution status/endTime to WaveProgress (~line 765)

Add these props to the WaveProgress component:
```typescript
executionStatus={execution.status}
executionEndTime={execution.endTime}
```

## Why These Changes

- **Change 1**: Keeps polling active while execution is being cancelled so UI updates when DRS jobs finish
- **Change 2**: Prevents user from clicking Cancel again while cancellation is in progress  
- **Change 3**: Allows WaveProgress to cap wave durations when execution ends (cancelled/completed)
