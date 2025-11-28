# Implementation Plan: Remove Wave ExecutionType Field

## [Overview]

Remove the redundant `executionType` field from the Wave architecture since the backend already ignores it and all within-wave execution is parallel with DRS-safe delays.

The current architecture has an unused `executionType: 'sequential' | 'parallel'` field in the Wave interface that was intended to control server launch behavior within a wave. However, the backend Lambda function (`lambda/index.py` lines 885-970) completely ignores this field and always launches servers with 15-second delays between them regardless of the executionType value. This creates a misleading UI that appears to offer sequential vs parallel execution when in reality all waves execute the same way.

Sequential operations are already properly handled through wave dependencies (DependsOn relationships), making the executionType field completely redundant. This change simplifies the architecture, removes user confusion, and aligns the frontend data model with actual backend behavior.

## [Types]

Remove the executionType field from Wave interface in TypeScript type definitions.

**Current Wave Interface (frontend/src/types/index.ts lines 48-67):**
```typescript
export interface Wave {
  waveNumber: number;
  name: string;
  description?: string;
  serverIds: string[];
  serverCount?: number;
  executionType: 'sequential' | 'parallel';  // ❌ REMOVE THIS
  dependsOnWaves?: number[];
  protectionGroupIds: string[];
  protectionGroupId?: string;
  ProtectionGroupIds?: string[];
  ProtectionGroupId?: string;
  preWaveActions?: WaveAction[];
  postWaveActions?: WaveAction[];
  healthCheckConfig?: HealthCheckConfig;
  rollbackConfig?: RollbackConfig;
}
```

**Updated Wave Interface:**
```typescript
export interface Wave {
  waveNumber: number;
  name: string;
  description?: string;
  serverIds: string[];
  serverCount?: number;
  // executionType removed - all within-wave execution is parallel with DRS-safe delays
  dependsOnWaves?: number[];
  protectionGroupIds: string[];
  protectionGroupId?: string;
  ProtectionGroupIds?: string[];
  ProtectionGroupId?: string;
  preWaveActions?: WaveAction[];
  postWaveActions?: WaveAction[];
  healthCheckConfig?: HealthCheckConfig;
  rollbackConfig?: RollbackConfig;
}
```

**No Changes Required:**
- Backend Lambda already ignores executionType
- DynamoDB schema doesn't enforce executionType
- Existing stored plans will continue to work (extra field ignored)

## [Files]

Three frontend files require modification to remove executionType references.

**Files to Modify:**

1. **frontend/src/types/index.ts** (Line 53)
   - Remove: `executionType: 'sequential' | 'parallel';`
   - Add comment explaining removal reason
   - Keep all other Wave interface fields intact

2. **frontend/src/components/WaveConfigEditor.tsx** (Lines 95-97, 155-165)
   - Remove: executionType from handleAddWave() initialization
   - Remove: entire execution type Select/MenuItem block (lines 155-165)
   - Remove: executionType Chip from accordion header
   - Keep all other wave configuration UI elements

3. **frontend/src/components/RecoveryPlanDialog.tsx** (Lines 113, 131)
   - Remove: ExecutionType field from wave mapping in handleSubmit()
   - Remove from both create and update API calls
   - Keep all other wave fields in API payload

**Files NOT Modified:**
- lambda/index.py - Already ignores executionType (no changes needed)
- Lambda backend never reads this field, so removal is safe
- DynamoDB schema - Field can exist but will be ignored (backward compatible)

## [Functions]

Update three React component functions to remove executionType field handling.

**1. WaveConfigEditor.handleAddWave() (frontend/src/components/WaveConfigEditor.tsx line 95)**

Current implementation:
```typescript
const handleAddWave = () => {
  const newWave: Wave = {
    waveNumber: safeWaves.length,
    name: `Wave ${safeWaves.length + 1}`,
    description: '',
    serverIds: [],
    executionType: 'sequential',  // ❌ REMOVE
    dependsOnWaves: [],
    protectionGroupIds: [],
    protectionGroupId: '',
  };
  onChange([...safeWaves, newWave]);
  setExpandedWave(safeWaves.length);
};
```

Updated implementation:
```typescript
const handleAddWave = () => {
  const newWave: Wave = {
    waveNumber: safeWaves.length,
    name: `Wave ${safeWaves.length + 1}`,
    description: '',
    serverIds: [],
    // executionType removed - all within-wave execution is parallel with delays
    dependsOnWaves: [],
    protectionGroupIds: [],
    protectionGroupId: '',
  };
  onChange([...safeWaves, newWave]);
  setExpandedWave(safeWaves.length);
};
```

**2. WaveConfigEditor Accordion Header Render (frontend/src/components/WaveConfigEditor.tsx lines 225-235)**

Current implementation:
```tsx
<Chip
  label={wave.executionType}  // ❌ REMOVE THIS CHIP
  size="small"
  color="default"
  variant="outlined"
/>
```

Updated implementation:
```tsx
// Chip removed - executionType no longer exists
// Keep only Protection Group count and Server count chips
```

**3. WaveConfigEditor Execution Type Select (frontend/src/components/WaveConfigEditor.tsx lines 155-165)**

Current implementation:
```tsx
<FormControl fullWidth disabled={readonly}>
  <InputLabel>Execution Type</InputLabel>
  <Select
    value={wave.executionType}
    label="Execution Type"
    onChange={(e) => handleUpdateWave(wave.waveNumber, 'executionType', e.target.value)}
  >
    <MenuItem value="sequential">Sequential (one server at a time)</MenuItem>
    <MenuItem value="parallel">Parallel (all servers simultaneously)</MenuItem>
  </Select>
</FormControl>
```

Updated implementation:
```tsx
// Entire FormControl block removed
// Replace with informational Alert
<Alert severity="info" sx={{ mb: 2 }}>
  All servers within a wave launch in parallel with DRS-safe delays (15s between servers).
  Use wave dependencies for sequential operations.
</Alert>
```

**4. RecoveryPlanDialog.handleSubmit() (frontend/src/components/RecoveryPlanDialog.tsx lines 105-135)**

Current implementation (both create and update):
```typescript
Waves: waves.map((wave, index) => ({
  WaveId: `wave-${index}`,
  WaveName: wave.name,
  WaveDescription: wave.description || '',
  ExecutionOrder: index,
  ProtectionGroupId: wave.protectionGroupId,
  ServerIds: wave.serverIds,
  ExecutionType: wave.executionType,  // ❌ REMOVE
  Dependencies: (wave.dependsOnWaves || []).map(depNum => ({
    DependsOnWaveId: `wave-${depNum}`
  }))
}))
```

Updated implementation:
```typescript
Waves: waves.map((wave, index) => ({
  WaveId: `wave-${index}`,
  WaveName: wave.name,
  WaveDescription: wave.description || '',
  ExecutionOrder: index,
  ProtectionGroupId: wave.protectionGroupId,
  ServerIds: wave.serverIds,
  // ExecutionType removed - backend ignores this field
  Dependencies: (wave.dependsOnWaves || []).map(depNum => ({
    DependsOnWaveId: `wave-${depNum}`
  }))
}))
```

## [Classes]

No class modifications required - all components are functional React components.

**Component Overview:**
- WaveConfigEditor - Functional component with hooks
- RecoveryPlanDialog - Functional component with hooks
- All state management via useState hooks
- No class-based components in the affected files

## [Dependencies]

No dependency changes required.

**Current Dependencies (unchanged):**
- React 18.3.1
- Material-UI 6.x
- TypeScript 5.x
- All existing frontend packages remain

**Why No Changes:**
- Only removing fields, not adding functionality
- No new libraries needed
- No version upgrades required

## [Testing]

Comprehensive manual testing to ensure backward compatibility and correct behavior.

**Test Cases:**

1. **Create New Recovery Plan**
   - Navigate to Recovery Plans page
   - Click "Create Recovery Plan"
   - Add multiple waves
   - Verify no executionType dropdown appears
   - Verify informational message about parallel execution
   - Save plan successfully
   - Verify plan appears in list

2. **Edit Existing Recovery Plan**
   - Open existing plan (may have executionType in data)
   - Edit wave configuration
   - Verify no executionType dropdown appears
   - Verify waves still load correctly despite old field
   - Save changes successfully
   - Verify changes persist

3. **Execute Recovery Plan**
   - Select plan with waves
   - Start execution
   - Monitor execution progress
   - Verify servers launch with delays (unchanged behavior)
   - Confirm execution completes successfully

4. **Wave Dependencies**
   - Create plan with wave dependencies (Wave 2 depends on Wave 1)
   - Execute plan
   - Verify Wave 2 waits for Wave 1 completion
   - Confirm sequential behavior still works via dependencies

5. **Backward Compatibility**
   - Test with plans created before this change
   - Verify plans with executionType field still load
   - Confirm extra field doesn't cause errors
   - Validate execution works correctly

**CloudWatch Logs Monitoring:**
- Check Lambda logs for execution delays (15s between servers)
- Verify no errors related to missing executionType
- Confirm DRS StartRecovery calls succeed

**Browser Console:**
- No TypeScript errors
- No runtime errors
- No warnings about missing fields

## [Implementation Order]

Implement changes in logical sequence to maintain working state throughout.

**Step 1: Update TypeScript Types** (5 minutes)
- File: frontend/src/types/index.ts
- Remove executionType field from Wave interface (line 53)
- Add explanatory comment about removal
- Save and verify TypeScript compilation
- Expected: TypeScript errors will appear in components (expected, fixed in next steps)

**Step 2: Update WaveConfigEditor Component** (15 minutes)
- File: frontend/src/components/WaveConfigEditor.tsx
- Remove executionType from handleAddWave() initialization (line 95)
- Remove executionType Chip from accordion header (line 232)
- Remove entire execution type Select block (lines 155-165)
- Add informational Alert about parallel execution
- Save and verify TypeScript compilation passes
- Expected: No more TypeScript errors in this file

**Step 3: Update RecoveryPlanDialog Component** (10 minutes)
- File: frontend/src/components/RecoveryPlanDialog.tsx
- Remove ExecutionType from wave mapping in handleSubmit() (lines 113, 131)
- Remove from both create and update operations
- Save and verify TypeScript compilation passes
- Expected: All TypeScript errors resolved

**Step 4: Build and Test Frontend** (20 minutes)
- Run: `cd frontend && npm run build`
- Verify build succeeds with no errors
- Run: `npm run dev` for local testing
- Test all cases from Testing section above
- Fix any issues discovered
- Expected: All tests pass

**Step 5: Deploy to TEST Environment** (10 minutes)
- Run CloudFormation update to deploy new frontend
- Wait for deployment completion
- Smoke test in TEST environment
- Verify existing plans still work
- Expected: Clean deployment, no errors

**Step 6: Update Documentation** (15 minutes)
- Update README.md to remove executionType references
- Update PROJECT_STATUS.md with session notes
- Add migration note for users
- Document new behavior clearly
- Expected: Documentation reflects new architecture

**Step 7: Git Commit and Tag** (5 minutes)
- Stage all changes: `git add frontend/src/`
- Commit: `git commit -m "refactor: Remove unused executionType from Wave interface"`
- Push to remote
- Optional: Tag as architectural improvement
- Expected: Clean git history

**Total Estimated Time: ~80 minutes (1.5 hours)**

**Rollback Plan:**
If issues discovered after deployment:
1. Revert git commit: `git revert HEAD`
2. Rebuild frontend: `npm run build`
3. Redeploy CloudFormation
4. Investigate issues before retry

**Success Criteria:**
- ✅ TypeScript compilation clean
- ✅ Frontend build succeeds
- ✅ All manual tests pass
- ✅ Backward compatibility maintained
- ✅ No executionType UI elements visible
- ✅ Wave dependencies still work correctly
- ✅ Documentation updated

---

## Navigation Commands

Use these commands to read specific sections of this implementation plan:

```bash
# Read Overview section
sed -n '/## \[Overview\]/,/## \[Types\]/p' implementation_plan.md | head -n -1 | cat

# Read Types section
sed -n '/## \[Types\]/,/## \[Files\]/p' implementation_plan.md | head -n -1 | cat

# Read Files section
sed -n '/## \[Files\]/,/## \[Functions\]/p' implementation_plan.md | head -n -1 | cat

# Read Functions section
sed -n '/## \[Functions\]/,/## \[Classes\]/p' implementation_plan.md | head -n -1 | cat

# Read Classes section
sed -n '/## \[Classes\]/,/## \[Dependencies\]/p' implementation_plan.md | head -n -1 | cat

# Read Dependencies section
sed -n '/## \[Dependencies\]/,/## \[Testing\]/p' implementation_plan.md | head -n -1 | cat

# Read Testing section
sed -n '/## \[Testing\]/,/## \[Implementation Order\]/p' implementation_plan.md | head -n -1 | cat

# Read Implementation Order section
sed -n '/## \[Implementation Order\]/,$p' implementation_plan.md | cat
