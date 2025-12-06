# CloudScape Migration - Task Breakdown

## Phase 1: Setup & Infrastructure

### Task 1.1: Install CloudScape Dependencies
**Estimated Time:** 15 minutes
**Status:** ✅ Complete

```bash
cd frontend
npm install @cloudscape-design/components@latest \
  @cloudscape-design/global-styles@latest \
  @cloudscape-design/design-tokens@latest \
  @cloudscape-design/collection-hooks@latest \
  @cloudscape-design/board-components@latest
```

**Acceptance Criteria:**
- All CloudScape packages installed
- package.json updated
- No installation errors

### Task 1.2: Remove Material-UI Dependencies
**Estimated Time:** 15 minutes
**Status:** ✅ Complete

```bash
npm uninstall @mui/material @mui/icons-material @mui/x-data-grid \
  @emotion/react @emotion/styled
```

**Acceptance Criteria:**
- All Material-UI packages removed from package.json
- No Material-UI imports remain in code
- Build still succeeds (will fail until components migrated)

### Task 1.3: Create CloudScape Theme Configuration
**Estimated Time:** 30 minutes
**Status:** ✅ Complete

**Files to Create:**
- `frontend/src/styles/cloudscape-theme.ts`

**Content:**
```typescript
import { applyMode, Mode } from '@cloudscape-design/global-styles';

export const initializeTheme = () => {
  // Apply AWS branded theme
  applyMode(Mode.Light);
};

export const themeConfig = {
  // Custom theme tokens if needed
};
```

**Acceptance Criteria:**
- Theme configuration file created
- Theme initialization function exported
- AWS branded theme applied

### Task 1.4: Update main.tsx
**Estimated Time:** 30 minutes
**Status:** ✅ Complete

**File to Modify:**
- `frontend/src/main.tsx`

**Changes:**
- Remove Material-UI ThemeProvider
- Import CloudScape global styles
- Initialize CloudScape theme

**Before:**
```typescript
import { ThemeProvider } from '@mui/material/styles';
import theme from './theme';

<ThemeProvider theme={theme}>
  <App />
</ThemeProvider>
```

**After:**
```typescript
import '@cloudscape-design/global-styles/index.css';
import { initializeTheme } from './styles/cloudscape-theme';

initializeTheme();

<App />
```

**Acceptance Criteria:**
- CloudScape global styles imported
- Theme initialized
- No Material-UI theme provider
- App renders without errors

### Task 1.5: Create AppLayout Wrapper
**Estimated Time:** 1 hour
**Status:** ✅ Complete

**File to Create:**
- `frontend/src/components/cloudscape/AppLayout.tsx`

**Purpose:**
- Wrap all pages with CloudScape AppLayout
- Provide consistent navigation and header
- Handle breadcrumbs and notifications

**Acceptance Criteria:**
- AppLayout component created
- Navigation working
- Header with user info
- Breadcrumbs functional

### Task 1.6: Create ContentLayout Wrapper
**Estimated Time:** 30 minutes
**Status:** ✅ Complete

**File to Create:**
- `frontend/src/components/cloudscape/ContentLayout.tsx`

**Purpose:**
- Standardize page content layout
- Provide consistent spacing
- Handle page headers

**Acceptance Criteria:**
- ContentLayout component created
- Consistent spacing applied
- Page headers standardized

---

## Phase 2: Core Shared Components

### Task 2.1: Migrate StatusBadge.tsx
**Estimated Time:** 30 minutes
**Status:** ✅ Complete

**File to Modify:**
- `frontend/src/components/StatusBadge.tsx`

**Changes:**
- Material-UI Chip → CloudScape Badge
- Color mapping: success, error, warning, info

**Before:**
```typescript
import { Chip } from '@mui/material';

<Chip label={status} color={color} />
```

**After:**
```typescript
import { Badge } from '@cloudscape-design/components';

<Badge color={color}>{status}</Badge>
```

**Acceptance Criteria:**
- Badge displays correctly
- Colors mapped correctly
- No Material-UI imports

### Task 2.2: Verify DateTimeDisplay.tsx
**Estimated Time:** 15 minutes
**Status:** ✅ Complete

**File to Check:**
- `frontend/src/components/DateTimeDisplay.tsx`

**Purpose:**
- Verify no Material-UI dependencies
- Ensure date-fns formatting works

**Acceptance Criteria:**
- No Material-UI imports
- Component works as-is

### Task 2.3: Migrate LoadingState.tsx
**Estimated Time:** 30 minutes
**Status:** ✅ Complete

**File to Modify:**
- `frontend/src/components/LoadingSpinner.tsx`

**Changes:**
- Material-UI CircularProgress → CloudScape Spinner

**Before:**
```typescript
import { CircularProgress } from '@mui/material';

<CircularProgress />
```

**After:**
```typescript
import { Spinner } from '@cloudscape-design/components';

<Spinner size="large" />
```

**Acceptance Criteria:**
- Spinner displays correctly
- Size options work
- No Material-UI imports

### Task 2.4: Migrate ConfirmDialog.tsx
**Estimated Time:** 1 hour
**Status:** ✅ Complete

**File to Modify:**
- `frontend/src/components/ConfirmDialog.tsx`

**Changes:**
- Material-UI Dialog → CloudScape Modal
- DialogTitle → Modal header prop
- DialogContent → Modal children
- DialogActions → Modal footer prop

**Before:**
```typescript
<Dialog open={open} onClose={onClose}>
  <DialogTitle>Title</DialogTitle>
  <DialogContent>Content</DialogContent>
  <DialogActions>
    <Button onClick={onClose}>Cancel</Button>
    <Button onClick={onConfirm}>Confirm</Button>
  </DialogActions>
</Dialog>
```

**After:**
```typescript
<Modal
  visible={visible}
  onDismiss={onDismiss}
  header="Title"
  footer={
    <Box float="right">
      <SpaceBetween direction="horizontal" size="xs">
        <Button onClick={onDismiss}>Cancel</Button>
        <Button variant="primary" onClick={onConfirm}>Confirm</Button>
      </SpaceBetween>
    </Box>
  }
>
  Content
</Modal>
```

**Acceptance Criteria:**
- Modal displays correctly
- Buttons work
- Dismiss functionality works
- No Material-UI imports

### Task 2.5: Migrate ProtectionGroupDialog.tsx
**Estimated Time:** 2 hours
**Status:** ✅ Complete

**File to Modify:**
- `frontend/src/components/ProtectionGroupDialog.tsx`

**Changes:**
- Material-UI Dialog → CloudScape Modal
- TextField → FormField + Input
- Alert → Flashbar
- Button → Button

**Key Challenges:**
- Complex form with validation
- Server discovery panel integration
- Error handling

**Acceptance Criteria:**
- Modal displays correctly
- Form validation works
- Server discovery works
- Error messages display
- Save/Cancel work
- No Material-UI imports

### Task 2.6: Migrate RecoveryPlanDialog.tsx
**Estimated Time:** 2 hours
**Status:** ✅ Complete

**File to Modify:**
- `frontend/src/components/RecoveryPlanDialog.tsx`

**Changes:**
- Similar to ProtectionGroupDialog
- Complex wave configuration
- Dependency management

**Acceptance Criteria:**
- Modal displays correctly
- Wave configuration works
- Dependency validation works
- Save/Cancel work
- No Material-UI imports

### Task 2.7: Migrate RegionSelector.tsx
**Estimated Time:** 1 hour
**Status:** ✅ Complete

**File to Modify:**
- `frontend/src/components/RegionSelector.tsx`

**Changes:**
- Material-UI Select → CloudScape Select
- MenuItem → option objects

**Before:**
```typescript
<Select value={value} onChange={onChange}>
  <MenuItem value="us-east-1">US East (N. Virginia)</MenuItem>
  <MenuItem value="us-west-2">US West (Oregon)</MenuItem>
</Select>
```

**After:**
```typescript
<Select
  selectedOption={{ value: value, label: getRegionLabel(value) }}
  onChange={({ detail }) => onChange(detail.selectedOption.value)}
  options={[
    { value: 'us-east-1', label: 'US East (N. Virginia)' },
    { value: 'us-west-2', label: 'US West (Oregon)' }
  ]}
/>
```

**Acceptance Criteria:**
- Select displays correctly
- All 13 regions available
- Selection works
- No Material-UI imports

### Task 2.8: Migrate ServerSelector.tsx
**Estimated Time:** 2 hours
**Status:** ✅ Complete

**File to Modify:**
- `frontend/src/components/ServerSelector.tsx`

**Changes:**
- Material-UI DataGrid → CloudScape Table
- Checkbox selection built-in
- Manual sorting/filtering

**Key Challenges:**
- Complex table with selection
- Real-time search
- Assignment status badges

**Acceptance Criteria:**
- Table displays correctly
- Selection works
- Search works
- Assignment badges display
- No Material-UI imports

### Task 2.9: Migrate TagFilterEditor.tsx
**Estimated Time:** 1 hour
**Status:** Not Started

**File to Modify:**
- `frontend/src/components/TagFilterEditor.tsx`

**Changes:**
- Material-UI Chip → CloudScape Token
- TokenGroup for multiple tags

**Acceptance Criteria:**
- Tags display correctly
- Add/remove works
- No Material-UI imports

### Task 2.10: Migrate WaveProgress.tsx
**Estimated Time:** 1.5 hours
**Status:** ✅ Complete

**File to Modify:**
- `frontend/src/components/WaveProgress.tsx`

**Changes:**
- Material-UI Stepper → CloudScape ProgressIndicator
- Step → ProgressIndicator.Step

**Before:**
```typescript
<Stepper activeStep={activeStep}>
  <Step>
    <StepLabel>Wave 1</StepLabel>
  </Step>
  <Step>
    <StepLabel>Wave 2</StepLabel>
  </Step>
</Stepper>
```

**After:**
```typescript
<ProgressIndicator
  currentStepIndex={currentStepIndex}
  steps={[
    { label: 'Wave 1', description: 'Description' },
    { label: 'Wave 2', description: 'Description' }
  ]}
/>
```

**Acceptance Criteria:**
- Progress indicator displays correctly
- Steps show correct status
- No Material-UI imports

### Task 2.11: Migrate InfoPanel.tsx
**Estimated Time:** 30 minutes
**Status:** Not Started

**File to Modify:**
- `frontend/src/components/InfoPanel.tsx`

**Changes:**
- Material-UI Card → CloudScape Container

**Acceptance Criteria:**
- Container displays correctly
- Content renders
- No Material-UI imports

### Task 2.12: Migrate EmptyState.tsx
**Estimated Time:** 30 minutes
**Status:** Not Started

**File to Modify:**
- `frontend/src/components/EmptyState.tsx`

**Changes:**
- Material-UI Box → CloudScape Box
- Typography → CloudScape text utilities

**Acceptance Criteria:**
- Empty state displays correctly
- Message and icon show
- No Material-UI imports

---

## Phase 3: Page Components

### Task 3.1: Migrate LoginPage.tsx
**Estimated Time:** 1.5 hours
**Status:** ✅ Complete

**File to Modify:**
- `frontend/src/pages/LoginPage.tsx`

**Changes:**
- Material-UI Box → CloudScape SpaceBetween
- TextField → FormField + Input
- Button → Button
- Alert → Flashbar

**Acceptance Criteria:**
- Login form displays correctly
- Cognito authentication works
- Error messages display
- No Material-UI imports

### Task 3.2: Migrate Dashboard.tsx
**Estimated Time:** 1.5 hours
**Status:** ✅ Complete

**File to Modify:**
- `frontend/src/pages/Dashboard.tsx`

**Changes:**
- Material-UI Grid → CloudScape ColumnLayout
- Card → Container
- Typography → CloudScape Header

**Acceptance Criteria:**
- Dashboard layout correct
- Metrics display
- Quick actions work
- No Material-UI imports

### Task 3.3: Migrate ProtectionGroupsPage.tsx
**Estimated Time:** 3 hours
**Status:** ✅ Complete

**File to Modify:**
- `frontend/src/pages/ProtectionGroupsPage.tsx`

**Changes:**
- Material-UI DataGrid → CloudScape Table
- Manual sorting/filtering with collection hooks
- GridActionsCellItem → Button in table cell

**Key Challenges:**
- Complex table with actions
- CRUD operations
- Real-time updates

**Acceptance Criteria:**
- Table displays correctly
- Sorting works
- Filtering works
- Pagination works
- CRUD operations work
- No Material-UI imports

### Task 3.4: Migrate RecoveryPlansPage.tsx
**Estimated Time:** 3 hours
**Status:** ✅ Complete

**File to Modify:**
- `frontend/src/pages/RecoveryPlansPage.tsx`

**Changes:**
- Similar to ProtectionGroupsPage
- Complex nested data display

**Acceptance Criteria:**
- Table displays correctly
- Wave data displays
- CRUD operations work
- No Material-UI imports

### Task 3.5: Migrate ExecutionsPage.tsx
**Estimated Time:** 3 hours
**Status:** ✅ Complete

**File to Modify:**
- `frontend/src/pages/ExecutionsPage.tsx`

**Changes:**
- Real-time data updates
- Status indicators
- Wave progress display

**Acceptance Criteria:**
- Table displays correctly
- Real-time updates work
- Status badges display
- Wave progress shows
- No Material-UI imports

---

## Phase 4: Testing & Refinement

### Task 4.1: Visual Regression Testing
**Estimated Time:** 2 hours
**Status:** Not Started

**Activities:**
- Compare screenshots before/after
- Verify spacing and alignment
- Check color contrast ratios
- Test responsive breakpoints

**Acceptance Criteria:**
- No visual regressions
- Spacing consistent
- Colors accessible
- Responsive design works

### Task 4.2: Functionality Testing
**Estimated Time:** 2 hours
**Status:** Not Started

**Activities:**
- Test all CRUD operations
- Verify server discovery
- Test execution monitoring
- Validate search/filter/sort

**Acceptance Criteria:**
- All CRUD operations work
- Server discovery works
- Execution monitoring works
- Search/filter/sort work

### Task 4.3: Accessibility Testing
**Estimated Time:** 1 hour
**Status:** Not Started

**Activities:**
- Keyboard navigation
- Screen reader testing
- Focus management
- ARIA attributes

**Acceptance Criteria:**
- Keyboard navigation works
- Screen reader compatible
- Focus management correct
- WCAG 2.1 AA compliant

### Task 4.4: Performance Testing
**Estimated Time:** 1 hour
**Status:** Not Started

**Activities:**
- Bundle size comparison
- Load time metrics
- Runtime performance

**Acceptance Criteria:**
- Bundle size <3MB
- Load time acceptable
- No performance regressions

---

## Summary

**Total Tasks:** 29
**Total Estimated Time:** 22-34 hours

**Phase Breakdown:**
- Phase 1 (Setup): 6 tasks, 2-4 hours
- Phase 2 (Core Components): 12 tasks, 8-12 hours
- Phase 3 (Pages): 5 tasks, 8-12 hours
- Phase 4 (Testing): 4 tasks, 4-6 hours

**Next Steps:**
1. Begin Phase 1: Setup & Infrastructure
2. Install CloudScape dependencies
3. Create theme configuration
4. Update main.tsx
5. Create layout wrappers
