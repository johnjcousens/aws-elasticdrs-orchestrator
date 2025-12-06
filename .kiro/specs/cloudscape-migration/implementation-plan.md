# CloudScape Migration - Implementation Plan

## Status: READY TO START

## Context
Migrating AWS DRS Orchestration frontend from Material-UI 7.3.5 to CloudScape Design System while maintaining current functionality and AWS-branded look/feel.

## Current State Analysis

### Dependencies to Remove
```json
"@emotion/react": "^11.14.0",
"@emotion/styled": "^11.14.1",
"@mui/icons-material": "^7.3.5",
"@mui/material": "^7.3.5",
"@mui/x-data-grid": "^8.17.0"
```

### Dependencies to Add
```json
"@cloudscape-design/components": "^3.0.0",
"@cloudscape-design/global-styles": "^1.0.0",
"@cloudscape-design/design-tokens": "^3.0.0",
"@cloudscape-design/collection-hooks": "^1.0.0",
"@cloudscape-design/board-components": "^3.0.0"
```

## Implementation Phases

### Phase 1: Setup & Infrastructure (2-4 hours)

#### 1.1 Install CloudScape Dependencies
```bash
cd frontend
npm install @cloudscape-design/components@latest \
  @cloudscape-design/global-styles@latest \
  @cloudscape-design/design-tokens@latest \
  @cloudscape-design/collection-hooks@latest \
  @cloudscape-design/board-components@latest
```

#### 1.2 Remove Material-UI Dependencies
```bash
npm uninstall @mui/material @mui/icons-material @mui/x-data-grid \
  @emotion/react @emotion/styled
```

#### 1.3 Update Global Styles
- Create `src/styles/cloudscape-theme.ts` for theme configuration
- Update `src/main.tsx` to import CloudScape global styles
- Remove Material-UI theme provider

#### 1.4 Create CloudScape Wrapper Components
- `src/components/cloudscape/AppLayout.tsx` - Main layout wrapper
- `src/components/cloudscape/ContentLayout.tsx` - Page content wrapper

### Phase 2: Core Shared Components (8-12 hours)

#### Priority 1: Utility Components (2 hours)
1. **StatusBadge.tsx** → CloudScape Badge
   - Material-UI Chip → CloudScape Badge
   - Color mapping: success, error, warning, info

2. **DateTimeDisplay.tsx** → Keep as-is
   - No Material-UI dependencies
   - Uses date-fns for formatting

3. **LoadingSpinner.tsx** → CloudScape Spinner
   - Material-UI CircularProgress → CloudScape Spinner

#### Priority 2: Dialog Components (3 hours)
4. **ConfirmDialog.tsx** → CloudScape Modal
   - Material-UI Dialog → CloudScape Modal
   - DialogTitle → Modal header prop
   - DialogContent → Modal children
   - DialogActions → Modal footer prop

5. **ProtectionGroupDialog.tsx** → CloudScape Modal + Form
   - Material-UI Dialog → CloudScape Modal
   - TextField → FormField + Input
   - Alert → Flashbar
   - Button → Button (similar API)

6. **RecoveryPlanDialog.tsx** → CloudScape Modal + Form
   - Similar to ProtectionGroupDialog
   - Complex form with waves

#### Priority 3: Selector Components (3 hours)
7. **RegionSelector.tsx** → CloudScape Select
   - Material-UI Select → CloudScape Select
   - MenuItem → option objects

8. **ServerSelector.tsx** → CloudScape Table + Checkbox
   - Material-UI DataGrid → CloudScape Table
   - Checkbox selection built-in

9. **TagFilterEditor.tsx** → CloudScape TokenGroup
   - Material-UI Chip → CloudScape Token

#### Priority 4: Display Components (2 hours)
10. **WaveProgress.tsx** → CloudScape ProgressIndicator
    - Material-UI Stepper → CloudScape ProgressIndicator
    - Step → ProgressIndicator.Step

11. **InfoPanel.tsx** → CloudScape Container
    - Material-UI Card → CloudScape Container

12. **EmptyState.tsx** → CloudScape Box
    - Material-UI Box → CloudScape Box
    - Typography → CloudScape text utilities

### Phase 3: Page Components (8-12 hours)

#### Priority 1: Simple Pages (2 hours)
13. **LoginPage.tsx** → CloudScape Form + Container
    - Material-UI Box → CloudScape SpaceBetween
    - TextField → FormField + Input
    - Button → Button
    - Alert → Flashbar

14. **Dashboard.tsx** → CloudScape AppLayout + Cards
    - Material-UI Grid → CloudScape ColumnLayout
    - Card → Container
    - Typography → CloudScape Header

#### Priority 2: Complex Pages (6 hours)
15. **ProtectionGroupsPage.tsx** → CloudScape Table + AppLayout
    - Material-UI DataGrid → CloudScape Table
    - Manual sorting/filtering with collection hooks
    - GridActionsCellItem → Button in table cell

16. **RecoveryPlansPage.tsx** → CloudScape Table + AppLayout
    - Similar to ProtectionGroupsPage
    - Complex nested data display

17. **ExecutionsPage.tsx** → CloudScape Table + AppLayout
    - Real-time data updates
    - Status indicators
    - Wave progress display

### Phase 4: Testing & Refinement (4-6 hours)

#### 4.1 Visual Testing (2 hours)
- Compare screenshots before/after
- Verify spacing and alignment
- Check color contrast ratios
- Test responsive breakpoints

#### 4.2 Functionality Testing (2 hours)
- Test all CRUD operations
- Verify server discovery
- Test execution monitoring
- Validate search/filter/sort

#### 4.3 Accessibility Testing (1 hour)
- Keyboard navigation
- Screen reader testing
- Focus management
- ARIA attributes

#### 4.4 Performance Testing (1 hour)
- Bundle size comparison
- Load time metrics
- Runtime performance

## Component Migration Details

### DataGrid → Table Migration

**Material-UI DataGrid:**
```tsx
<DataGrid
  rows={rows}
  columns={columns}
  loading={loading}
  pageSize={25}
  sortModel={sortModel}
  onSortModelChange={setSortModel}
/>
```

**CloudScape Table:**
```tsx
<Table
  items={items}
  columnDefinitions={columnDefinitions}
  loading={loading}
  loadingText="Loading..."
  sortingColumn={sortingColumn}
  sortingDescending={sortingDescending}
  onSortingChange={handleSortingChange}
  pagination={<Pagination currentPageIndex={1} pagesCount={10} />}
  filter={<TextFilter filteringText={filteringText} />}
/>
```

**Key Differences:**
- Manual sorting implementation required
- Manual filtering implementation required
- Use `@cloudscape-design/collection-hooks` for state management
- Pagination is separate component

### Dialog → Modal Migration

**Material-UI Dialog:**
```tsx
<Dialog open={open} onClose={onClose}>
  <DialogTitle>Title</DialogTitle>
  <DialogContent>Content</DialogContent>
  <DialogActions>
    <Button onClick={onClose}>Cancel</Button>
    <Button onClick={onSave}>Save</Button>
  </DialogActions>
</Dialog>
```

**CloudScape Modal:**
```tsx
<Modal
  visible={visible}
  onDismiss={onDismiss}
  header="Title"
  footer={
    <Box float="right">
      <SpaceBetween direction="horizontal" size="xs">
        <Button onClick={onDismiss}>Cancel</Button>
        <Button variant="primary" onClick={onSave}>Save</Button>
      </SpaceBetween>
    </Box>
  }
>
  Content
</Modal>
```

**Key Differences:**
- `open` → `visible`
- `onClose` → `onDismiss`
- Explicit `header` and `footer` props
- Footer requires manual layout

### TextField → FormField + Input Migration

**Material-UI TextField:**
```tsx
<TextField
  label="Name"
  value={value}
  onChange={(e) => setValue(e.target.value)}
  error={Boolean(error)}
  helperText={error || "Helper text"}
  fullWidth
/>
```

**CloudScape FormField + Input:**
```tsx
<FormField
  label="Name"
  description="Helper text"
  errorText={error}
>
  <Input
    value={value}
    onChange={(e) => setValue(e.detail.value)}
  />
</FormField>
```

**Key Differences:**
- Separate FormField wrapper for label/error
- `onChange` event has `detail` property
- No `fullWidth` prop (default behavior)

## File Structure Changes

### New Files to Create
```
frontend/src/
├── styles/
│   └── cloudscape-theme.ts          # CloudScape theme configuration
├── components/
│   └── cloudscape/
│       ├── AppLayout.tsx             # Main layout wrapper
│       ├── ContentLayout.tsx         # Page content wrapper
│       └── TableWrapper.tsx          # Reusable table with hooks
└── hooks/
    ├── useTableCollection.ts         # Table state management
    └── useFlashbar.ts                # Notification management
```

### Files to Modify
All 23 component files (5 pages + 18 shared components)

### Files to Delete
- `src/theme/` directory (Material-UI theme)
- Any Material-UI specific utilities

## Migration Checklist

### Phase 1: Setup ✅
- [ ] Install CloudScape dependencies
- [ ] Remove Material-UI dependencies
- [ ] Create CloudScape theme configuration
- [ ] Update main.tsx with global styles
- [ ] Create AppLayout wrapper
- [ ] Create ContentLayout wrapper

### Phase 2: Core Components ✅
- [ ] StatusBadge.tsx
- [ ] DateTimeDisplay.tsx (verify no MUI deps)
- [ ] LoadingSpinner.tsx
- [ ] ConfirmDialog.tsx
- [ ] ProtectionGroupDialog.tsx
- [ ] RecoveryPlanDialog.tsx
- [ ] RegionSelector.tsx
- [ ] ServerSelector.tsx
- [ ] TagFilterEditor.tsx
- [ ] WaveProgress.tsx
- [ ] InfoPanel.tsx
- [ ] EmptyState.tsx

### Phase 3: Pages ✅
- [ ] LoginPage.tsx
- [ ] Dashboard.tsx
- [ ] ProtectionGroupsPage.tsx
- [ ] RecoveryPlansPage.tsx
- [ ] ExecutionsPage.tsx

### Phase 4: Testing ✅
- [ ] Visual regression tests
- [ ] Functionality tests
- [ ] Accessibility tests
- [ ] Performance tests
- [ ] Cross-browser tests

## Risk Mitigation

### Risk 1: Table Complexity
**Issue:** CloudScape Table requires manual sorting/filtering
**Mitigation:** Use `@cloudscape-design/collection-hooks` for state management

### Risk 2: Breaking Changes
**Issue:** API differences between Material-UI and CloudScape
**Mitigation:** Migrate incrementally, test each component

### Risk 3: Bundle Size
**Issue:** CloudScape may increase bundle size
**Mitigation:** Monitor bundle size, use code splitting

### Risk 4: Visual Inconsistencies
**Issue:** Different component styling
**Mitigation:** Use CloudScape design tokens, create style guide

## Success Criteria

- [ ] Zero Material-UI dependencies in package.json
- [ ] All 23 components migrated to CloudScape
- [ ] All functionality preserved (CRUD, search, filter, sort)
- [ ] WCAG 2.1 AA compliance maintained
- [ ] Bundle size <3MB
- [ ] No console errors or warnings
- [ ] All TypeScript types correct
- [ ] Build succeeds without errors

## Timeline

- **Phase 1:** 2-4 hours (Setup)
- **Phase 2:** 8-12 hours (Core Components)
- **Phase 3:** 8-12 hours (Pages)
- **Phase 4:** 4-6 hours (Testing)

**Total:** 22-34 hours

## Next Steps

1. Start with Phase 1: Setup & Infrastructure
2. Install CloudScape dependencies
3. Create theme configuration
4. Update main.tsx
5. Create layout wrappers
6. Begin Phase 2: Core Components migration
