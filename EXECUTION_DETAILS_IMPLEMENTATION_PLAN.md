# ExecutionDetailsPage.tsx Implementation Plan

## Current Status: CRITICAL CORRUPTION ISSUE

### Problem Summary
The `frontend/src/pages/ExecutionDetailsPage.tsx` file has been systematically corrupted across multiple restoration attempts, showing 700+ TypeScript errors with patterns like:
- "Unterminated regular expression literal"
- Malformed JSX syntax
- Missing imports and type definitions

### Root Cause Analysis

#### 1. File Writing Corruption Pattern
**Evidence**: Every attempt to restore the file (via `cp`, `git show`, `fsWrite`) results in identical corruption patterns.

**Hypothesis**: The corruption appears to be happening during the file writing process, not from the source. This suggests:
- IDE auto-formatting/auto-fixing is corrupting the file during write operations
- File encoding issues during transfer
- Memory/buffer corruption during large file operations

#### 2. Steering Rule Violation
The `.kiro/steering/file-writing.md` rule explicitly states:
- "Just write the file using fsWrite/strReplace tools"
- "Do NOT open files in the editor window after writing"
- "Opening files in editor tends to cause autocomplete issues"

**Current Issue**: The file is currently open in the editor, which may be triggering auto-fix/autocomplete corruption.

### Required Changes (From EXECUTION_DETAILS_PAGE_CHANGES_TODO.md)

We need to implement exactly 3 changes:

#### Change 1: Add 'cancelling' to Polling Status List (Line ~96-97)
```typescript
// CURRENT (around line 96-97):
const shouldPoll = [
  'PENDING',
  'POLLING', 
  'INITIATED',
  'LAUNCHING',
  'STARTED',
  'IN_PROGRESS',
  'RUNNING'
].includes(execution.Status);

// REQUIRED CHANGE:
const shouldPoll = [
  'PENDING',
  'POLLING', 
  'INITIATED',
  'LAUNCHING',
  'STARTED',
  'IN_PROGRESS',
  'RUNNING',
  'cancelling'  // Keep polling while cancelling
].includes(execution.Status);
```

**Purpose**: Ensures the UI continues polling for status updates while an execution is being cancelled, providing real-time feedback to users.

#### Change 2: Update canCancel Logic (Line ~406)
```typescript
// CURRENT (around line 406):
const canCancel = execution && [
  'PENDING', 'POLLING', 'INITIATED', 'LAUNCHING', 'STARTED', 'IN_PROGRESS', 'RUNNING', 'PAUSED'
].includes(execution.Status);

// REQUIRED CHANGE:
const canCancel = execution && [
  'PENDING', 'POLLING', 'INITIATED', 'LAUNCHING', 'STARTED', 'IN_PROGRESS', 'RUNNING', 'PAUSED'
].includes(execution.Status) && execution.Status !== 'cancelling';
```

**Purpose**: Prevents users from clicking the "Cancel" button multiple times while cancellation is already in progress, avoiding duplicate API calls.

#### Change 3: Add Props to WaveProgress Component (Line ~755-760)
```typescript
// CURRENT (around line 755-760):
<WaveProgress
  waves={mapWavesToWaveExecutions(execution)}
  totalWaves={execution.TotalWaves}
  executionId={execution.ExecutionId}
/>

// REQUIRED CHANGE:
<WaveProgress
  waves={mapWavesToWaveExecutions(execution)}
  totalWaves={execution.TotalWaves}
  executionId={execution.ExecutionId}
  executionStatus={execution.Status}
  executionEndTime={execution.EndTime}
/>
```

**Purpose**: Provides the WaveProgress component with additional execution context needed for proper status display and behavior.

### Implementation Strategy

#### Phase 1: Corruption Resolution
1. **Close Editor**: Ensure the file is not open in any editor
2. **Clean Restoration**: Use a method that bypasses potential IDE interference
3. **Verify Integrity**: Confirm the file has no TypeScript errors before proceeding

#### Phase 2: Targeted Changes
1. **Use strReplace**: Make only the 3 specific changes using targeted string replacement
2. **Avoid Full Rewrites**: Never rewrite the entire file
3. **Validate Each Change**: Check diagnostics after each change

#### Phase 3: Testing & Commit
1. **Verify Functionality**: Ensure all 3 changes work as expected
2. **Update Documentation**: Update CHANGELOG.md with the fixes
3. **Commit Changes**: Use proper git commit message format

### Alternative Approaches if Corruption Persists

#### Option A: Manual Line-by-Line Restoration
- Read the clean backup file line by line
- Write each line individually using strReplace
- Avoid large block operations

#### Option B: Component Splitting
- Extract problematic sections into separate components
- Reduce the size of the main file to avoid corruption
- Import the components back

#### Option C: Git-Based Restoration
- Use git commands to restore from a known good commit
- Apply changes as patches rather than direct edits

### File Dependencies

#### Import Issues to Resolve
```typescript
// Missing/incorrect imports that need fixing:
import { useNotification } from '../contexts/NotificationContext';  // Should be useNotifications
import { Execution, ExecutionStatus } from '../types/execution';     // Module not found
```

#### Component Dependencies
- StatusBadge
- DateTimeDisplay  
- WaveProgress
- ConfirmDialog
- LoadingState
- ErrorState
- PageTransition

### Success Criteria

1. **Zero TypeScript Errors**: File must compile without any errors
2. **All 3 Changes Applied**: Each required change must be present and correct
3. **Functional UI**: The page must render and function properly
4. **No Regression**: Existing functionality must remain intact

### Risk Mitigation

1. **Backup Strategy**: Keep multiple clean backups of the working file
2. **Incremental Changes**: Apply one change at a time with validation
3. **Rollback Plan**: Be prepared to restore from git if corruption recurs
4. **Editor Isolation**: Keep the file closed in all editors during modification

### Next Steps

1. **Immediate**: Close the file in the editor to prevent further corruption
2. **Restore**: Use a clean restoration method that bypasses IDE interference  
3. **Apply Changes**: Use targeted strReplace operations for the 3 required changes
4. **Validate**: Verify each change works correctly
5. **Document**: Update CHANGELOG.md and commit the changes

## Technical Notes

### File Size Considerations
- The file is approximately 575 lines
- Large file operations may be triggering corruption
- Consider chunked operations if issues persist

### IDE Behavior
- Auto-formatting may be corrupting JSX syntax
- Auto-imports may be adding incorrect import statements
- Auto-completion may be inserting malformed code

### Git Strategy
- Use `--no-pager` for all git commands
- Create commit message in temporary file
- Ensure clean working directory before committing