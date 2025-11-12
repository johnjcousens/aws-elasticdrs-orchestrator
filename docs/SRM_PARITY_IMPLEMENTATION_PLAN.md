# SRM Parity Implementation Plan

**Date**: November 12, 2025  
**Version**: 1.0  
**Status**: Ready for Implementation

## [Overview]

Refactor Recovery Plan architecture to match VMware Site Recovery Manager (SRM) behavior exactly.

This implementation restructures how Protection Groups and servers are selected in Recovery Plans. Currently, our system allows selecting Protection Groups per wave and cherry-picking individual servers from those groups. VMware SRM treats Protection Groups as atomic units selected at the Recovery Plan level, with Waves (Priorities) controlling only the timing and boot order.

The core philosophy change: **Protection Groups are the unit of recovery. Waves control the sequence.**

Key changes:
1. Move Protection Group selection from wave-level to plan-level
2. Remove individual server selection (treat PGs as atomic units)
3. Add per-server boot order and delay configuration within waves
4. Assign complete Protection Groups to waves (no cherry-picking)
5. Display all servers from assigned PGs (read-only list)

## [Types]

TypeScript interface modifications for SRM-compliant data structures.

```typescript
// frontend/src/types/index.ts

// Updated Wave interface - add boot configuration
export interface Wave {
  waveNumber: number;
  name: string;
  description?: string;
  protectionGroupIds: string[];  // PGs assigned to this wave
  serverIds: string[];  // Auto-populated from assigned PGs (read-only)
  executionType: 'sequential' | 'parallel';
  dependsOnWaves?: number[];
  
  // NEW: Per-server boot configuration
  bootOrder?: Record<string, number>;  // serverId -> boot order (1, 2, 3...)
  bootDelays?: Record<string, number>; // serverId -> delay in seconds
  
  // DEPRECATED: Remove these
  // protectionGroupId: string;  // Old single PG field
}

// Updated RecoveryPlan interface - PGs at plan level
export interface RecoveryPlan {
  id: string;
  name: string;
  description?: string;
  
  // NEW: Protection Groups selected at plan level
  protectionGroupIds: string[];
  
  waves: Wave[];
  createdAt: string;
  updatedAt: string;
  owner: string;
  
  // DEPRECATED: Remove these
  // protectionGroupId?: string;  // Old plan-level single PG
}

// New interface for boot configuration UI
export interface ServerBootConfig {
  serverId: string;
  serverName: string;
  bootOrder: number;
  bootDelay: number;
}
```

## [Files]

Detailed file modifications and new files to be created.

### Modified Files:

**1. frontend/src/types/index.ts**
- Purpose: Update type definitions for SRM parity
- Changes:
  - Add `bootOrder` and `bootDelays` to Wave interface
  - Add `protectionGroupIds` array to RecoveryPlan interface
  - Remove deprecated single PG fields
  - Add `ServerBootConfig` interface

**2. frontend/src/components/RecoveryPlanDialog.tsx**
- Purpose: Add Protection Group selection at plan level
- Changes:
  - Add `selectedProtectionGroups` state variable
  - Add Autocomplete multi-select for Protection Groups (top of dialog)
  - Pass selected PG IDs to WaveConfigEditor
  - Update create/update API calls to include plan-level PG IDs
  - Add validation: at least one PG must be selected
  - Remove PG selection from wave creation logic

**3. frontend/src/components/WaveConfigEditor.tsx**
- Purpose: Refactor to assign PGs to waves, remove server picking
- Changes:
  - Remove Protection Group Autocomplete per wave
  - Remove ServerSelector component import and usage
  - Add new prop: `availableProtectionGroups: ProtectionGroup[]`
  - Add UI: Assign PGs to wave (dropdown or multi-select)
  - Add UI: Display servers from assigned PGs (read-only list with checkboxes showing inclusion)
  - Add UI: Boot order configuration (drag-to-reorder list)
  - Add UI: Boot delay input fields per server
  - Add validation: PG can only be assigned to one wave
  - Update wave data structure when PGs assigned
  - Auto-populate `serverIds` from assigned PGs

**4. frontend/src/services/api.ts**
- Purpose: Update API calls for new data structure
- Changes:
  - Modify `createRecoveryPlan` to send plan-level `protectionGroupIds`
  - Modify `updateRecoveryPlan` to send plan-level `protectionGroupIds`
  - Ensure wave boot order/delays are included in payload
  - Handle response transformation for backward compatibility

**5. lambda/index.py**
- Purpose: Update backend to handle new structure
- Changes:
  - Update `create_recovery_plan` handler to accept plan-level PG IDs
  - Update `update_recovery_plan` handler to accept plan-level PG IDs
  - Store `bootOrder` and `bootDelays` in DynamoDB
  - Add validation: each PG only in one wave
  - Update `list_recovery_plans` to return plan-level PG IDs
  - Maintain backward compatibility with old data format

**6. lambda/orchestration/drs_orchestrator.py** (if exists)
- Purpose: Update orchestration to respect boot order/delays
- Changes:
  - Sort servers within wave by `bootOrder` field
  - Apply `bootDelay` timing between server launches
  - Handle sequential vs parallel execution with boot order

### New Files:

**1. frontend/src/components/BootOrderEditor.tsx**
- Purpose: Dedicated component for configuring boot order
- Content:
  - Drag-and-drop list for reordering servers
  - Input fields for boot delays
  - Visual feedback for ordering
  - Export/import functions for testing

**2. frontend/src/components/ProtectionGroupAssignment.tsx**
- Purpose: Component for assigning PGs to waves
- Content:
  - Dropdown showing available (unassigned) PGs
  - Display currently assigned PGs
  - Validation for duplicate assignments
  - Clear visual feedback

## [Functions]

Detailed function modifications and new functions.

### Modified Functions:

**1. RecoveryPlanDialog.tsx - Component**
```typescript
// NEW: Add state for plan-level PG selection
const [selectedProtectionGroupIds, setSelectedProtectionGroupIds] = useState<string[]>([]);

// NEW: Validation function
const validateProtectionGroups = (): boolean => {
  if (selectedProtectionGroupIds.length === 0) {
    setErrors(prev => ({ ...prev, protectionGroups: 'Select at least one Protection Group' }));
    return false;
  }
  return true;
};

// MODIFIED: handleSubmit
const handleSubmit = async () => {
  if (!validate() || !validateProtectionGroups()) return;
  
  const payload = {
    PlanName: name,
    Description: description,
    ProtectionGroupIds: selectedProtectionGroupIds,  // NEW: Plan-level PGs
    Waves: waves.map((wave, index) => ({
      // ... existing wave fields ...
      BootOrder: wave.bootOrder || {},      // NEW
      BootDelays: wave.bootDelays || {}     // NEW
    }))
  };
  
  // ... rest of submit logic
};
```

**2. WaveConfigEditor.tsx - Component**
```typescript
// NEW: Props interface
interface WaveConfigEditorProps {
  waves: Wave[];
  availableProtectionGroups: ProtectionGroup[];  // NEW: From plan level
  onChange: (waves: Wave[]) => void;
  readonly?: boolean;
}

// NEW: Get PGs available for assignment (not already assigned)
const getUnassignedProtectionGroups = (currentWaveNumber: number): ProtectionGroup[] => {
  const assignedPgIds = new Set(
    waves.flatMap(w => w.waveNumber !== currentWaveNumber ? w.protectionGroupIds : [])
  );
  return availableProtectionGroups.filter(pg => !assignedPgIds.has(pg.protectionGroupId));
};

// NEW: Handle PG assignment to wave
const handleAssignProtectionGroup = (waveNumber: number, pgId: string) => {
  const pg = availableProtectionGroups.find(p => p.protectionGroupId === pgId);
  if (!pg) return;
  
  const updatedWaves = waves.map(w => {
    if (w.waveNumber === waveNumber) {
      const newPgIds = [...w.protectionGroupIds, pgId];
      const newServerIds = getServersFromProtectionGroups(newPgIds);
      return {
        ...w,
        protectionGroupIds: newPgIds,
        serverIds: newServerIds,
        // Initialize boot order/delays for new servers
        bootOrder: { ...w.bootOrder, ...initializeBootOrder(pg.sourceServerIds) },
        bootDelays: { ...w.bootDelays, ...initializeBootDelays(pg.sourceServerIds) }
      };
    }
    return w;
  });
  onChange(updatedWaves);
};

// NEW: Initialize boot order for servers
const initializeBootOrder = (serverIds: string[]): Record<string, number> => {
  return serverIds.reduce((acc, serverId, index) => {
    acc[serverId] = index + 1;
    return acc;
  }, {} as Record<string, number>);
};

// NEW: Initialize boot delays (all zero by default)
const initializeBootDelays = (serverIds: string[]): Record<string, number> => {
  return serverIds.reduce((acc, serverId) => {
    acc[serverId] = 0;
    return acc;
  }, {} as Record<string, number>);
};

// NEW: Update boot order for a server
const handleBootOrderChange = (waveNumber: number, serverId: string, newOrder: number) => {
  const updatedWaves = waves.map(w => {
    if (w.waveNumber === waveNumber) {
      return {
        ...w,
        bootOrder: { ...w.bootOrder, [serverId]: newOrder }
      };
    }
    return w;
  });
  onChange(updatedWaves);
};

// NEW: Update boot delay for a server
const handleBootDelayChange = (waveNumber: number, serverId: string, delay: number) => {
  const updatedWaves = waves.map(w => {
    if (w.waveNumber === waveNumber) {
      return {
        ...w,
        bootDelays: { ...w.bootDelays, [serverId]: delay }
      };
    }
    return w;
  });
  onChange(updatedWaves);
};
```

**3. lambda/index.py - create_recovery_plan**
```python
def create_recovery_plan(event, context):
    body = json.loads(event['body'])
    
    # NEW: Extract plan-level Protection Group IDs
    protection_group_ids = body.get('ProtectionGroupIds', [])
    
    # Validate: PGs exist and user has access
    for pg_id in protection_group_ids:
        pg = table.get_item(Key={'protectionGroupId': pg_id}).get('Item')
        if not pg:
            return error_response(404, f'Protection Group {pg_id} not found')
    
    # NEW: Validate waves don't duplicate PG assignments
    wave_pg_assignments = {}
    for wave in body.get('Waves', []):
        for pg_id in wave.get('ProtectionGroupIds', []):
            if pg_id in wave_pg_assignments:
                return error_response(400, 
                    f'Protection Group {pg_id} assigned to multiple waves')
            wave_pg_assignments[pg_id] = wave['WaveId']
    
    item = {
        'recoveryPlanId': str(uuid.uuid4()),
        'name': body['PlanName'],
        'description': body.get('Description', ''),
        'protectionGroupIds': protection_group_ids,  # NEW
        'waves': [
            {
                'waveNumber': idx,
                'name': wave['WaveName'],
                'protectionGroupIds': wave.get('ProtectionGroupIds', []),
                'serverIds': wave.get('ServerIds', []),
                'bootOrder': wave.get('BootOrder', {}),  # NEW
                'bootDelays': wave.get('BootDelays', {}),  # NEW
                'executionType': wave.get('ExecutionType', 'sequential'),
                'dependsOnWaves': wave.get('Dependencies', [])
            }
            for idx, wave in enumerate(body.get('Waves', []))
        ],
        'createdAt': datetime.utcnow().isoformat(),
        'updatedAt': datetime.utcnow().isoformat()
    }
    
    table.put_item(Item=item)
    return success_response(item, 201)
```

### New Functions:

**1. BootOrderEditor.tsx - Component**
```typescript
interface BootOrderEditorProps {
  servers: Array<{ serverId: string; serverName: string }>;
  bootOrder: Record<string, number>;
  bootDelays: Record<string, number>;
  onBootOrderChange: (serverId: string, order: number) => void;
  onBootDelayChange: (serverId: string, delay: number) => void;
  readonly?: boolean;
}

export const BootOrderEditor: React.FC<BootOrderEditorProps> = ({
  servers,
  bootOrder,
  bootDelays,
  onBootOrderChange,
  onBootDelayChange,
  readonly = false
}) => {
  // Drag-and-drop implementation
  // Number input for delays
  // Visual ordering feedback
};
```

**2. ProtectionGroupAssignment.tsx - Component**
```typescript
interface ProtectionGroupAssignmentProps {
  availableProtectionGroups: ProtectionGroup[];
  assignedProtectionGroupIds: string[];
  onAssign: (pgId: string) => void;
  onUnassign: (pgId: string) => void;
  readonly?: boolean;
}

export const ProtectionGroupAssignment: React.FC<ProtectionGroupAssignmentProps> = ({
  availableProtectionGroups,
  assignedProtectionGroupIds,
  onAssign,
  onUnassign,
  readonly = false
}) => {
  // Dropdown for assignment
  // List of assigned PGs with remove button
  // Validation feedback
};
```

## [Classes]

No new classes required. All changes are functional components and TypeScript interfaces.

## [Dependencies]

No new external dependencies required. All functionality uses existing libraries:

- **Frontend**: 
  - React (existing)
  - Material-UI (existing)
  - TypeScript (existing)
  
- **Backend**:
  - boto3 (existing)
  - Python standard library (existing)

**Optional Enhancement** (future phase):
- `react-beautiful-dnd` - For drag-and-drop boot order UI (v13.1.1)
- Can be added later if manual number input is insufficient

## [Testing]

Comprehensive testing strategy for SRM parity changes.

### Unit Tests:

**1. WaveConfigEditor.test.tsx** (new file)
- Test PG assignment to waves
- Test validation: PG can't be in multiple waves
- Test boot order initialization
- Test boot delay updates
- Test server list auto-population from PGs

**2. RecoveryPlanDialog.test.tsx** (update existing)
- Test plan-level PG selection
- Test validation: at least one PG required
- Test wave creation with assigned PGs
- Test data transformation for API calls

**3. BootOrderEditor.test.tsx** (new file)
- Test boot order changes
- Test boot delay changes
- Test drag-and-drop ordering (if implemented)

### Integration Tests:

**1. Recovery Plan Creation Flow** (tests/playwright/)
- Create plan with multiple PGs
- Assign PGs to different waves
- Configure boot order within waves
- Save and verify data persistence

**2. Recovery Plan Execution** (tests/playwright/)
- Execute plan with boot order
- Verify servers start in correct order
- Verify boot delays are applied
- Check execution logs

### API Tests:

**1. Backend Validation Tests**
- Test: Reject duplicate PG assignments
- Test: Validate PG IDs exist
- Test: Boot order persists correctly
- Test: Backward compatibility with old data

### Manual Testing Checklist:

- [ ] Create new recovery plan with 3 PGs
- [ ] Assign PGs to waves 1, 2, 3
- [ ] Configure boot order within wave 1
- [ ] Add boot delays (30s, 60s)
- [ ] Save and reload plan
- [ ] Verify all data persisted
- [ ] Edit plan and reassign PGs
- [ ] Execute in drill mode
- [ ] Verify boot sequence matches configuration

## [Implementation Order]

Logical sequence to minimize breaking changes and enable incremental testing.

### Phase 1: Type Updates (Day 1 - 2 hours)
1. Update `frontend/src/types/index.ts`
   - Add `bootOrder` and `bootDelays` to Wave interface
   - Add `protectionGroupIds` to RecoveryPlan interface
   - Add `ServerBootConfig` interface
2. Verify TypeScript compilation succeeds
3. Update any type errors in existing code

### Phase 2: Backend API Updates (Day 1-2 - 4 hours)
1. Update `lambda/index.py` - `create_recovery_plan`
   - Accept plan-level `protectionGroupIds`
   - Add PG duplication validation
   - Store boot configuration
2. Update `lambda/index.py` - `update_recovery_plan`
   - Same changes as create
3. Update `lambda/index.py` - `list_recovery_plans`
   - Return plan-level PG IDs
4. Add backward compatibility logic
5. Test API endpoints with Postman/curl

### Phase 3: Protection Group Selection at Plan Level (Day 2 - 3 hours)
1. Update `RecoveryPlanDialog.tsx`
   - Add `selectedProtectionGroupIds` state
   - Add Autocomplete multi-select UI
   - Add validation
   - Update handleSubmit to send plan-level PGs
2. Test: Create new plan with multiple PGs selected
3. Test: Edit existing plan (PGs should load)

### Phase 4: Wave Editor Refactor (Day 3 - 6 hours)
1. Create `ProtectionGroupAssignment.tsx` component
   - PG assignment dropdown
   - Display assigned PGs
   - Remove button functionality
2. Update `WaveConfigEditor.tsx`
   - Remove old PG Autocomplete
   - Remove ServerSelector import
   - Add ProtectionGroupAssignment component
   - Implement `handleAssignProtectionGroup`
   - Auto-populate serverIds from assigned PGs
   - Add read-only server list display
3. Test: Assign PGs to waves
4. Test: Validation prevents duplicate assignments

### Phase 5: Boot Order Configuration (Day 4 - 4 hours)
1. Create `BootOrderEditor.tsx` component
   - Number inputs for boot order
   - Number inputs for boot delays (seconds)
   - Sort display by boot order
2. Integrate into `WaveConfigEditor.tsx`
   - Add BootOrderEditor per wave
   - Wire up onChange handlers
3. Test: Configure boot order
4. Test: Boot order persists on save/reload

### Phase 6: Testing & Validation (Day 5 - 4 hours)
1. Write unit tests for new components
2. Update existing integration tests
3. Manual testing of complete flow
4. Test backward compatibility with old plans
5. Fix any bugs found

### Phase 7: Documentation & Deployment (Day 5 - 2 hours)
1. Update user documentation
2. Update API documentation
3. Create migration guide for existing plans
4. Deploy to test environment
5. Validate in production-like environment

### Total Estimated Time: 5 days

---

**Document End**

**Next Steps**: Create implementation task with trackable checklist following this plan.
