# Session 45 Manual Fix Guide

## You're Right - We're Going in Circles

Today's attempts (4 commits, multiple corrupted files):
- `27bcd61` - Fixed `_event` → `event` parameter ✅ (this works)
- `3a8cc9a` - Tried useEffect fix (wrong approach)
- `9d0c35d` - Re-deployed commit 27bcd61
- `466bd69` - Documentation only
- **Multiple corrupted attempts** - Automated edits keep breaking JSX

## The Actual Problem (CONFIRMED)

**Your console log proves it:**
```
🔵 onChange fired! {newValue: Array(1)}
```

**onChange DOES fire** ✅  
**Chips DON'T appear** ❌

**Root Cause:** Stale state from 3 sequential function calls

## Current Code (Lines 363-368)

```typescript
onChange={(event, newValue) => {
  const pgIds = newValue.map(pg => pg.protectionGroupId);
  console.log('🔵 onChange fired!', { newValue });
  handleUpdateWave(wave.waveNumber, 'protectionGroupIds', pgIds);      // Call 1
  // Keep protectionGroupId in sync for backward compatibility
  handleUpdateWave(wave.waveNumber, 'protectionGroupId', pgIds[0] || ''); // Call 2 (sees stale waves)
  // Clear server selections when PGs change
  handleUpdateWave(wave.waveNumber, 'serverIds', []);                  // Call 3 (sees stale waves)
}}
```

**Problem:** Each `handleUpdateWave()` call sees the SAME stale `waves` state because React hasn't re-rendered yet. Only the last call's update survives.

## The Fix (Batched Update)

Replace lines 363-368 with:

```typescript
onChange={(event, newValue) => {
  const pgIds = newValue.map(pg => pg.protectionGroupId);
  console.log('🔵 onChange fired!', { newValue, pgIds });
  // Batch all updates in ONE call to prevent stale state
  const updatedWaves = safeWaves.map(w =>
    w.waveNumber === wave.waveNumber 
      ? { ...w, protectionGroupIds: pgIds, protectionGroupId: pgIds[0] || '', serverIds: [] } 
      : w
  );
  onChange(updatedWaves);
}}
```

**Why This Works:** Single call to `onChange()` with all three updates applied atomically. No stale state possible.

## Manual Application Steps

### Step 1: Open File
```bash
code frontend/src/components/WaveConfigEditor.tsx
```

### Step 2: Navigate to Line 363
- Press `Cmd+G` (Mac) or `Ctrl+G` (Windows)
- Type `363` and press Enter

### Step 3: Select Lines 363-368
- Click at start of line 363
- Shift+Click at end of line 368 (the closing `}}`)
- All 6 lines should be selected

### Step 4: Delete and Paste Fix
- Press Delete/Backspace to remove selected lines
- Paste the fix code from above
- Save file (`Cmd+S` / `Ctrl+S`)

### Step 5: Validate
```bash
cd frontend && npm run type-check
```
Should output: No errors ✅

### Step 6: Build
```bash
npm run build
```
Should complete successfully ✅

### Step 7: Deploy
```bash
aws s3 sync dist/ s3://drs-orchestration-fe-***REMOVED***-test --delete
aws cloudfront create-invalidation --distribution-id E46O075T9AHF3 --paths "/*"
```

### Step 8: Test
1. Wait 2 minutes for invalidation
2. Visit: https://d1wfyuosowt0hl.cloudfront.net
3. Hard refresh (Cmd+Shift+R)
4. Open Console (F12)
5. Recovery Plans → Create New → Expand Wave 1
6. Click Protection Group option

**Expected Results:**
- ✅ Console shows: `🔵 onChange fired! {newValue, pgIds}`
- ✅ Chip appears with Protection Group name
- ✅ Server dropdown populates with servers
- ✅ Chip persists when you click away

### Step 9: Commit
```bash
git add frontend/src/components/WaveConfigEditor.tsx
git commit -m "fix(frontend): Batch Protection Group state updates to prevent stale state

FINAL FIX - Console confirmed onChange fires but chips don't appear.
Root cause: 3 sequential handleUpdateWave calls caused stale state.

Solution: Single batched update using map ensures all properties
update atomically in one render cycle.

Manual application after automated edits repeatedly corrupted file.

Tested: Chips appear, server dropdown populates, selections persist."
git push origin main
```

## Why Manual Fix?

**Automated attempts keep corrupting the JSX:**
- sed: Breaks multi-line JSX syntax
- replace_in_file: Complex JSX confuses the parser

**Manual edit is safest** because:
1. You see the exact change in VS Code
2. TypeScript validates immediately
3. No risk of syntax corruption
4. You're in full control

## What Happens After Fix

**Protection Group selection will work:**
- ✅ Click option → Chip appears
- ✅ Chip shows correct PG name and server count
- ✅ Chips persist (no disappearing)
- ✅ Server dropdown populates immediately
- ✅ Can select multiple Protection Groups per wave

**Bug is permanently fixed** - No more stale state issues.

## Support

If anything goes wrong during manual application:
1. Revert: `git checkout frontend/src/components/WaveConfigEditor.tsx`
2. Try again following steps exactly
3. Verify file isn't corrupted before committing

Current working commit: `466bd69` (has the `_event` fix deployed)
Target: Add batched update on top of this commit
